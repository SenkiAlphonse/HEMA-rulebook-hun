"""
HEMA Rulebook Search Engine - Simplified wrapper around AliasAwareSearch

This module provides backward compatibility for existing code that uses RulebookSearch.
Internally, it delegates to AliasAwareSearch (the production search engine) which provides
all the functionality needed for comprehensive rulebook querying.

The legacy RulebookSearch class is now a thin wrapper that:
1. Takes only an index_path (no aliases parameter)
2. Internally uses empty aliases dict (no alias expansion)
3. Maintains the same public API for backward compatibility with tests/demos
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from qa_tools.search_engine.search_aliases import AliasAwareSearch, SearchResult

# Re-export SearchResult for backward compatibility
__all__ = ['RulebookSearch', 'SearchResult', 'format_result', 'main']


class RulebookSearch:
    """
    Simple HEMA rulebook search engine (backward-compatible wrapper).
    
    This is now a wrapper around AliasAwareSearch for backward compatibility.
    It provides the same API but without alias expansion (which requires both
    index_path and aliases_path).
    
    Note: For new code, use AliasAwareSearch directly with both index and aliases paths.
    """
    
    def __init__(self, index_path: str):
        """Initialize search engine with just an index path (no aliases).
        
        Args:
            index_path: Path to rules_index.json
        """
        # Internally use AliasAwareSearch with empty aliases
        self._engine = AliasAwareSearch(index_path, "")
        # Public API compatibility
        self.rules = self._engine.rules
        self.index_path = Path(index_path)
    
    def search(self, query: str, max_results: int = 5,
               weapon_filter: str = None, variant_filter: str = None) -> List[SearchResult]:
        """Search for rules matching the query.
        
        Args:
            query: Search query (keywords, natural language, or rule ID)
            max_results: Maximum number of result groups to return
            weapon_filter: Filter by weapon type (e.g., "longsword")
            variant_filter: Filter by variant (e.g., "VOR", "COMBAT", "AFTERBLOW")
        
        Returns:
            List of SearchResult objects, sorted by relevance
        """
        return self._engine.search(query, max_results, weapon_filter, variant_filter)
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific rule by its ID (case-insensitive)."""
        # Try exact match first (case-sensitive)
        rule = self._engine.get_rule_by_id(rule_id)
        if rule:
            return rule
        
        # Try case-insensitive match
        rule_id_lower = rule_id.lower()
        for rule in self.rules:
            if rule.get('rule_id', '').lower() == rule_id_lower:
                return rule
        return None
    
    def get_rules_by_section(self, section_name: str) -> List[Dict[str, Any]]:
        """Get all rules in a specific section."""
        section_lower = section_name.lower()
        return [rule for rule in self.rules 
                if section_lower in rule.get('section', '').lower()]
    
    def get_rule_depth(self, rule_id: str) -> int:
        """Get depth of rule from its ID."""
        return self._engine.get_rule_depth(rule_id)
    
    def get_rule_lineage(self, rule_id: str) -> List[str]:
        """Get list of parent rule IDs."""
        return self._engine.get_rule_lineage(rule_id)
    
    def get_children_rules(self, rule_id: str) -> List[str]:
        """Get direct child rule IDs."""
        return self._engine.get_children_rules(rule_id)
    
    # Backward compatibility aliases for tests
    def _get_rule_depth(self, rule_id: str) -> int:
        """Get depth of rule from its ID (backward compat)."""
        return self.get_rule_depth(rule_id)
    
    def _get_rule_lineage(self, rule_id: str) -> List[str]:
        """Get list of parent rule IDs (backward compat)."""
        return self.get_rule_lineage(rule_id)
    
    def _get_children_rules(self, rule_id: str) -> List[str]:
        """Get direct child rule IDs (backward compat)."""
        return self.get_children_rules(rule_id)
    
    def _detect_variant_in_query(self, query: str) -> str:
        """Detect variant in query (backward compat)."""
        return self._engine._detect_variant_in_query(query)


def format_result(result: SearchResult, show_context: bool = True) -> str:
    """Format a search result for display."""
    output = []
    output.append(f"\n{'='*70}")
    output.append(f"Rule ID: {result.rule_id}")
    output.append(f"Document: {result.document}")
    
    # Display weapon type and variant
    display_parts = []
    if result.weapon_type and result.weapon_type != 'general':
        display_parts.append(result.weapon_type)
    if result.variant:
        display_parts.append(f"[{result.variant}]")
    
    if display_parts:
        output.append(f"Category: {' '.join(display_parts)}")
    
    if show_context:
        output.append(f"\nSection: {result.section}")
        if result.subsection:
            output.append(f"Subsection: {result.subsection}")
    
    output.append(f"\nText:\n{result.text}")
    output.append(f"\n[Relevance Score: {result.score:.1f}]")
    
    return "\n".join(output)


def main() -> None:
    """Interactive search CLI."""
    import sys
    
    # Get the index path
    current_dir = Path(__file__).parent.parent / "data"
    index_path = current_dir / "rules_index.json"
    
    if not index_path.exists():
        print("Error: Index not found. Please run parser.py first to create the index.")
        sys.exit(1)
    
    # Initialize search engine
    search_engine = RulebookSearch(str(index_path))
    
    print("\n" + "="*70)
    print("HEMA Rulebook Search Engine")
    print("="*70)
    print("\nEnter your query (or 'quit' to exit)")
    print("\nExample queries:")
    print("  - találati felület")
    print("  - valid target areas")
    print("  - GEN-1.1.1")
    print("  - hosszúkard vágás")
    print("  - VOR mérkőzés")
    print("  - COMBAT pontozás")
    print("-"*70)
    
    while True:
        try:
            query = input("\nQuery: ").strip()
            
            if not query or query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            # Search
            results = search_engine.search(query, max_results=5)
            
            if not results:
                print("\nNo results found. Try different keywords.")
                continue
            
            print(f"\nFound {len(results)} results:")
            
            for i, result in enumerate(results, 1):
                print(format_result(result))
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
