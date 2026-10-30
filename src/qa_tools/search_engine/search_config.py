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
SCORE_ALIAS_TEXT: Final[float] = 40.0  # One boost per alias group found in rule text
SCORE_ALIAS_SECTION: Final[float] = 20.0  # One boost per alias group found in a heading

# Length penalty for very long rules (e.g., large tables)
# Rules longer than threshold get exponentially lower scores
LENGTH_PENALTY_THRESHOLD: Final[int] = 2000  # Character threshold
LENGTH_PENALTY_EXP: Final[float] = 1.5  # Exponential penalty factor
