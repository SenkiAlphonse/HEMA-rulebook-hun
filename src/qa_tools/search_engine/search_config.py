"""
Search engine configuration constants for HEMA Rulebook

This module centralizes all scoring weights, thresholds, and constants
used by the search engine to ensure consistency and ease of tuning.
"""

# Type hints for constants
from typing import Final

# Default maximum number of results to return
DEFAULT_MAX_RESULTS: Final[int] = 5

# Scoring weights - higher scores indicate better matches
SCORE_RULE_ID_MATCH: Final[float] = 100.0  # Direct rule ID match (highest priority)
SCORE_EXACT_PHRASE_TEXT: Final[float] = 50.0  # Exact phrase found in rule text
SCORE_EXACT_PHRASE_SECTION: Final[float] = 30.0  # Exact phrase in section/subsection
SCORE_TERM_FREQUENCY: Final[float] = 10.0  # Per occurrence of search term in text
SCORE_TERM_SECTION: Final[float] = 5.0  # Search term in section/subsection
SCORE_CONCEPT_TERM: Final[float] = 15.0  # Concept term from alias expansion
SCORE_VARIANT_ALIAS: Final[float] = 40.0  # Variant alias match (legacy)
SCORE_WEAPON_ALIAS: Final[float] = 20.0  # Weapon alias match (legacy)

# Length penalty for very long rules (e.g., large tables)
# Rules longer than threshold get exponentially lower scores
LENGTH_PENALTY_THRESHOLD: Final[int] = 2000  # Character threshold
LENGTH_PENALTY_EXP: Final[float] = 1.5  # Exponential penalty factor

# Grouping multiplier for hierarchical results
# Level 4-5 rules are grouped with parents/children, expanding result count
GROUPING_MULTIPLIER: Final[int] = 3
