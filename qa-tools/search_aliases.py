"""
Enhanced HEMA Rulebook Search Engine with Alias Support
"""

import json
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Tuple
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
    formatum: str
    score: float


class AliasAwareSearch:
    """Search engine with alias support for HEMA rulebook"""

    def __init__(self, index_path: str, aliases_path: str = None):
        self.index_path = Path(index_path)
        self.rules = []
        self.aliases = {}
        self.alias_to_key = {}  # Reverse lookup: alias -> (category, key)

        if aliases_path is None:
            aliases_path = self.index_path.parent / "aliases.json"

        self.load_aliases(aliases_path)
        self.load_index()
        self._build_alias_lookup()

    def load_aliases(self, aliases_path: str):
        """Load aliases from JSON"""
        try:
            with open(aliases_path, 'r', encoding='utf-8') as f:
                self.aliases = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Aliases file not found at {aliases_path}")
            self.aliases = {"variants": {}, "weapons": {}, "concepts": {}}

    def _build_alias_lookup(self):
        """Build reverse lookup from alias to its category and key"""
        # Map format aliases
        for key, aliases in self.aliases.get('variants', {}).items():
            for alias in aliases:
                self.alias_to_key[alias.lower()] = ('formatum', key)
        
        # Map weapon aliases
        for key, aliases in self.aliases.get('weapons', {}).items():
            for alias in aliases:
                self.alias_to_key[alias.lower()] = ('weapon', key)
        
        # Map concept aliases - store all aliases in concept group
        for concept_key, aliases in self.aliases.get('concepts', {}).items():
            for alias in aliases:
                self.alias_to_key[alias.lower()] = ('concept', concept_key)

    def load_index(self):
        """Load the rules index"""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index not found: {self.index_path}")
        
        with open(self.index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.rules = data['rules']
        
        print(f"Loaded {len(self.rules)} rules with alias support")

    def _expand_query(self, query: str) -> Tuple[str, str, str, List[str], str]:
        """
        Expand query based on aliases
        
        Returns: (expanded_query, formatum_filter, weapon_filter, concept_terms)
        """
        query_lower = query.lower()
        formatum_filter = None
        weapon_filter = None
        concept_terms = []
        remaining_terms = []
        
        # Split query into words
        words = re.findall(r'\w+', query_lower)
        
        for word in words:
            if word in self.alias_to_key:
                category, key = self.alias_to_key[word]
                
                if category == 'formatum':
                    formatum_filter = key
                elif category == 'weapon':
                    weapon_filter = key
                elif category == 'concept':
                    # Add all aliases from this concept to search terms
                    concept_terms.extend(self.aliases['concepts'][key])
            else:
                remaining_terms.append(word)
        
        # Build expanded query
        base_query = ' '.join(remaining_terms)
        expanded_query = base_query
        if concept_terms:
            # Add concept terms to search
            expanded_query = expanded_query + ' ' + ' '.join(concept_terms)
        
        return expanded_query.strip(), formatum_filter, weapon_filter, concept_terms, base_query.strip()

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()

    def search(self, query: str, max_results: int = 5,
               formatum_filter: str = None, weapon_filter: str = None) -> List[SearchResult]:
        """
        Search with alias awareness and query expansion

        Args:
            query: Search query
            max_results: Max results to return
            formatum_filter: Filter by format (VOR, COMBAT, AFTERBLOW) - can be overridden by query
            weapon_filter: Filter by weapon (longsword, rapier, etc.) - can be overridden by query
        """
        # Expand query based on aliases
        expanded_query, detected_formatum, detected_weapon, concept_terms, base_query = self._expand_query(query)
        
        # Use detected filters if not explicitly provided
        if not formatum_filter and detected_formatum:
            formatum_filter = detected_formatum
        if not weapon_filter and detected_weapon:
            weapon_filter = detected_weapon
        
        query_lower = expanded_query.lower() if expanded_query else query.lower()
        query_norm = self._normalize_text(query_lower)
        query_terms = self._extract_terms(query_norm)
        required_terms = self._extract_terms(self._normalize_text(base_query)) if base_query else []

        results = []
        
        for rule in self.rules:
            # Apply filters with hierarchy:
            # - General rules (weapon_type='general') apply to everything
            # - Weapon-general rules (no formatum) apply to all formats of that weapon
            # - Format-specific rules apply only to that format
            
            rule_weapon = rule.get('weapon_type', 'general')
            rule_formatum = rule.get('formatum', '')
            
            # If weapon filter is specified
            if weapon_filter:
                # Exclude if rule is for different weapon (unless rule is general)
                if rule_weapon != 'general' and rule_weapon != weapon_filter:
                    continue
            
            # If formatum filter is specified
            if formatum_filter:
                # Include if: rule is general, OR rule is weapon-general, OR rule matches the format
                if rule_weapon != 'general' and rule_formatum and rule_formatum != formatum_filter:
                    continue

            # Require all base query terms to appear somewhere
            if required_terms:
                combined_text = " ".join([
                    rule.get('text', ''),
                    rule.get('section', ''),
                    rule.get('subsection', '')
                ])
                combined_norm = self._normalize_text(combined_text)
                if any(term not in combined_norm for term in required_terms):
                    continue

            # Calculate score including aliases
            score = self._calculate_score_with_aliases(rule, query_lower, query_norm, query_terms, concept_terms)

            if score > 0:
                results.append(SearchResult(
                    rule_id=rule['rule_id'],
                    text=rule['text'],
                    section=rule.get('section', ''),
                    subsection=rule.get('subsection', ''),
                    document=rule.get('document', ''),
                    weapon_type=rule.get('weapon_type', ''),
                    formatum=rule.get('formatum', ''),
                    score=score
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:max_results]
    
    def _extract_terms(self, query: str) -> List[str]:
        """Extract search terms"""
        stop_words = {'a', 'az', 'és', 'vagy', 'de', 'ha', 'hogy', 'mi', 'van', 'volt',
                     'the', 'a', 'an', 'and', 'or', 'but', 'if', 'is'}
        terms = re.findall(r'\w+', query)
        return [t for t in terms if t not in stop_words and len(t) > 2]
    
    def _calculate_score_with_aliases(self, rule: Dict[str, Any],
                                      query: str, query_norm: str, terms: List[str],
                                      concept_terms: List[str] = None) -> float:
        """Calculate score including alias matches"""
        score = 0.0

        text_lower = rule['text'].lower()
        section_lower = rule.get('section', '').lower()
        subsection_lower = rule.get('subsection', '').lower()
        rule_id_lower = rule['rule_id'].lower()

        text_norm = self._normalize_text(text_lower)
        section_norm = self._normalize_text(section_lower)
        subsection_norm = self._normalize_text(subsection_lower)

        # Direct rule ID match (highest priority)
        if rule_id_lower in query:
            score += 100.0

        # Exact phrase in text
        if query_norm and query_norm in text_norm:
            score += 50.0

        # Exact phrase in section
        if query_norm and (query_norm in section_norm or query_norm in subsection_norm):
            score += 30.0

        # Term frequency in text
        for term in terms:
            count_in_text = text_norm.count(term)
            score += count_in_text * 10.0

            if term in section_norm or term in subsection_norm:
                score += 5.0

        # Check concept terms (from alias expansion)
        if concept_terms:
            for concept_term in concept_terms:
                if self._normalize_text(concept_term) in text_norm:
                    score += 15.0

        # Check formatum aliases (legacy scoring for non-expanded queries)
        if rule.get('formatum'):
            for alias in rule.get('formatum_aliases', []):
                if alias in query:
                    score += 40.0

        # Check weapon aliases (legacy scoring for non-expanded queries)
        for alias in rule.get('weapon_aliases', []):
            if alias in query:
                score += 20.0

        # Apply length penalty for very long rules (e.g., large tables)
        # Rules >2000 chars get progressively lower scores to push them down rankings
        text_length = len(rule['text'])
        if text_length > 2000:
            # Exponential penalty: 2000 chars = 1.5x, 4000 = 3x, 8000 = 9x
            length_penalty = (text_length / 2000.0) ** 1.5
            score = score / length_penalty

        return score
    def get_rule_by_id(self, rule_id: str) -> dict:
        """Get a rule by its ID"""
        for rule in self.rules:
            if rule.get('rule_id') == rule_id:
                return rule
        return None


def format_result(result: SearchResult) -> str:
    """Format a result for display"""
    output = []
    output.append(f"\n{'='*70}")
    output.append(f"Rule ID: {result.rule_id}")
    output.append(f"Document: {result.document}")
    
    if result.weapon_type and result.weapon_type != 'general':
        output.append(f"Weapon: {result.weapon_type}")
        if result.formatum:
            output.append(f"Format: {result.formatum}")
    elif result.formatum:
        output.append(f"Format: {result.formatum}")
    
    output.append(f"\nSection: {result.section}")
    if result.subsection:
        output.append(f"Subsection: {result.subsection}")
    
    output.append(f"\n{result.text[:300]}...")
    output.append(f"\n[Score: {result.score:.1f}]")
    
    return "\n".join(output)


def main():
    """Interactive search CLI"""
    current_dir = Path(__file__).parent
    index_path = current_dir / "rules_index.json"
    aliases_path = current_dir / "aliases.json"
    
    if not index_path.exists():
        print("Error: Index not found. Run parser.py first.")
        return
    
    search = AliasAwareSearch(str(index_path), str(aliases_path))
    
    print("\n" + "="*70)
    print("HEMA Rulebook Search - Alias-Aware")
    print("="*70)
    print("\nExample queries:")
    print("  - 'right of way' (will find VOR rules)")
    print("  - 'longsword target area'")
    print("  - 'combat priority'")
    print("  - 'rapier equipment'")
    print("  - 'penalty illegal'")
    print("\nFilters:")
    print("  - search VOR <query>")
    print("  - search longsword <query>")
    print("  - quit to exit")
    print("-"*70)
    
    while True:
        try:
            cmd = input("\nQuery: ").strip()
            
            if not cmd or cmd.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            parts = cmd.split(maxsplit=1)
            formatum_filter = None
            weapon_filter = None
            query = cmd
            
            # Check for filters
            if parts[0].upper() in ['VOR', 'COMBAT', 'AFTERBLOW']:
                formatum_filter = parts[0].upper()
                query = parts[1] if len(parts) > 1 else ""
            elif parts[0].lower() in ['longsword', 'rapier', 'padded']:
                weapon_filter = parts[0].lower() if parts[0].lower() != 'padded' else 'padded_weapons'
                query = parts[1] if len(parts) > 1 else ""
            
            if not query:
                print("Please enter a query.")
                continue
            
            results = search.search(query, max_results=5, 
                                   formatum_filter=formatum_filter,
                                   weapon_filter=weapon_filter)
            
            if not results:
                print("\nNo results found. Try different keywords or aliases.")
                continue
            
            print(f"\nFound {len(results)} results:")
            for result in results:
                print(format_result(result))
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
