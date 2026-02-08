"""
HEMA Rulebook Search Engine
Simple keyword-based search over indexed rules
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Represents a search result"""
    rule_id: str
    text: str
    section: str
    subsection: str
    document: str
    weapon_type: str
    variant: str
    score: float  # Relevance score


class RulebookSearch:
    """Search engine for HEMA rulebook"""
    
    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self.rules = []
        self.load_index()
    
    def load_index(self):
        """Load the rules index from JSON"""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_path}")
        
        with open(self.index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.rules = data['rules']
        
        print(f"Loaded {len(self.rules)} rules from index")
    
    def search(self, query: str, max_results: int = 5, 
               weapon_filter: str = None, formatum_filter: str = None) -> List[SearchResult]:
        """
        Search for rules matching the query.
        For level 4-5 rules, includes parent rules (up to level 3) and direct children.
        
        Args:
            query: Search query (keywords, natural language, or rule ID)
            max_results: Maximum number of result groups to return
            weapon_filter: Filter by weapon type (e.g., "longsword")
            formatum_filter: Filter by format/variant (e.g., "VOR", "COMBAT", "AFTERBLOW")
        
        Returns:
            List of SearchResult objects, grouped by rule lineage and sorted by relevance
        """
        query_lower = query.lower()
        query_terms = self._extract_terms(query_lower)
        
        # Extract format/variant from query if present (e.g., "VOR", "Combat")
        detected_formatum = self._detect_formatum_in_query(query)
        
        results = []
        
        for rule in self.rules:
            # Apply filters
            if weapon_filter and rule.get('weapon_type') != weapon_filter:
                continue
            
            # Use explicit filter or detected from query
            effective_formatum_filter = formatum_filter or detected_formatum
            if effective_formatum_filter:
                rule_formatum = rule.get('formatum', '').upper()
                if rule_formatum and rule_formatum != effective_formatum_filter.upper():
                    continue
            
            # Calculate relevance score
            score = self._calculate_score(rule, query_lower, query_terms)
            
            if score > 0:
                results.append(SearchResult(
                    rule_id=rule['rule_id'],
                    text=rule['text'],
                    section=rule['section'],
                    subsection=rule['subsection'],
                    document=rule['document'],
                    weapon_type=rule.get('weapon_type', ''),
                    variant=rule.get('formatum', ''),
                    score=score
                ))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x.score, reverse=True)
        
        # Group results: for level 4-5 rules, include parents and children
        grouped_results = []
        seen_root_ids = set()  # Track which root rules we've already processed
        
        for result in results:
            depth = self._get_rule_depth(result.rule_id)
            
            # For level 4-5 rules, find the root of the hierarchy (level 1 or 2)
            if depth >= 4:
                lineage = self._get_rule_lineage(result.rule_id)
                # Root is the smallest parent that's not just the prefix
                root_id = lineage[1] if len(lineage) > 1 else result.rule_id
                
                if root_id not in seen_root_ids:
                    seen_root_ids.add(root_id)
                    
                    # Collect all related rules: parents + matched rule + children
                    related_ids = set(lineage) | {result.rule_id} | set(self._get_children_rules(result.rule_id))
                    
                    # Find all matching results that are in this family
                    family_results = [r for r in results if r.rule_id in related_ids]
                    family_results.sort(key=lambda x: (
                        self._get_rule_depth(x.rule_id),  # Sort by depth
                        results.index(x)  # Then by original order
                    ))
                    
                    grouped_results.extend(family_results)
            else:
                # For level 1-3 rules, just add them if not already added as part of a family
                rule_in_group = any(r.rule_id == result.rule_id for r in grouped_results)
                if not rule_in_group:
                    grouped_results.append(result)
        
        return grouped_results[:max_results]
    
    def _extract_terms(self, query: str) -> List[str]:
        """Extract search terms from query"""
        # Remove Hungarian stop words and punctuation
        stop_words = {'a', 'az', 'és', 'vagy', 'de', 'ha', 'hogy', 'mi', 'van', 'volt'}
        terms = re.findall(r'\w+', query)
        return [t for t in terms if t not in stop_words and len(t) > 2]
    
    def _detect_formatum_in_query(self, query: str) -> str:
        """
        Detect if query contains references to specific formats/variants.
        Returns the detected formatum (VOR, COMBAT, AFTERBLOW) or empty string.
        """
        query_upper = query.upper()
        
        # Check for format keywords
        if 'VOR' in query_upper:
            return 'VOR'
        elif 'COMBAT' in query_upper:
            return 'COMBAT'
        elif 'AFTERBLOW' in query_upper or 'AFTER' in query_upper:
            return 'AFTERBLOW'
        
        # Check for Hungarian variant names
        if 'ELŐBOTLÁS' in query_upper or 'VORBEIGEHEN' in query_upper:
            return 'VOR'
        elif 'SZABADHARC' in query_upper:
            return 'COMBAT'
        
        return ''
    
    def _calculate_score(self, rule: Dict[str, Any], query: str, terms: List[str]) -> float:
        """Calculate relevance score for a rule"""
        score = 0.0
        
        # Combine searchable text
        text_lower = rule['text'].lower()
        section_lower = rule['section'].lower()
        subsection_lower = rule['subsection'].lower()
        rule_id_lower = rule['rule_id'].lower()
        rule_formatum = rule.get('formatum', '').upper()
        
        # Exact rule ID match (highest priority)
        if rule_id_lower in query:
            score += 100.0
        
        # Exact phrase match in text
        if query in text_lower:
            score += 50.0
        
        # Exact phrase match in section/subsection
        if query in section_lower or query in subsection_lower:
            score += 30.0
        
        # Term frequency in text
        for term in terms:
            count_in_text = text_lower.count(term)
            score += count_in_text * 10.0
            
            # Bonus for terms in section/subsection
            if term in section_lower or term in subsection_lower:
                score += 5.0
        
        # Bonus for specific weapon rules if relevant
        if any(weapon_term in query for weapon_term in ['hosszúkard', 'longsword', 'rapir', 'rapier']):
            if rule.get('weapon_type') != 'general':
                score += 10.0
        
        # Bonus for formatum-specific rules if query contains variant keywords
        detected_formatum = self._detect_formatum_in_query(query)
        if detected_formatum and rule_formatum:
            if rule_formatum == detected_formatum.upper():
                score += 25.0  # Significant bonus for matching variant
            elif rule_formatum == '':  # General rules get slight bonus
                score += 5.0
        
        return score
    
    def get_rule_by_id(self, rule_id: str) -> Dict[str, Any]:
        """Get a specific rule by its ID"""
        for rule in self.rules:
            if rule['rule_id'].lower() == rule_id.lower():
                return rule
        return None
    
    def get_rules_by_section(self, section_name: str) -> List[Dict[str, Any]]:
        """Get all rules in a specific section"""
        return [rule for rule in self.rules 
                if section_name.lower() in rule['section'].lower()]
    
    def _get_rule_depth(self, rule_id: str) -> int:
        """Get depth of rule from its ID (e.g., GEN-6.7.4.2 → depth 4, LS-AB-1.2.10.2 → depth 4)"""
        if not rule_id or '-' not in rule_id:
            return 0
        # The numeric part is always the last part after splitting by '-'
        numeric_part = rule_id.split('-')[-1]
        return numeric_part.count('.') + 1
    
    def _get_rule_lineage(self, rule_id: str) -> List[str]:
        """Get list of parent rule IDs for a given rule (e.g., GEN-6.7.4.2 → [GEN, GEN-6, GEN-6.7, GEN-6.7.4])"""
        if not rule_id or '-' not in rule_id:
            return []
        
        prefix, numeric = rule_id.split('-', 1)
        parts = numeric.split('.')
        lineage = [prefix]  # Start with just prefix (e.g., GEN)
        
        # Build each parent level
        for i in range(len(parts) - 1):  # -1 because we don't include the full rule ID
            parent_numeric = '.'.join(parts[:i+1])
            lineage.append(f"{prefix}-{parent_numeric}")
        
        return lineage
    
    def _get_children_rules(self, rule_id: str) -> List[str]:
        """Get rule IDs of direct children of a given rule"""
        depth = self._get_rule_depth(rule_id)
        children = []
        
        # Find rules with depth = current depth + 1
        for rule in self.rules:
            rule_depth = self._get_rule_depth(rule['rule_id'])
            if rule_depth == depth + 1 and rule['rule_id'].startswith(rule_id + '.'):
                children.append(rule['rule_id'])
        
        return sorted(children)


def format_result(result: SearchResult, show_context: bool = True) -> str:
    """Format a search result for display"""
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


def main():
    """Interactive search CLI"""
    import sys
    
    # Get the index path
    current_dir = Path(__file__).parent
    index_path = current_dir / "rules_index.json"
    
    if not index_path.exists():
        print("Error: Index not found. Please run parser.py first to create the index.")
        sys.exit(1)
    
    # Initialize search engine
    search_engine = RulebookSearch(index_path)
    
    print("\n" + "="*70)
    print("HEMA Rulebook Search Engine")
    print("="*70)
    print("\nEnter your query (or 'quit' to exit)")
    print("\nExample queries:")
    print("  - találati felület")
    print("  - valid target areas")
    print("  - GEN-1.1.1")
    print("  - hosszúkard vágás")
    print("  - VOR mérkőzés (searches only VOR variant rules)")
    print("  - COMBAT 5 találat")
    print("  - AFTERBLOW pontozás")
    print("\nFilters (use space-separated):")
    print("  - Add 'VOR', 'COMBAT', or 'AFTERBLOW' to filter by variant")
    print("  - Add 'longsword' or 'rapier' to filter by weapon")
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
