"""
Signal Hunter Tech Blogs RSS/Atom Collector.

Requests RSS/Atom feeds of configured prominent engineering blogs, parses their XML structure,
and maps entries to unified ResearchItem objects.
"""

import re
import time
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, List, Optional, Dict
import requests

from collectors.base import BaseCollector
from models.research_item import ResearchItem, Author, Source
from utils.exceptions import CollectionError


class TechBlogsCollector(BaseCollector):
    """
    Ingests official engineering blog announcements from OpenAI, Google DeepMind, Netflix, etc.
    """

    @property
    def name(self) -> str:
        """
        Return the unique descriptive name of the collector.
        """
        return "Tech_Blogs"

    def _map_to_feed_url(self, source_url: str) -> str:
        """
        Maps a standard landing page URL to its typical RSS/Atom feed URL.
        """
        url = source_url.lower().strip()
        
        if "openai.com" in url:
            # OpenAI typically uses newsroom rss
            return "https://openai.com/newsroom/rss.xml"
        if "deepmind" in url:
            return "https://deepmind.google/blog/feed/basic/"
        if "netflixtechblog" in url or "netflix.com" in url:
            return "https://netflixtechblog.com/feed"
        
        # If it already looks like a feed, return it
        if url.endswith("/feed") or url.endswith(".xml") or "/rss" in url:
            return source_url
            
        # Default fallback is to try appending /feed
        if url.endswith("/"):
            return source_url + "feed"
        return source_url + "/feed"

    def collect(self) -> List[ResearchItem]:
        """
        Scan configured tech blog feeds and return parsed ResearchItem objects.
        """
        self.logger.info("Starting collection from Tech Blogs feeds")

        sources: List[str] = self.config.sources or [
            "https://openai.com/blog",
            "https://deepmind.google/discover",
            "https://netflixtechblog.com"
        ]
        max_results: int = int(self.config.params.get("max_results", 10))
        timeout: float = float(self.config.params.get("timeout", 10.0))

        collected_items: List[ResearchItem] = []
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SignalHunter/2.0; +https://ai.studio/build)",
        }

        for source in sources:
            feed_url = self._map_to_feed_url(source)
            self.logger.info("Parsing blog feed: %s (mapped from: %s)", feed_url, source)

            try:
                response = requests.get(feed_url, headers=headers, timeout=timeout)
                if response.status_code != 200:
                    self.logger.warning("Failed to fetch feed %s: status %d", feed_url, response.status_code)
                    continue

                xml_data = response.text
                items_parsed = self._parse_feed_xml(xml_data, source)
                
                for item in items_parsed:
                    # Avoid duplicates
                    if not any(x.unique_id == item.unique_id for x in collected_items):
                        collected_items.append(item)
                    if len(collected_items) >= max_results:
                        break

            except Exception as e:
                self.logger.error("Failed to parse feed at '%s': %s", feed_url, e)
                continue

            if len(collected_items) >= max_results:
                break

        self.logger.info("Completed Tech Blogs collection. Gathered: %d article(s).", len(collected_items))
        return collected_items

    def _parse_feed_xml(self, xml_string: str, original_source: str) -> List[ResearchItem]:
        """
        Parses either RSS or Atom feed formats.
        """
        results: List[ResearchItem] = []
        
        # Clean potential leading whitespace
        xml_string = xml_string.strip()
        if not xml_string:
            return results

        try:
            root = ET.fromstring(xml_string)
        except Exception as e:
            self.logger.warning("XML root parse failed: %s. Trying direct string pattern extraction fallback.", e)
            return self._fallback_regex_parse(xml_string, original_source)

        # Detect feed type (Atom vs RSS)
        # Atom usually has a namespace and <feed> as root
        # RSS usually has <rss> as root with <channel>
        
        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "content": "http://purl.org/rss/1.0/modules/content/",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

        # Handle RSS (typically Root is 'rss' with 'channel/item' children)
        channel = root.find("channel")
        if channel is not None:
            source_name = channel.findtext("title") or self._extract_domain(original_source)
            for item_el in channel.findall("item"):
                try:
                    item = self._parse_rss_item(item_el, source_name, original_source, namespaces)
                    if item:
                        results.append(item)
                except Exception as ex:
                    self.logger.debug("Skipped RSS item parse: %s", ex)
            return results

        # Handle Atom Feed
        # Check if root is atom <feed> or has atom namespace
        is_atom = "feed" in root.tag.lower() or root.find("{http://www.w3.org/2005/Atom}entry") is not None
        if is_atom:
            # We will use namespace-agnostic search or direct tag comparison
            ns_prefix = ""
            if "{" in root.tag:
                ns_prefix = root.tag.split("}")[0] + "}"
                
            source_name = root.findtext(f"{ns_prefix}title") or self._extract_domain(original_source)
            for entry_el in root.findall(f"{ns_prefix}entry"):
                try:
                    item = self._parse_atom_entry(entry_el, source_name, original_source, ns_prefix)
                    if item:
                        results.append(item)
                except Exception as ex:
                    self.logger.debug("Skipped Atom entry parse: %s", ex)
            return results

        return results

    def _parse_rss_item(self, el: ET.Element, source_name: str, original_source: str, ns: Dict[str, str]) -> Optional[ResearchItem]:
        title = el.findtext("title")
        link = el.findtext("link")
        if not title or not link:
            return None

        # Standard clean title
        title = " ".join(title.split()).strip()
        link = link.strip()

        guid = el.findtext("guid") or link
        unique_id = f"techblog-{re.sub(r'[^a-zA-Z0-9]', '', guid)}"

        pub_date_str = el.findtext("pubDate")
        pub_date = self._parse_date(pub_date_str)

        summary = el.findtext("description") or ""
        # Strip simple HTML from description if any
        summary = re.sub(r"<[^>]+>", "", summary).strip()
        summary = " ".join(summary.split())
        if len(summary) > 350:
            summary = summary[:347] + "..."

        author_name = el.findtext("author") or el.findtext("{http://purl.org/dc/elements/1.1/}creator") or "Engineering Team"
        
        # Extract categories/tags
        tags = []
        for cat_el in el.findall("category"):
            if cat_el.text:
                tags.append(cat_el.text.strip().lower())

        domain = self._extract_domain(original_source)

        return ResearchItem(
            id=unique_id,
            title=title,
            source_name=domain,
            source_type="engineering_blog",
            url=link,
            publication_date=pub_date,
            discovered_date=datetime.now(timezone.utc),
            authors=[Author(name=author_name)],
            organization=domain,
            summary=summary,
            tags=tags or [domain.lower(), "engineering-blog"],
            categories=["Engineering Blog"],
            raw_content=summary,
            raw_metadata={
                "original_feed": original_source,
                "author": author_name,
            }
        )

    def _parse_atom_entry(self, el: ET.Element, source_name: str, original_source: str, ns_prefix: str) -> Optional[ResearchItem]:
        title = el.findtext(f"{ns_prefix}title")
        
        # Link in Atom is an element with href attribute
        link_el = el.find(f"{ns_prefix}link")
        link = ""
        if link_el is not None:
            link = link_el.attrib.get("href", "").strip()
            
        if not title or not link:
            return None

        title = " ".join(title.split()).strip()

        entry_id = el.findtext(f"{ns_prefix}id") or link
        unique_id = f"techblog-{re.sub(r'[^a-zA-Z0-9]', '', entry_id)}"

        pub_date_str = el.findtext(f"{ns_prefix}published") or el.findtext(f"{ns_prefix}updated")
        pub_date = self._parse_date(pub_date_str)

        summary_el = el.find(f"{ns_prefix}summary") or el.find(f"{ns_prefix}content")
        summary = summary_el.text if summary_el is not None and summary_el.text else ""
        summary = re.sub(r"<[^>]+>", "", summary).strip()
        summary = " ".join(summary.split())
        if len(summary) > 350:
            summary = summary[:347] + "..."

        author_el = el.find(f"{ns_prefix}author")
        author_name = "Engineering Team"
        if author_el is not None:
            name_el = author_el.find(f"{ns_prefix}name")
            if name_el is not None and name_el.text:
                author_name = name_el.text.strip()

        domain = self._extract_domain(original_source)

        return ResearchItem(
            id=unique_id,
            title=title,
            source_name=domain,
            source_type="engineering_blog",
            url=link,
            publication_date=pub_date,
            discovered_date=datetime.now(timezone.utc),
            authors=[Author(name=author_name)],
            organization=domain,
            summary=summary,
            tags=[domain.lower(), "tech-news"],
            categories=["Engineering Blog"],
            raw_content=summary,
            raw_metadata={
                "original_feed": original_source,
                "author": author_name,
            }
        )

    def _fallback_regex_parse(self, xml_string: str, original_source: str) -> List[ResearchItem]:
        """
        Extremely basic, fault-tolerant regex parser in case XML parser breaks on custom namespaces or characters.
        """
        results = []
        items = re.findall(r"<item>(.*?)</item>", xml_string, re.DOTALL)
        domain = self._extract_domain(original_source)
        
        for item_data in items[:10]:
            try:
                title_match = re.search(r"<title>(.*?)</title>", item_data, re.DOTALL)
                link_match = re.search(r"<link>(.*?)</link>", item_data, re.DOTALL)
                
                if title_match and link_match:
                    title = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", title_match.group(1)).strip()
                    link = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", link_match.group(1)).strip()
                    
                    desc_match = re.search(r"<description>(.*?)</description>", item_data, re.DOTALL)
                    summary = ""
                    if desc_match:
                        summary = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", desc_match.group(1)).strip()
                        summary = re.sub(r"<[^>]+>", "", summary)
                        summary = " ".join(summary.split())
                        if len(summary) > 350:
                            summary = summary[:347] + "..."
                            
                    unique_id = f"techblog-{re.sub(r'[^a-zA-Z0-9]', '', link)}"
                    
                    results.append(
                        ResearchItem(
                            id=unique_id,
                            title=title,
                            source_name=domain,
                            source_type="engineering_blog",
                            url=link,
                            publication_date=datetime.now(timezone.utc),
                            discovered_date=datetime.now(timezone.utc),
                            authors=[Author(name="Engineering Team")],
                            organization=domain,
                            summary=summary or f"New blog update from {domain}",
                            tags=[domain.lower()],
                            categories=["Engineering Blog"],
                            raw_content=summary,
                        )
                    )
            except Exception:
                continue
        return results

    def _extract_domain(self, url: str) -> str:
        """Extracts simple name from URL, e.g. openai.com or netflixtechblog.com"""
        try:
            clean = url.replace("https://", "").replace("http://", "").replace("www.", "")
            parts = clean.split("/")
            return parts[0]
        except Exception:
            return "Engineering Blog"

    def _parse_date(self, date_str: Optional[str]) -> datetime:
        """
        Standard parser for multiple feed date patterns (pubDate or ISO format).
        """
        if not date_str:
            return datetime.now(timezone.utc)
        date_str = date_str.strip()
        
        # Try ISO format
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            pass
            
        # Try RFC 822 format (e.g., Fri, 05 May 2023 18:24:00 GMT)
        formats = [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S",
            "%d %b %Y %H:%M:%S %Z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
                
        return datetime.now(timezone.utc)
