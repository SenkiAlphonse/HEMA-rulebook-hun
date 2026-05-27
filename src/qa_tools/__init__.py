"""
HEMA Rulebook Q&A Tools Package

This package provides search engine, indexing, and utility tools for querying
the Hungarian Historical European Martial Arts (HEMA) rulebook.

Main Components:
- search_engine: Search implementation (AliasAwareSearch with alias + case-insensitive lookup)
- tools: Utility scripts for indexing, aliases, and analysis
- data: Configuration and index files

Usage:
    from qa_tools.search_engine import AliasAwareSearch
    from qa_tools.tools import add_aliases, check_variants
"""

__version__ = "1.0.0"
__author__ = "HEMA Rulebook Project"

from qa_tools.search_engine.search_aliases import AliasAwareSearch

__all__ = [
    "AliasAwareSearch",
]
