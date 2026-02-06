#!/usr/bin/env python
"""
Quick setup and test script for the HEMA Rulebook Search app
Run this to verify everything is set up correctly
"""

import os
import json
import sys
from pathlib import Path

def check_files():
    """Check if all required files exist"""
    print("=" * 60)
    print("Checking required files...")
    print("=" * 60)
    
    required_files = {
        "app.py": "Flask application",
        "templates/index.html": "Web interface",
        "qa-tools/parser.py": "Rule parser",
        "qa-tools/search_aliases.py": "Search engine",
        "qa-tools/rules_index.json": "Rule index",
        "qa-tools/aliases.json": "Search aliases",
        "requirements.txt": "Dependencies",
        "render.yaml": "Render config",
    }
    
    all_exist = True
    for filepath, description in required_files.items():
        path = Path(filepath)
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {filepath:<35} ({description})")
        if not exists:
            all_exist = False
    
    return all_exist

def check_index():
    """Check rule index"""
    print("\n" + "=" * 60)
    print("Checking rule index...")
    print("=" * 60)
    
    try:
        with open("qa-tools/rules_index.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        rules = data.get("rules", data) if isinstance(data, dict) else data
        print(f"✓ Rules indexed: {len(rules)}")
        
        # Count by weapon and format
        weapons = {}
        formats = {}
        for rule in rules:
            w = rule.get("weapon_type", "unknown")
            f = rule.get("formatum", "general")
            weapons[w] = weapons.get(w, 0) + 1
            formats[f] = formats.get(f, 0) + 1
        
        print(f"\nBy weapon type:")
        for w in sorted(weapons.keys()):
            print(f"  - {w}: {weapons[w]} rules")
        
        print(f"\nBy format:")
        for f in sorted(formats.keys()) or ["general"]:
            print(f"  - {f or 'general'}: {formats[f]} rules")
        
        return True
    except Exception as e:
        print(f"✗ Error loading index: {e}")
        return False

def check_aliases():
    """Check aliases configuration"""
    print("\n" + "=" * 60)
    print("Checking aliases...")
    print("=" * 60)
    
    try:
        with open("qa-tools/aliases.json", "r", encoding="utf-8") as f:
            aliases = json.load(f)
        
        if "variants" in aliases:
            print(f"✓ Format aliases:")
            for fmt, terms in aliases["variants"].items():
                print(f"  - {fmt}: {len(terms)} aliases")
        
        if "weapons" in aliases:
            print(f"\n✓ Weapon aliases:")
            for weapon, terms in aliases["weapons"].items():
                print(f"  - {weapon}: {len(terms)} aliases")
        
        if "concepts" in aliases:
            print(f"\n✓ Concept aliases:")
            for concept, terms in aliases["concepts"].items():
                print(f"  - {concept}: {len(terms)} aliases")
        
        return True
    except Exception as e:
        print(f"✗ Error loading aliases: {e}")
        return False

def test_search():
    """Test the search engine"""
    print("\n" + "=" * 60)
    print("Testing search engine...")
    print("=" * 60)
    
    try:
        # Add qa-tools to path
        sys.path.insert(0, str(Path("qa-tools").absolute()))
        from search_aliases import AliasAwareSearch
        
        search = AliasAwareSearch("qa-tools/rules_index.json", "qa-tools/aliases.json")
        
        test_queries = [
            ("longsword strike", None, None),
            ("right of way", "VOR", None),
            ("target", None, "longsword"),
        ]
        
        for query, fmt, weapon in test_queries:
            results = search.search(query, max_results=3, formatum_filter=fmt, weapon_filter=weapon)
            fmt_label = f" [format={fmt}]" if fmt else ""
            weapon_label = f" [weapon={weapon}]" if weapon else ""
            print(f"\n✓ Query: '{query}'{fmt_label}{weapon_label}")
            if results:
                print(f"  Found {len(results)} results:")
                for r in results[:2]:
                    print(f"    - {r.rule_id} (score={r.score:.1f})")
            else:
                print(f"  No results")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     HEMA Rulebook Search - Setup Verification              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    checks = [
        ("Files", check_files),
        ("Index", check_index),
        ("Aliases", check_aliases),
        ("Search", test_search),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} check failed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ All checks passed! The app is ready to deploy.")
        print("\nTo run locally:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run the app: python app.py")
        print("  3. Visit: http://localhost:5000")
        print("\nTo deploy to Render:")
        print("  1. Push to GitHub")
        print("  2. Go to render.com and connect your repo")
        print("  3. Render will auto-detect and deploy")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        sys.exit(1)
    
    print()

if __name__ == "__main__":
    main()
