"""
Filtering and normalization utilities for HEMA rulebook app.
"""
from typing import Optional, List


def normalize_filter(value: Optional[str], allowed: List[str]) -> Optional[str]:
    """Validate and normalize filter values"""
    if value:
        value_upper = value.upper()
        if value_upper in allowed:
            return value_upper
    return None
