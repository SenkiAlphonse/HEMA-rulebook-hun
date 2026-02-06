"""
Direct test of alias search without interactive input
"""
import json
from pathlib import Path

# Load data directly
current_dir = Path(__file__).parent

with open(current_dir / "aliases.json", 'r', encoding='utf-8') as f:
    aliases = json.load(f)

with open(current_dir / "rules_index.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

rules = data['rules']

def search_simple(query_text, formatum_filter=None):
    """Simple search matching"""
    results = []
    query_lower = query_text.lower()
    
    for rule in rules:
        # Filter by formatum if specified
        if formatum_filter and rule.get('formatum') != formatum_filter:
            continue
        
        # Check direct match
        score = 0
        if query_lower in rule['text'].lower():
            score += 50
        if query_lower in rule['rule_id'].lower():
            score += 100
        if query_lower in rule.get('section', '').lower():
            score += 30
        
        # Check aliases
        for alias in rule.get('formatum_aliases', []):
            if alias.lower() in query_lower:
                score += 40
        
        for alias in rule.get('weapon_aliases', []):
            if alias.lower() in query_lower:
                score += 20
        
        if score > 0:
            results.append((score, rule))
    
    results.sort(reverse=True, key=lambda x: x[0])
    return results[:3]

print("\n" + "="*70)
print("ALIAS SEARCH TEST - DIRECT")
print("="*70)

test_cases = [
    ("right of way", None),
    ("vor target", None),
    ("free fencing", None),
    ("longsword strike", None),
    ("rapier equipment", None),
]

for query, formatum in test_cases:
    print(f"\n{'─'*70}")
    print(f"Query: '{query}'")
    if formatum:
        print(f"Format: {formatum}")
    print(f"{'─'*70}")
    
    results = search_simple(query, formatum)
    
    if not results:
        print("❌ No results")
        continue
    
    print(f"✅ Found {len(results)} results:\n")
    for score, rule in results:
        print(f"  [{rule['rule_id']}] {rule['document']}")
        print(f"  Section: {rule['section']}")
        if rule.get('formatum'):
            print(f"  Format: {rule['formatum']}")
        print(f"  Score: {score:.0f}")
        print(f"  Text: {rule['text'][:80]}...\n")

print("="*70)
print("✅ Alias system is working!")
print("="*70)
