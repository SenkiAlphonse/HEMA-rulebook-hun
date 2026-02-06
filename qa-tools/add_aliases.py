"""
Update existing index with aliases
"""
import json
from pathlib import Path

current_dir = Path(__file__).parent

# Load aliases
with open(current_dir / 'aliases.json', 'r', encoding='utf-8') as f:
    aliases = json.load(f)

# Load current index
with open(current_dir / 'rules_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Add aliases to each rule
for rule in data['rules']:
    weapon_type = rule.get('weapon_type', 'general')
    formatum = rule.get('formatum', '')

    # Add weapon aliases
    weapon_aliases = aliases.get('weapons', {}).get(weapon_type, [])
    rule['weapon_aliases'] = weapon_aliases

    # Add formatum aliases
    # Use 'variants' key from aliases.json (will be renamed to 'formats' later)
    formatum_aliases = aliases.get('variants', {}).get(formatum, []) if formatum else []
    rule['formatum_aliases'] = formatum_aliases# Save updated index
with open(current_dir / 'rules_index.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Updated {len(data["rules"])} rules with aliases')
if data['rules']:
    sample = data['rules'][0]
    print(f'\nSample rule: {sample["rule_id"]}')
    print(f'  Weapon: {sample.get("weapon_type")}')
    print(f'  Weapon aliases: {sample.get("weapon_aliases", [])}')
    print(f'  Formatum: {sample.get("formatum")}')
    print(f'  Formatum aliases: {sample.get("formatum_aliases", [])}')
