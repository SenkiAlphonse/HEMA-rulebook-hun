"""
Enhanced HEMA Rulebook Search with Variant Awareness
Handles mutually exclusive longsword variants intelligently
"""
import json
from pathlib import Path

class VariantAwareSearch:
    """Search engine that understands mutually exclusive variants"""
    
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
    
    def search_for_competition(self, query: str, competition_variant: str = None, 
                               max_results: int = 5):
        """
        Search rules for a specific competition format
        
        Args:
            query: Search query
            competition_variant: Which variant this competition uses ("VOR", "COMBAT", "AFTERBLOW")
                                 If None, returns all variants
            max_results: Maximum results to return
        
        Returns:
            List of matching rules
        """
        query_lower = query.lower()
        query_terms = self._extract_terms(query_lower)
        
        results = []
        
        for rule in self.rules:
            # Filter by competition variant if specified
            if competition_variant:
                # Always include general rules (no variant)
                if rule.get('variant') and rule.get('variant') != competition_variant:
                    continue
            
            # Calculate relevance score
            score = self._calculate_score(rule, query_lower, query_terms)
            
            if score > 0:
                results.append({
                    'score': score,
                    'rule': rule,
                    'is_general': not rule.get('variant'),
                    'is_variant': bool(rule.get('variant'))
                })
        
        # Sort: specific variant rules first, then general rules
        # Both sorted by relevance score
        results.sort(key=lambda x: (-x['is_variant'], -x['score']))
        return [r['rule'] for r in results[:max_results]]
    
    def get_variant_rules(self, variant: str) -> dict:
        """
        Get all rules for a specific variant
        Useful for competitor preparation or rule comparison
        
        Args:
            variant: "VOR", "COMBAT", or "AFTERBLOW"
        
        Returns:
            Dict with general rules + variant-specific rules
        """
        general = [r for r in self.rules if not r.get('variant')]
        variant_specific = [r for r in self.rules 
                           if r.get('variant') == variant]
        
        return {
            'variant': variant,
            'general_rules': general,
            'variant_specific_rules': variant_specific,
            'total': len(general) + len(variant_specific)
        }
    
    def compare_variants(self, query: str) -> dict:
        """
        Compare how a rule differs across variants
        
        Args:
            query: Search query
        
        Returns:
            Dict showing rule variations
        """
        query_lower = query.lower()
        variants = ['VOR', 'COMBAT', 'AFTERBLOW']
        
        comparison = {
            'query': query,
            'general': [],
            'variants': {}
        }
        
        # Get general rules matching query
        comparison['general'] = self.search_for_competition(query, None, max_results=10)
        
        # Get variant-specific rules for each variant
        for variant in variants:
            comparison['variants'][variant] = self.search_for_competition(
                query, variant, max_results=5
            )
        
        return comparison
    
    def _extract_terms(self, query: str):
        """Extract search terms from query"""
        import re
        stop_words = {'a', 'az', 'és', 'vagy', 'de', 'ha', 'hogy', 'mi', 'van', 'volt', 
                     'the', 'a', 'an', 'and', 'or', 'but', 'if', 'is'}
        terms = re.findall(r'\w+', query)
        return [t for t in terms if t not in stop_words and len(t) > 2]
    
    def _calculate_score(self, rule: dict, query: str, terms: list) -> float:
        """Calculate relevance score"""
        score = 0.0
        
        text_lower = rule['text'].lower()
        section_lower = rule['section'].lower()
        rule_id_lower = rule['rule_id'].lower()
        
        # Exact rule ID match (highest priority)
        if rule_id_lower in query:
            score += 100.0
        
        # Exact phrase match in text
        if query in text_lower:
            score += 50.0
        
        # Term frequency
        for term in terms:
            score += text_lower.count(term) * 10.0
            if term in section_lower:
                score += 5.0
        
        return score


def format_competition_results(results: list, variant: str = None) -> str:
    """Format search results for competition use"""
    output = []
    output.append(f"\n{'='*70}")
    if variant:
        output.append(f"Rules for {variant} competition")
    else:
        output.append(f"All matching rules")
    output.append(f"{'='*70}\n")
    
    for i, rule in enumerate(results[:3], 1):
        prefix = "⚔" if rule.get('variant') else "📖"
        output.append(f"{i}. {prefix} [{rule['rule_id']}] {rule['document']}")
        output.append(f"   {rule['section']}")
        if rule.get('variant'):
            output.append(f"   Variant: {rule['variant']}")
        output.append(f"\n   {rule['text'][:200]}...\n")
    
    return "\n".join(output)


def main():
    """Interactive demo"""
    import sys
    
    current_dir = Path(__file__).parent
    index_path = current_dir / "rules_index.json"
    
    if not index_path.exists():
        print("Index not found. Run parser.py first.")
        return
    
    search = VariantAwareSearch(str(index_path))
    
    print("\n" + "="*70)
    print("HEMA Longsword Q&A - Variant-Aware Search")
    print("="*70)
    print("\nCommands:")
    print("  search <query>              - Search all rules")
    print("  search VOR <query>          - Search for VOR competition")
    print("  search COMBAT <query>       - Search for COMBAT competition")
    print("  search AFTERBLOW <query>    - Search for AFTERBLOW competition")
    print("  compare <query>             - Compare rule across variants")
    print("  variant VOR                 - Show all VOR rules")
    print("  quit                        - Exit")
    print("-"*70)
    
    while True:
        try:
            cmd = input("\nCommand: ").strip().split(maxsplit=1)
            
            if not cmd or cmd[0].lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if cmd[0].lower() == 'search':
                if len(cmd) > 1:
                    parts = cmd[1].split(maxsplit=1)
                    if parts[0] in ['VOR', 'COMBAT', 'AFTERBLOW']:
                        variant = parts[0]
                        query = parts[1] if len(parts) > 1 else ""
                        print(f"\nSearching for: '{query}' in {variant}")
                        results = search.search_for_competition(query, variant)
                        print(format_competition_results(results, variant))
                    else:
                        query = cmd[1]
                        print(f"\nSearching for: '{query}' (all variants)")
                        results = search.search_for_competition(query, None)
                        print(format_competition_results(results))
            
            elif cmd[0].lower() == 'compare':
                if len(cmd) > 1:
                    query = cmd[1]
                    print(f"\nComparing: '{query}' across variants")
                    comp = search.compare_variants(query)
                    
                    print(f"\n{'='*70}")
                    print(f"General Rules (apply to all variants):")
                    print(f"{'='*70}")
                    for rule in comp['general'][:2]:
                        print(f"\n[{rule['rule_id']}] {rule['text'][:150]}...")
                    
                    for variant, rules in comp['variants'].items():
                        if rules:
                            print(f"\n{variant}-specific rules:")
                            for rule in rules[:1]:
                                print(f"[{rule['rule_id']}] {rule['text'][:150]}...")
            
            elif cmd[0].lower() == 'variant':
                if len(cmd) > 1:
                    variant = cmd[1].upper()
                    if variant in ['VOR', 'COMBAT', 'AFTERBLOW']:
                        info = search.get_variant_rules(variant)
                        print(f"\n{'='*70}")
                        print(f"{variant} Competition Rules")
                        print(f"{'='*70}")
                        print(f"General rules: {len(info['general_rules'])}")
                        print(f"Variant-specific rules: {len(info['variant_specific_rules'])}")
                        print(f"Total: {info['total']}")
                        
                        print(f"\nVariant-specific rules:")
                        for rule in info['variant_specific_rules'][:5]:
                            print(f"  - [{rule['rule_id']}] {rule['section']}")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
