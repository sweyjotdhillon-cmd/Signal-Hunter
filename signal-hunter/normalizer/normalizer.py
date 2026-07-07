"""
Signal Hunter Normalizer.

Standardizes fields of research items gathered from diverse collectors.
"""

import logging
from typing import List
from models.research_item import ResearchItem
from normalizer.base import BaseNormalizer
from utils.exceptions import NormalizationError
from utils.logger import setup_logger


"""
Signal Hunter Normalizer.

Standardizes fields of research items gathered from diverse collectors to ensure consistent schema contracts.
"""

import logging
import re
from datetime import datetime, timezone
from typing import List, Set, Optional, Any
from urllib.parse import urlparse, urlunparse

from models.research_item import ResearchItem
from normalizer.base import BaseNormalizer
from utils.exceptions import NormalizationError
from utils.logger import setup_logger


# Standard mappings for programming languages
PROGRAMMING_LANG_MAP = {
    "python": "Python",
    "rust": "Rust",
    "cpp": "C++",
    "c++": "C++",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "go": "Go",
    "golang": "Go",
    "java": "Java",
    "kotlin": "Kotlin",
    "swift": "Swift",
    "ruby": "Ruby",
    "scala": "Scala",
    "julia": "Julia",
    "shell": "Shell",
    "bash": "Shell",
    "html": "HTML",
    "css": "CSS"
}

# Standard mappings for technology names
TECH_MAP = {
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "transformers": "Transformers",
    "keras": "Keras",
    "jax": "JAX",
    "cuda": "CUDA",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "react": "React",
    "nextjs": "Next.js",
    "next.js": "Next.js",
    "vue": "Vue",
    "tailwindcss": "Tailwind CSS",
    "tailwind": "Tailwind CSS",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "sqlite": "SQLite",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "llm": "LLM",
    "bert": "BERT",
    "gpt": "GPT",
    "resnet": "ResNet",
    "diffusion": "Diffusion",
    "quantization": "Quantization",
    "lora": "LoRA",
    "rag": "RAG"
}

# Standard mappings for arXiv categories to ensure consistent casing
CATEGORY_MAP = {
    "cs.ai": "cs.AI",
    "cs.lg": "cs.LG",
    "cs.cl": "cs.CL",
    "cs.cv": "cs.CV",
    "cs.ne": "cs.NE",
    "cs.lo": "cs.LO",
    "cs.pl": "cs.PL",
    "cs.cc": "cs.CC"
}


def clean_whitespace(s: str) -> str:
    """Strip leading/trailing and replace multiple spaces with single space."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.strip())


def normalize_date(dt: Any) -> Optional[datetime]:
    """Standardize input date representation into a UTC timezone-aware datetime."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    if isinstance(dt, str):
        s = dt.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        # Try fromisoformat first
        try:
            parsed = datetime.fromisoformat(s)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            pass
        # Fallbacks for common web date/API formats
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z"
        ):
            try:
                parsed = datetime.strptime(s, fmt)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                continue
    return None


def normalize_url(url: str) -> str:
    """Normalize URLs by stripping, lowecasing protocol/host and stripping trailing slash."""
    if not url:
        return ""
    url = url.strip()
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path
        if path == "/":
            path = ""
        elif path.endswith("/") and len(path) > 1:
            path = path[:-1]
        return urlunparse((scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))
    except Exception:
        return url


def extract_keywords(text: str, mapping: dict) -> Set[str]:
    """Search for keyword occurrences in text using word boundaries."""
    found = set()
    for key, val in mapping.items():
        escaped_key = re.escape(key)
        pattern = rf"\b{escaped_key}\b"
        if re.search(pattern, text, re.IGNORECASE):
            found.add(val)
    return found


