import json

with open('rules_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

rules = index.get('rules', index) if isinstance(index, dict) else index

# Check first 10 rules
print("First 10 rules:")
for rule in rules[:10]:
    wa = rule.get('weapon_aliases', [])
    fa = rule.get('formatum_aliases', [])
    print(f"  {rule.get('rule_id')}: weapon_aliases={wa}, formatum_aliases={fa}")

# Count total
count_with_weapon_aliases = sum(1 for r in rules if r.get('weapon_aliases'))
count_with_formatum_aliases = sum(1 for r in rules if r.get('formatum_aliases'))

print(f'\nTotal with weapon_aliases: {count_with_weapon_aliases}/{len(rules)}')
print(f'Total with formatum_aliases: {count_with_formatum_aliases}/{len(rules)}')
