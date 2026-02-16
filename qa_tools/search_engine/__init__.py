"""
Search Engine Module

Provides different search implementations for rulebook querying.

Classes:
- AliasAwareSearch: Production search engine with alias support
- RulebookSearch: Backward-compatible wrapper around AliasAwareSearch
  (simplified demo/test fixture without alias expansion)
"""

from qa_tools.search_engine.search_aliases import AliasAwareSearch
from qa_tools.search_engine.search import RulebookSearch

__all__ = [
    "AliasAwareSearch",
    "RulebookSearch",
]
