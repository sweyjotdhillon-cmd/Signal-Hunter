"""
Signal Hunter collectors package.

Houses all source integrations (papers, blogs, github, etc.) inheriting from BaseCollector.
"""

from collectors.base import BaseCollector
from collectors.arxiv import ArXivCollector
from collectors.github_trending import GitHubTrendingCollector
from collectors.tech_blogs import TechBlogsCollector

__all__ = ["BaseCollector", "ArXivCollector", "GitHubTrendingCollector", "TechBlogsCollector"]
