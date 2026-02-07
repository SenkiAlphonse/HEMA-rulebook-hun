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
        Search for rules matching the query
        
        Args:
            query: Search query (keywords, natural language, or rule ID)
            max_results: Maximum number of results to return
            weapon_filter: Filter by weapon type (e.g., "longsword")
            formatum_filter: Filter by format/variant (e.g., "VOR", "COMBAT", "AFTERBLOW")
        
        Returns:
            List of SearchResult objects, sorted by relevance
        """
        query_lower = query.lower()
        query_terms = self._extract_terms(query_lower)
        
        # Extract format/variant from query if present (e.g., "VOR", "Combat")
        detected_formatum = self._detect_formatum_in_query(query)
        
        results = []
        
        effective_formatum_filter = (formatum_filter or detected_formatum)

        for rule in self.rules:
            # Apply filters
            if not self._passes_filters(rule, weapon_filter, effective_formatum_filter):
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
        
        # Sort by score (descending) and keep top results
        results.sort(key=lambda x: x.score, reverse=True)
        top_results = results[:max_results]

        # Expand with hierarchical parent/child rules when appropriate
        expanded_results = self._expand_hierarchy(
            top_results,
            query_lower,
            query_terms,
            weapon_filter,
            effective_formatum_filter
        )

        return expanded_results

    def _passes_filters(self, rule: Dict[str, Any], weapon_filter: str,
                        formatum_filter: str) -> bool:
        """Check if a rule passes weapon/format filters."""
        if weapon_filter and rule.get('weapon_type') != weapon_filter:
            return False

        if formatum_filter:
            rule_formatum = rule.get('formatum', '').upper()
            if rule_formatum != formatum_filter.upper():
                return False

        return True

    def _split_rule_id(self, rule_id: str) -> tuple:
        """Split rule ID into prefix and numeric parts."""
        match = re.match(r'^([A-Z]+(?:-[A-Z]+)*)-(\d+(?:\.\d+)*)$', rule_id)
        if not match:
            return None, None
        prefix = match.group(1)
        numbers = [int(part) for part in match.group(2).split('.')]
        return prefix, numbers

    def _make_rule_id(self, prefix: str, numbers: List[int]) -> str:
        """Reconstruct rule ID from prefix and numeric parts."""
        return f"{prefix}-" + ".".join(str(part) for part in numbers)

    def _expand_hierarchy(self, base_results: List[SearchResult], query_lower: str,
                          query_terms: List[str], weapon_filter: str,
                          formatum_filter: str) -> List[SearchResult]:
        """Include parent/child rules and keep them grouped in order."""
        rule_by_id = {rule['rule_id']: rule for rule in self.rules}
        expanded = []
        seen = set()

        def add_rule(rule: Dict[str, Any], fallback_score: float) -> None:
            if rule['rule_id'] in seen:
                return
            score = self._calculate_score(rule, query_lower, query_terms)
            if score <= 0:
                score = fallback_score
            expanded.append(SearchResult(
                rule_id=rule['rule_id'],
                text=rule['text'],
                section=rule['section'],
                subsection=rule['subsection'],
                document=rule['document'],
                weapon_type=rule.get('weapon_type', ''),
                variant=rule.get('formatum', ''),
                score=score
            ))
            seen.add(rule['rule_id'])

        def iter_children(prefix: str, numbers: List[int], child_level: int) -> List[Dict[str, Any]]:
            children = []
            for rule in self.rules:
                child_prefix, child_numbers = self._split_rule_id(rule['rule_id'])
                if child_prefix != prefix or not child_numbers:
                    continue
                if len(child_numbers) == child_level and child_numbers[:len(numbers)] == numbers:
                    if not self._passes_filters(rule, weapon_filter, formatum_filter):
                        continue
                    children.append(rule)
            children.sort(key=lambda r: self._split_rule_id(r['rule_id'])[1])
            return children

        for result in base_results:
            prefix, numbers = self._split_rule_id(result.rule_id)
            if not prefix or not numbers:
                if result.rule_id not in seen:
                    expanded.append(result)
                    seen.add(result.rule_id)
                continue

            level = len(numbers)

            # Level 3: include parent first, then level 4 children
            if level == 3:
                parent_rule = rule_by_id.get(result.rule_id)
                if parent_rule and self._passes_filters(parent_rule, weapon_filter, formatum_filter):
                    add_rule(parent_rule, result.score)
                for child in iter_children(prefix, numbers, 4):
                    add_rule(child, result.score - 0.1)
                continue

            # Level 4: include parent (level 3), self, then level 5 children
            if level == 4:
                parent_id = self._make_rule_id(prefix, numbers[:3])
                parent_rule = rule_by_id.get(parent_id)
                if parent_rule and self._passes_filters(parent_rule, weapon_filter, formatum_filter):
                    add_rule(parent_rule, result.score)
                current_rule = rule_by_id.get(result.rule_id)
                if current_rule and self._passes_filters(current_rule, weapon_filter, formatum_filter):
                    add_rule(current_rule, result.score)
                for child in iter_children(prefix, numbers, 5):
                    add_rule(child, result.score - 0.1)
                continue

            # Level 5: include parent (level 4), self
            if level == 5:
                parent_id = self._make_rule_id(prefix, numbers[:4])
                parent_rule = rule_by_id.get(parent_id)
                if parent_rule and self._passes_filters(parent_rule, weapon_filter, formatum_filter):
                    add_rule(parent_rule, result.score)
                current_rule = rule_by_id.get(result.rule_id)
                if current_rule and self._passes_filters(current_rule, weapon_filter, formatum_filter):
                    add_rule(current_rule, result.score)
                continue

            # Default: add as-is
            if result.rule_id not in seen:
                expanded.append(result)
                seen.add(result.rule_id)

        return expanded
    
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
