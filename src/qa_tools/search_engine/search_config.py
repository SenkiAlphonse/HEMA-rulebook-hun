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
SCORE_RULE_ID_MATCH: Final[float] = 1000.0  # Exact rule IDs use a separate priority tier
MAX_NON_ID_SCORE: Final[float] = 999.0
SCORE_EXACT_PHRASE_TEXT: Final[float] = 50.0  # Exact phrase found in rule text
SCORE_EXACT_PHRASE_SECTION: Final[float] = 30.0  # Exact phrase in section/subsection
SCORE_TERM_MATCH: Final[float] = 10.0  # Per distinct query term present in rule text
SCORE_TERM_SECTION: Final[float] = 5.0  # Per distinct query term in section/subsection
SCORE_CONCEPT_TERM: Final[float] = 15.0  # One boost for any matching concept alias
SCORE_VARIANT_ALIAS: Final[float] = 40.0  # One boost for variant metadata or alias
SCORE_WEAPON_ALIAS: Final[float] = 20.0  # One boost for weapon metadata or alias

# Length penalty for very long rules (e.g., large tables)
# Rules longer than threshold get exponentially lower scores
LENGTH_PENALTY_THRESHOLD: Final[int] = 2000  # Character threshold
LENGTH_PENALTY_EXP: Final[float] = 1.5  # Exponential penalty factor
