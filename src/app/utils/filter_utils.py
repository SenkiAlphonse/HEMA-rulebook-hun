"""
Filtering and normalization utilities for HEMA rulebook app.
"""

def normalize_filter(value: str | None, allowed: list[str]) -> str | None:
    """Validate and normalize filter values"""
    if value:
        value_upper = value.upper()
        if value_upper in allowed:
            return value_upper
    return None
