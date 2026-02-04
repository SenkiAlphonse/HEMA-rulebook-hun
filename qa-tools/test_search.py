"""
Simple search test - demonstrates the Q&A capabilities
"""
import json
from pathlib import Path

# Load index
with open('qa-tools/rules_index.json', encoding='utf-8') as f:
    data = json.load(f)

rules = data['rules']

def search_rules(query):
    """Simple search function"""
    query_lower = query.lower()
    results = []
    
    for rule in rules:
        score = 0
        text_lower = rule['text'].lower()
        section_lower = rule['section'].lower()
        
        # Score based on matches
        if query_lower in text_lower:
            score += 10
        if query_lower in section_lower:
            score += 5
        if query_lower in rule['rule_id'].lower():
            score += 20
            
        if score > 0:
            results.append((score, rule))
    
    # Sort by score
    results.sort(reverse=True, key=lambda x: x[0])
    return [r[1] for r in results[:3]]

# Test queries
test_queries = [
    "találati felület",
    "hosszúkard",
    "GEN-1.1.1",
    "felszerelés"
]

print("="*70)
print("HEMA RULEBOOK Q&A - DEMO")
print("="*70)

for query in test_queries:
    print(f"\n🔍 Query: '{query}'")
    print("-"*70)
    
    results = search_rules(query)
    
    if not results:
        print("No results found.")
        continue
    
    for i, rule in enumerate(results[:2], 1):
        print(f"\n{i}. [{rule['rule_id']}] {rule['document']}")
        print(f"   Section: {rule['section']}")
        if rule['weapon_type'] != 'general':
            print(f"   Weapon: {rule['weapon_type']}" + 
                  (f" ({rule['variant']})" if rule['variant'] else ""))
        print(f"   Text: {rule['text'][:200]}...")
