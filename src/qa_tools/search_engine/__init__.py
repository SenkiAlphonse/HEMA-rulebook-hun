"""
Search Engine Module

Provides alias-aware search for rulebook querying.

Classes:
- AliasAwareSearch: Production search engine with alias support and
  case-insensitive rule ID lookup.
- SearchResult: Dataclass representing a single search hit.
"""

from qa_tools.search_engine.search_aliases import AliasAwareSearch, SearchResult

__all__ = [
    "AliasAwareSearch",
    "SearchResult",
]
