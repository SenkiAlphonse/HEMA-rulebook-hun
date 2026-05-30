import json

with open("rules_index.json", encoding="utf-8") as f:
    data = json.load(f)

# Find all GEN-6.10.4 and GEN-6.10.5 variants
variants = [r for r in data["rules"] if r["rule_id"].startswith(("GEN-6.10.4.1.", "GEN-6.10.5."))]

print(f"Found {len(variants)} variant rules:\n")
for rule in variants:
    print(f"Rule ID: {rule['rule_id']}")
    print(f"Variant: '{rule['variant']}'")
    print(f"Text: {rule['text'][:100]}...")
    print()

# Check VOR, COMBAT, AFTERBLOW distribution
vor_rules = [r for r in variants if r["variant"] == "VOR"]
combat_rules = [r for r in variants if r["variant"] == "COMBAT"]
afterblow_rules = [r for r in variants if r["variant"] == "AFTERBLOW"]

print("\nSummary:")
print(f"VOR rules: {len(vor_rules)}")
print(f"COMBAT rules: {len(combat_rules)}")
print(f"AFTERBLOW rules: {len(afterblow_rules)}")
