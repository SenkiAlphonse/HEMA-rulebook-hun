#!/usr/bin/env python3
"""Test script to verify hierarchy metadata"""

import json

with open('rules_index.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    rules = data['rules']

# Find and display sample rules
print("=" * 80)
print("HIERARCHY METADATA TEST")
print("=" * 80)

samples = ['GEN-3.2.1.1', 'GEN-3.2.1', 'GEN-3.2', 'GEN-3', 'GEN']
for rule_id in samples:
    found = None
    for r in rules:
        if r['rule_id'] == rule_id:
            found = r
            break

    if found:
        print(f"\nRule: {found['rule_id']}")
        print(f"  Depth: {found.get('depth')}")
        print(f"  Parent: {found.get('parent_id')}")
        print(f"  Lineage: {found.get('lineage')}")
        print(f"  Is Leaf: {found.get('is_leaf')}")
        print(f"  Children: {found.get('child_ids')[:3] if found.get('child_ids') else []}...")
        print(f"  Siblings: {found.get('sibling_ids')[:3] if found.get('sibling_ids') else []}...")
    else:
        print(f"\nRule {rule_id}: NOT FOUND")

print("\n" + "=" * 80)
print("Summary Statistics")
print("=" * 80)
depths = {}
for r in rules:
    d = r.get('depth', 0)
    depths[d] = depths.get(d, 0) + 1

for depth in sorted(depths.keys()):
    print(f"Depth {depth}: {depths[depth]} rules")

leaves = sum(1 for r in rules if r.get('is_leaf'))
non_leaves = len(rules) - leaves
print(f"\nLeaf rules: {leaves}")
print(f"Parent rules (non-leaf): {non_leaves}")
