"""
Shared utilities for HEMA rulebook search functionality
"""

from typing import List, Dict, Any


def get_rule_depth(rule_id: str) -> int:
    """
    Calculate indentation depth from rule ID
    
    Examples:
        GEN-6.7.4.2 → depth 4
        LS-AB-1.2.10.2 → depth 4
        DIS-4.1.5.1 → depth 4
    
    Args:
        rule_id: Rule identifier (e.g., "GEN-6.7.4.2" or "LS-AB-1.2.10.2")
    
    Returns:
        Depth level (1-5), or 0 if invalid
    """
    if not rule_id or '-' not in rule_id:
        return 0
    
    # The numeric part is always the last part after splitting by '-'
    # This handles multi-part prefixes like "LS-AB"
    parts = rule_id.split('-')
    numeric_part = parts[-1]
    
    # Count dots in numeric part + 1 gives the depth
    return numeric_part.count('.') + 1


def get_rule_lineage(rule_id: str) -> List[str]:
    """
    Get list of parent rule IDs for a given rule
    
    Examples:
        GEN-6.7.4.2 → ["GEN", "GEN-6", "GEN-6.7", "GEN-6.7.4"]
        LS-AB-1.2.10.2 → ["LS-AB", "LS-AB-1", "LS-AB-1.2", "LS-AB-1.2.10"]
    
    Args:
        rule_id: Rule identifier
    
    Returns:
        List of parent rule IDs (excluding the rule itself)
    """
    if not rule_id or '-' not in rule_id:
        return []
    
    # Split to get prefix and numeric parts
    parts = rule_id.split('-')
    
    # Prefix could be multi-part (e.g., "LS-AB")
    prefix = '-'.join(parts[:-1])
    numeric = parts[-1]
    numeric_parts = numeric.split('.')
    
    lineage = [prefix]  # Start with just the prefix (e.g., "GEN" or "LS-AB")
    
    # Build up the hierarchy
    for i in range(len(numeric_parts)):
        parent_numeric = '.'.join(numeric_parts[:i+1])
        lineage.append(f"{prefix}-{parent_numeric}")
    
    # Remove the rule itself from lineage (we only want parents)
    return lineage[:-1]


def get_children_rules(rule_id: str, all_rules: List[Dict[str, Any]]) -> List[str]:
    """
    Get direct child rule IDs for a given rule
    
    Args:
        rule_id: Parent rule identifier
        all_rules: List of all rule dictionaries
    
    Returns:
        List of direct child rule IDs
    """
    if not rule_id or '-' not in rule_id:
        return []
    
    current_depth = get_rule_depth(rule_id)
    children = []
    
    for rule in all_rules:
        child_id = rule.get('rule_id', '')
        if child_id.startswith(rule_id + '.'):
            child_depth = get_rule_depth(child_id)
            if child_depth == current_depth + 1:
                children.append(child_id)
    
    return children
