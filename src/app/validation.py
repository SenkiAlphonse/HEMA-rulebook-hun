"""
Input validation utilities for HEMA rulebook search engine
"""

import re
from typing import Optional, Tuple


# Validation constraints
MAX_QUERY_LENGTH = 1000
MIN_QUERY_LENGTH = 1
RULE_ID_PATTERN = re.compile(r'^[A-Z]+(?:-[A-Z]+)*-[\d.]+$')
MAX_RESULTS = 100


def validate_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate search query.
    
    Args:
        query: Search query to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - (True, None) if valid
        - (False, error_message) if invalid
    """
    if not isinstance(query, str):
        return False, "Query must be a string"
    
    query = query.strip()
    
    if len(query) < MIN_QUERY_LENGTH:
        return False, f"Query must be at least {MIN_QUERY_LENGTH} character"
    
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Query must not exceed {MAX_QUERY_LENGTH} characters (got {len(query)})"
    
    return True, None


def validate_rule_id(rule_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate rule ID format.
    
    Args:
        rule_id: Rule ID to validate (e.g., "GEN-1.1.1", "LS-VOR-1.2.3")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(rule_id, str):
        return False, "Rule ID must be a string"
    
    rule_id = rule_id.strip()
    
    if not rule_id:
        return False, "Rule ID cannot be empty"
    
    if not RULE_ID_PATTERN.match(rule_id):
        return False, f"Invalid rule ID format: {rule_id}. Expected format: PREFIX-1.2.3 or PREFIX-SUB-1.2.3"
    
    return True, None


def validate_filter(value: Optional[str], allowed_values: list) -> Tuple[bool, Optional[str]]:
    """
    Validate filter value against allowed list.
    
    Args:
        value: Filter value to validate
        allowed_values: List of allowed values
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        return True, None
    
    if not isinstance(value, str):
        return False, f"Filter value must be a string, got {type(value).__name__}"
    
    value = value.strip()
    
    if not value:
        return True, None  # Empty string is treated as no filter
    
    if value not in allowed_values:
        return False, f"Invalid filter value: {value}. Allowed values: {', '.join(allowed_values)}"
    
    return True, None


def validate_max_results(max_results: int, max_allowed: int = MAX_RESULTS) -> Tuple[bool, Optional[str]]:
    """
    Validate max_results parameter.
    
    Args:
        max_results: Maximum number of results requested
        max_allowed: Maximum allowed value
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(max_results, int):
        return False, f"max_results must be an integer, got {type(max_results).__name__}"
    
    if max_results < 1:
        return False, f"max_results must be at least 1, got {max_results}"
    
    if max_results > max_allowed:
        return False, f"max_results must not exceed {max_allowed}, got {max_results}"
    
    return True, None


def sanitize_query(query: str) -> str:
    """
    Sanitize query for search (remove extra whitespace, etc).
    
    Args:
        query: Query to sanitize
        
    Returns:
        Sanitized query
    """
    # Strip leading/trailing whitespace
    query = query.strip()
    
    # Collapse multiple spaces into single space
    query = re.sub(r'\s+', ' ', query)
    
    return query
