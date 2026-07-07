"""
Signal Hunter collectors package.

Houses all source integrations (papers, blogs, github, etc.) inheriting from BaseCollector.
"""

from collectors.base import BaseCollector
from collectors.arxiv import ArXivCollector

__all__ = ["BaseCollector", "ArXivCollector"]
