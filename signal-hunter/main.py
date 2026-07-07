"""
Signal Hunter - ArXiv Collector Demonstration.

This is the main entry point for the ArXiv collection demonstration.
It loads configuration, runs the ArXiv collector, and displays results.
"""

import sys
import logging
from config.config_loader import load_config
from collectors.arxiv import ArXivCollector
from utils.logger import setup_logger


def main() -> None:
    # 1. Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"FATAL: Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Setup logger
    setup_logger(
        name="signal_hunter",
        log_level=config.log_level,
    )

    # 3. Get ArXiv collector configuration
    arxiv_config = config.collectors.get("arxiv")
    if not arxiv_config:
        print("FATAL: ArXiv collector configuration is missing in settings.yaml", file=sys.stderr)
        sys.exit(1)

    # Force/override max_results to 25 for this demonstration as requested
    arxiv_config.params["max_results"] = 25

    # 4. Initialize and run collector
    try:
        collector = ArXivCollector(arxiv_config)
        papers = collector.collect()
    except Exception as e:
        print(f"FAILED: Collection failed with error: {e}", file=sys.stderr)
        sys.exit(1)

    # 5. Display output as requested by demonstration requirements:
    # "prints: Found 25 papers. and displays the first three papers."
    print(f"Found {len(papers)} papers.")

    for i, paper in enumerate(papers[:3], 1):
        print(f"\n--- Paper {i} ---")
        print(f"Title: {paper.title}")
        authors_str = ", ".join(author.name for author in paper.authors)
        print(f"Authors: {authors_str}")
        print(f"Publication Date: {paper.publication_date}")
        print(f"URL: {paper.url}")
        
        pdf_url = paper.raw_metadata.get("pdf_url")
        if not pdf_url and paper.url:
            pdf_url = paper.url.replace("/abs/", "/pdf/") + ".pdf"
        print(f"PDF URL: {pdf_url}")
        
        prim_cat = paper.raw_metadata.get("primary_category")
        if not prim_cat and paper.categories:
            prim_cat = paper.categories[0]
        print(f"Primary Category: {prim_cat}")
        
        print(f"Version: {paper.version}")
        if paper.organization:
            print(f"Organization: {paper.organization}")
        if paper.tags:
            print(f"Tags: {', '.join(paper.tags)}")
        print(f"Abstract: {paper.summary[:300]}...")


if __name__ == "__main__":
    main()
