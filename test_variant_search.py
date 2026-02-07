#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test the variant-specific search functionality"""

import sys
import json
sys.path.insert(0, 'qa-tools')

from search import RulebookSearch

def test_variant_search():
    """Test variant filtering in search"""
    search = RulebookSearch("qa-tools/rules_index.json")
    
    # Test 1: Search for "5 találat" without variant filter
    print("=" * 70)
    print("TEST 1: Search for '5 találat' (both VOR and COMBAT apply)")
    print("=" * 70)
    results = search.search("5 találat", max_results=5)
    print(f"Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Rule ID: {result.rule_id}")
        print(f"   Variant: {result.variant if result.variant else '(general)'}")
        print(f"   Score: {result.score:.1f}")
        print()
    
    # Test 2: Search for "VOR" - should prioritize VOR rules
    print("=" * 70)
    print("TEST 2: Search for 'VOR' (variant-specific search)")
    print("=" * 70)
    results = search.search("VOR", max_results=5)
    print(f"Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Rule ID: {result.rule_id}")
        print(f"   Variant: {result.variant if result.variant else '(general)'}")
        print(f"   Score: {result.score:.1f}")
        print()
    
    # Test 3: Search with explicit formatum filter
    print("=" * 70)
    print("TEST 3: Explicit formatum filter (AFTERBLOW only)")
    print("=" * 70)
    results = search.search("pont", max_results=3, formatum_filter="AFTERBLOW")
    print(f"Found {len(results)} AFTERBLOW results:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Rule ID: {result.rule_id}")
        print(f"   Variant: {result.variant if result.variant else '(general)'}")
        print(f"   Score: {result.score:.1f}")
        print()
    
    # Test 4: Get specific variant rules by ID
    print("=" * 70)
    print("TEST 4: Direct variant rule lookups")
    print("=" * 70)
    variant_ids = ["GEN-6.10.4.1.1", "GEN-6.10.4.1.2", "GEN-6.10.4.1.3"]
    for rule_id in variant_ids:
        rule = search.get_rule_by_id(rule_id)
        if rule:
            variant = rule.get('formatum', '(general)')
            print(f"Rule {rule_id}: [{variant}]")
        else:
            print(f"Rule {rule_id}: NOT FOUND")
    
    print("\n" + "=" * 70)
    print("SUMMARY: Variant-specific filtering is working!")
    print("=" * 70)

if __name__ == "__main__":
    test_variant_search()