class PlaceholderNormalizer(BaseNormalizer):
    """
    Standardizes fields on ResearchItem objects to ensure consistent schema contracts.
    """

    def __init__(self) -> None:
        """Initialize the normalizer with setup logging."""
        self.logger: logging.Logger = setup_logger(
            "signal_hunter.normalizer",
            log_level="INFO",
        )
        self.logger.info("Initialized PlaceholderNormalizer (Production Engine)")

    def process(self, items: List[ResearchItem]) -> List[ResearchItem]:
        """
        Normalize dates, author names, URLs, categories, tags, programming languages, and technologies.

        Args:
            items (List[ResearchItem]): Raw collected research items.

        Returns:
            List[ResearchItem]: Normalized research items.

        Raises:
            NormalizationError: If standardizing fields fails.
        """
        if items is None:
            raise NormalizationError("Items list cannot be None")

        self.logger.info("Starting normalization stage on %d items", len(items))
        normalized: List[ResearchItem] = []

        for item in items:
            try:
                self.logger.debug("Normalizing item: '%s' (ID: %s)", item.title, item.id)

                # 1. Title Normalization
                item.title = clean_whitespace(item.title)

                # 2. Date Normalization (ISO 8601 UTC)
                if item.publication_date is not None:
                    pub_normalized = normalize_date(item.publication_date)
                    if pub_normalized:
                        item.publication_date = pub_normalized
                
                if item.discovered_date is not None:
                    disc_normalized = normalize_date(item.discovered_date)
                    if disc_normalized:
                        item.discovered_date = disc_normalized

                # 3. URL Normalization
                item.url = normalize_url(item.url)
                if item.github_repository:
                    item.github_repository = normalize_url(item.github_repository)
                
                if item.documentation_links:
                    item.documentation_links = [normalize_url(link) for link in item.documentation_links if link.strip()]
                
                if item.related_links:
                    item.related_links = [normalize_url(link) for link in item.related_links if link.strip()]

                # 4. Author Name Normalization
                for author in item.authors:
                    author.name = clean_whitespace(author.name).title()
                    if author.email:
                        author.email = clean_whitespace(author.email).lower()
                    if author.affiliation:
                        author.affiliation = clean_whitespace(author.affiliation)
                    if author.github_username:
                        author.github_username = clean_whitespace(author.github_username).replace("@", "")
                    if author.website:
                        author.website = normalize_url(author.website)

                # 5. Categories Normalization
                clean_categories = []
                seen_cats = set()
                for cat in item.categories:
                    c = clean_whitespace(cat)
                    c_lower = c.lower()
                    if c_lower in CATEGORY_MAP:
                        c = CATEGORY_MAP[c_lower]
                    if c and c not in seen_cats:
                        clean_categories.append(c)
                        seen_cats.add(c)
                item.categories = clean_categories

                # 6. Tags Normalization
                clean_tags = []
                seen_tags = set()
                for tag in item.tags:
                    t = clean_whitespace(tag).lower()
                    if t and t not in seen_tags:
                        clean_tags.append(t)
                        seen_tags.add(t)
                item.tags = clean_tags

                # 7. Programming Languages Normalization & Extraction
                normalized_langs = set()
                for lang in item.programming_languages:
                    lang_clean = clean_whitespace(lang).lower()
                    if lang_clean in PROGRAMMING_LANG_MAP:
                        normalized_langs.add(PROGRAMMING_LANG_MAP[lang_clean])
                    elif lang.strip():
                        normalized_langs.add(clean_whitespace(lang))

                # Extract from title, summary, tags, and categories
                search_text = f"{item.title} {item.summary or ''} {' '.join(item.tags)} {' '.join(item.categories)}"
                extracted_langs = extract_keywords(search_text, PROGRAMMING_LANG_MAP)
                normalized_langs.update(extracted_langs)
                item.programming_languages = sorted(list(normalized_langs))

                # 8. Technologies Normalization & Extraction
                normalized_techs = set()
                for tech in item.technologies:
                    tech_clean = clean_whitespace(tech).lower()
                    if tech_clean in TECH_MAP:
                        normalized_techs.add(TECH_MAP[tech_clean])
                    elif tech.strip():
                        normalized_techs.add(clean_whitespace(tech))

                extracted_techs = extract_keywords(search_text, TECH_MAP)
                normalized_techs.update(extracted_techs)
                item.technologies = sorted(list(normalized_techs))

                normalized.append(item)
            except Exception as e:
                self.logger.error("Failed to normalize item %s: %s", getattr(item, "id", "Unknown"), e)
                raise NormalizationError(f"Error during item normalization: {e}") from e

        self.logger.info("Completed normalization stage. Outbound: %d items", len(normalized))
        return normalized


# Alias to support both namings natively
ResearchItemNormalizer = PlaceholderNormalizer

