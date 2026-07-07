"""
Signal Hunter production-quality arXiv Collector.

Queries the official arXiv Atom XML API, processes pagination, respects rate limits,
applies publication date filtering, and parses elements into ResearchItem models.
"""

import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import requests

from collectors.base import BaseCollector
from config.config_loader import CollectorConfig
from models.research_item import ResearchItem, Author, Source
from utils.exceptions import CollectionError


class ArXivCollector(BaseCollector):
    """
    Ingests research papers from the official arXiv API.

    Features:
    - Search by configurable topics (categories or text terms).
    - Filter by publication date (using days_back).
    - Limit number of returned papers.
    - Retry on network failures with exponential backoff.
    - Handle API and parsing errors gracefully.
    - Support pagination and respect arXiv rate limits.
    - Configurable timeout, retries, and sorting.
    """

    # ArXiv API endpoint
    BASE_URL = "http://export.arxiv.org/api/query"

    # Atom XML namespaces
    NAMESPACES = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    @property
    def name(self) -> str:
        """
        Return the unique descriptive name of the collector.
        """
        return "ArXiv"

    def _get_config_value(self, key: str, default: Any) -> Any:
        """Helper to get value from config params, falling back to a default."""
        return self.config.params.get(key, default)

    def collect(self) -> List[ResearchItem]:
        """
        Scan arXiv and gather raw ResearchItem objects.

        Returns:
            List[ResearchItem]: Discovered papers parsed as research items.

        Raises:
            CollectionError: If there's an issue executing the request or parsing.
        """
        start_time = time.time()
        self.logger.info("Starting collection from arXiv API")

        # Load and resolve all configurable options
        topics: List[str] = self._get_config_value("topics", self.config.sources or ["cs.AI", "cs.LG", "cs.CL"])
        max_results: int = int(self._get_config_value("max_results", 25))
        days_back: Optional[int] = self._get_config_value("days_back", None)
        timeout: float = float(self._get_config_value("timeout", 10.0))
        retry_count: int = int(self._get_config_value("retry_count", 3))
        sort_by: str = self._get_config_value("sort_by", "submittedDate")
        sort_order: str = self._get_config_value("sort_order", "descending")

        # Map client-side config names to arXiv API sorting terms
        arxiv_sort_by = "submittedDate"
        if sort_by in ["submittedDate", "lastUpdatedDate", "relevance"]:
            arxiv_sort_by = sort_by

        arxiv_sort_order = "descending"
        if sort_order in ["descending", "ascending"]:
            arxiv_sort_order = sort_order

        if not topics:
            self.logger.warning("No search topics specified. Returning empty paper list.")
            return []

        # Construct search query
        search_query = self._build_search_query(topics)
        self.logger.info("Constructed search query: '%s'", search_query)

        # Pagination parameters
        page_size = min(max_results, 50)  # query in blocks of 50 or configured max
        collected_items: List[ResearchItem] = []
        skipped_count = 0
        current_start = 0

        # Calculate publication cutoff if requested
        cutoff_date = None
        if days_back is not None:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            self.logger.info("Filtering for papers published/updated after: %s", cutoff_date)

        page_count = 0
        max_pages = 5

        while len(collected_items) < max_results:
            page_count += 1
            if page_count > max_pages:
                self.logger.info("Reached safety limit of %d pages. Stopping collection.", max_pages)
                break

            results_to_fetch = min(page_size, max_results - len(collected_items))
            params = {
                "search_query": search_query,
                "sortBy": arxiv_sort_by,
                "sortOrder": arxiv_sort_order,
                "start": current_start,
                "max_results": results_to_fetch,
            }

            # Enforce arXiv polite rate limit delay between paginated requests
            if current_start > 0:
                self.logger.info("Sleeping 3.0 seconds to respect arXiv rate limits...")
                time.sleep(3.0)

            try:
                xml_data = self._fetch_with_retry(
                    url=self.BASE_URL,
                    params=params,
                    timeout=timeout,
                    retry_count=retry_count,
                )
            except Exception as e:
                self.logger.error("Failed to fetch page start=%d from arXiv: %s", current_start, e)
                raise CollectionError("ArXiv", f"Failed fetching papers: {e}") from e

            # Parse entries from Atom XML
            try:
                parsed_entries = self._parse_xml_feed(xml_data, cutoff_date)
            except Exception as e:
                self.logger.error("XML parsing crashed on chunk: %s", e)
                raise CollectionError("ArXiv", f"Failed parsing XML payload: {e}") from e

            # If arXiv returned absolutely no entries, we are at the end of results
            if not parsed_entries:
                self.logger.info("No more papers returned from arXiv.")
                break

            initial_collected_count = len(collected_items)

            for item, is_skipped in parsed_entries:
                if is_skipped:
                    skipped_count += 1
                elif item:
                    # Append unique item if not already gathered (safety check)
                    if not any(x.unique_id == item.unique_id for x in collected_items):
                        collected_items.append(item)
                    if len(collected_items) >= max_results:
                        break

            # If cutoff_date is active, and the last item in this page is older than cutoff,
            # and we are sorting by date descending, then all subsequent pages will be even older.
            if cutoff_date is not None and parsed_entries:
                last_valid_item = None
                # find last successfully parsed item to check its date
                for entry_item, _ in reversed(parsed_entries):
                    if entry_item:
                        last_valid_item = entry_item
                        break
                if last_valid_item and last_valid_item.publication_date:
                    tz_last = last_valid_item.publication_date.replace(tzinfo=timezone.utc) if last_valid_item.publication_date.tzinfo is None else last_valid_item.publication_date
                    if tz_last < cutoff_date and sort_order == "descending" and sort_by in ["submittedDate", "lastUpdatedDate"]:
                        self.logger.info("Last paper on page is older than cutoff date. Stopping pagination.")
                        break

            # If we made no progress collecting any new items from this page, and all were skipped,
            # we should stop paginating to avoid looping infinitely on stale/filtered results
            if len(collected_items) == initial_collected_count:
                self.logger.info("No new items added from this page. Stopping pagination.")
                break

            # Increment pagination offset
            current_start += results_to_fetch

        duration = time.time() - start_time
        self.logger.info(
            "Completed arXiv collection. Found: %d paper(s), Skipped (by filters/parse errors): %d paper(s). Execution time: %.2f seconds.",
            len(collected_items),
            skipped_count,
            duration,
        )

        return collected_items

    def _build_search_query(self, topics: List[str]) -> str:
        """
        Translates human configurable topics into standard arXiv category/field queries.
        """
        parts = []
        for topic in topics:
            topic = topic.strip()
            if not topic:
                continue
            # If it has '.' (e.g. cs.AI, stat.ML) or fits standard prefixes, treat as category
            if "." in topic or any(topic.startswith(p) for p in ["cs", "stat", "math", "physics", "q-bio"]):
                parts.append(f"cat:{topic}")
            else:
                # Standard text term
                if " " in topic:
                    parts.append(f'all:"{topic}"')
                else:
                    parts.append(f"all:{topic}")

        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0]
        return "(" + " OR ".join(parts) + ")"

    def _fetch_with_retry(self, url: str, params: Dict[str, Any], timeout: float, retry_count: int) -> str:
        """
        Executes HTTP requests with exponential backoff retries.
        """
        delay = 1.0
        for attempt in range(1, retry_count + 1):
            try:
                self.logger.debug("Requesting arXiv (Attempt %d/%d)", attempt, retry_count)
                response = requests.get(url, params=params, timeout=timeout)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    self.logger.warning("ArXiv rate limit hit (429). Backing off.")
                    time.sleep(delay * 2)
                else:
                    self.logger.error("ArXiv error status %d", response.status_code)
            except requests.RequestException as e:
                self.logger.warning("Network issue during arXiv fetch (Attempt %d): %s", attempt, e)

            if attempt < retry_count:
                self.logger.info("Retrying fetch in %.1f seconds...", delay)
                time.sleep(delay)
                delay *= 2.0

        raise requests.RequestException("Max retry attempts reached for arXiv API request")

    def _parse_xml_feed(
        self, xml_string: str, cutoff_date: Optional[datetime]
    ) -> List[tuple[Optional[ResearchItem], bool]]:
        """
        Parses XML string into a list of tuples containing (ResearchItem, is_skipped).
        """
        results: List[tuple[Optional[ResearchItem], bool]] = []
        try:
            root = ET.fromstring(xml_string)
        except Exception as e:
            self.logger.error("Malformed XML content received from API: %s", e)
            raise CollectionError("ArXiv", f"XML root parse failed: {e}") from e

        for entry_el in root.findall("atom:entry", self.NAMESPACES):
            try:
                item, is_skipped = self._parse_single_entry(entry_el, cutoff_date)
                results.append((item, is_skipped))
            except Exception as e:
                self.logger.warning("Failed to parse single entry: %s. Skipping.", e)
                results.append((None, True))

        return results

    def _parse_single_entry(
        self, entry_el: ET.Element, cutoff_date: Optional[datetime]
    ) -> tuple[Optional[ResearchItem], bool]:
        """
        Extracts metadata from a single <entry> element and maps it to a ResearchItem.
        """
        # 1. Identifier / arXiv URL
        id_el = entry_el.find("atom:id", self.NAMESPACES)
        raw_id_url = id_el.text.strip() if id_el is not None and id_el.text else ""
        if not raw_id_url:
            self.logger.warning("Paper entry lacks ID tag. Skipping.")
            return None, True

        # Extract deterministic ID from the end of the URL
        canonical_id = raw_id_url.split("/abs/")[-1].split("/pdf/")[-1].strip()

        # Extract version
        version = "1"
        v_match = re.search(r"v(\d+)$", raw_id_url)
        if v_match:
            version = v_match.group(1)

        # 2. Title
        title_el = entry_el.find("atom:title", self.NAMESPACES)
        raw_title = title_el.text if title_el is not None and title_el.text else ""
        title = " ".join(raw_title.split()).strip() if raw_title else "Untitled arXiv Paper"

        # 3. Summary / Abstract
        summary_el = entry_el.find("atom:summary", self.NAMESPACES)
        raw_summary = summary_el.text if summary_el is not None and summary_el.text else ""
        summary = " ".join(raw_summary.split()).strip() if raw_summary else ""

        # 4. Dates
        published_el = entry_el.find("atom:published", self.NAMESPACES)
        published_text = published_el.text.strip() if published_el is not None and published_el.text else ""
        publication_date = self._parse_iso_date(published_text)

        updated_el = entry_el.find("atom:updated", self.NAMESPACES)
        updated_text = updated_el.text.strip() if updated_el is not None and updated_el.text else ""
        updated_date = self._parse_iso_date(updated_text)

        # Apply publication date filtering (days_back parameter)
        if cutoff_date is not None:
            # Check against publication_date or updated_date (using whichever is newer/available)
            target_date = publication_date or updated_date
            if target_date:
                # Handle comparison (ensure target is timezone-aware for correct compare)
                tz_target = target_date.replace(tzinfo=timezone.utc) if target_date.tzinfo is None else target_date
                if tz_target < cutoff_date:
                    self.logger.debug("Skipping paper [%s] - older than cutoff.", title)
                    return None, True

        # 5. Authors and Organizations
        authors_list: List[Author] = []
        organizations: List[str] = []

        for author_el in entry_el.findall("atom:author", self.NAMESPACES):
            name_el = author_el.find("atom:name", self.NAMESPACES)
            if name_el is not None and name_el.text:
                author_name = " ".join(name_el.text.split()).strip()
                aff_el = author_el.find("arxiv:affiliation", self.NAMESPACES)
                affiliation = " ".join(aff_el.text.split()).strip() if aff_el is not None and aff_el.text else None
                
                authors_list.append(Author(name=author_name, affiliation=affiliation))
                if affiliation:
                    organizations.append(affiliation)

        primary_org = organizations[0] if organizations else None

        # 6. Links (PDF and arXiv urls)
        pdf_url = ""
        arxiv_url = raw_id_url

        for link_el in entry_el.findall("atom:link", self.NAMESPACES):
            rel = link_el.attrib.get("rel")
            title_attr = link_el.attrib.get("title")
            href = link_el.attrib.get("href", "").strip()
            type_attr = link_el.attrib.get("type")

            if rel == "alternate" and href:
                arxiv_url = href
            if (title_attr == "pdf" or rel == "related" and type_attr == "application/pdf") and href:
                pdf_url = href

        # If PDF URL not explicitly declared, construct from alternate/ID
        if not pdf_url and arxiv_url and "/abs/" in arxiv_url:
            pdf_url = arxiv_url.replace("/abs/", "/pdf/") + ".pdf"
        elif not pdf_url and arxiv_url:
            pdf_url = f"https://arxiv.org/pdf/{canonical_id}.pdf"

        # Ensure we have clean protocol prefix
        if not arxiv_url.startswith("http"):
            arxiv_url = f"https://arxiv.org/abs/{canonical_id}"

        # 7. DOI
        doi_el = entry_el.find("arxiv:doi", self.NAMESPACES)
        doi = doi_el.text.strip() if doi_el is not None and doi_el.text else None

        # 8. Primary Category and Tags
        prim_cat_el = entry_el.find("arxiv:primary_category", self.NAMESPACES)
        primary_category = prim_cat_el.attrib.get("term", "").strip() if prim_cat_el is not None else ""

        categories = []
        for cat_el in entry_el.findall("atom:category", self.NAMESPACES):
            term = cat_el.attrib.get("term", "").strip()
            if term and term not in categories:
                categories.append(term)

        if not primary_category and categories:
            primary_category = categories[0]

        # Use categories directly as keywords tags
        tags = [c.lower() for c in categories]

        # Extra raw payload for preservation of original XML source
        raw_payload = {
            "arxiv_id": canonical_id,
            "primary_category": primary_category,
            "doi": doi,
            "updated": updated_text,
            "version": version,
        }

        # Create production model ResearchItem
        item = ResearchItem(
            id=canonical_id,
            title=title,
            source_name="arXiv",
            source_type="preprint",
            url=arxiv_url,
            publication_date=publication_date,
            discovered_date=datetime.now(timezone.utc),
            authors=authors_list,
            organization=primary_org,
            summary=summary,
            tags=tags,
            categories=categories,
            raw_metadata=raw_payload,
            version=f"1.0.0+v{version}",
            raw_content=summary,  # Backwards compatibility field
        )

        return item, False

    def _parse_iso_date(self, date_str: str) -> Optional[datetime]:
        """
        Parses ISO format UTC dates from arXiv XML feed.
        """
        if not date_str:
            return None
        try:
            cleaned = date_str.strip().replace("Z", "+00:00")
            return datetime.fromisoformat(cleaned)
        except Exception:
            for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
        return None
