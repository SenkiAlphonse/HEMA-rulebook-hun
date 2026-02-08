"""View sample rules from the index"""
import json

with open('qa-tools/rules_index.json', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total rules extracted: {data['total_rules']}")
print(f"Documents processed: {', '.join(data['documents'])}\n")

print("="*70)
print("SAMPLE RULES")
print("="*70)

for i, rule in enumerate(data['rules'][:5], 1):
    print(f"\n{i}. Rule ID: {rule['rule_id']}")
    print(f"   Document: {rule['document']}")
    print(f"   Section: {rule['section']}")
    if rule['weapon_type']:
        print(f"   Weapon: {rule['weapon_type']}" + 
              (f" ({rule['formatum']})" if rule['formatum'] else ""))
    print(f"   Text: {rule['text'][:150]}...")
    print("-"*70)
