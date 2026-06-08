#!/usr/bin/env python3
"""
HU → EN sync report for the HEMA rulebook.

Compares the Hungarian and English rule indexes and produces a structured
report of:
  - Rules present in HU but missing from EN  (need translation)
  - Rules present in EN but not in HU        (orphaned — likely deleted/renumbered)
  - Rules present in both with differing text (need review)

Output is a plain-text report, grouped by source document.
COMBAT is excluded by default (--include-combat to add it).

Usage:
    python tools/sync_report.py
    python tools/sync_report.py --include-combat
    python tools/sync_report.py --missing-only        # skip orphan/changed sections
    python tools/sync_report.py --out report.txt      # write to file
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HUN_INDEX = PROJECT_ROOT / "data" / "search" / "rules_index_hun.json"
ENG_INDEX = PROJECT_ROOT / "data" / "search" / "rules_index_eng.json"

# Map HU document name → EN document name (COMBAT intentionally absent)
DOC_MAP = {
    "01-altalanos.md": "01-general.en.md",
    "02-hosszukard.md": "02-longsword.en.md",
    "02.a-hosszukard-VOR.md": "02.a-longsword-VOR.en.md",
    "02.c-hosszukard-AFTERBLOW.md": "02.c-longsword-AFTERBLOW.en.md",
    "03-etikett_fegyelem.md": "03-etiquette_discipline.en.md",
    "04-szervezes.md": "04-organisation.en.md",
}
COMBAT_HU = "02.b-hosszukard-COMBAT.md"
COMBAT_EN = "02.b-longsword-COMBAT.en.md"


def load_index(path: Path) -> dict[str, dict]:
    """Load a rules index and return a dict of rule_id -> rule."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Keep first occurrence when duplicates exist
    seen: dict[str, dict] = {}
    for rule in data["rules"]:
        rid = rule["rule_id"]
        if rid not in seen:
            seen[rid] = rule
    return seen


def text_changed(hun_rule: dict, eng_rule: dict) -> bool:
    """Heuristic: flag if text length differs by more than 20% (structural change)."""
    ht = len(hun_rule.get("text", ""))
    et = len(eng_rule.get("text", ""))
    if ht == 0 and et == 0:
        return False
    ratio = abs(ht - et) / max(ht, et)
    return ratio > 0.20


def run_report(include_combat: bool, missing_only: bool, out_file) -> int:
    hun = load_index(HUN_INDEX)
    eng = load_index(ENG_INDEX)

    doc_pairs = list(DOC_MAP.items())
    if include_combat:
        doc_pairs.append((COMBAT_HU, COMBAT_EN))

    # Build per-document buckets
    missing: dict[str, list[str]] = {}  # rule_id in HU, absent from EN
    orphaned: dict[str, list[str]] = {}  # rule_id in EN, absent from HU
    changed: dict[str, list[str]] = {}  # rule_id in both, text likely changed

    for hu_doc, en_doc in doc_pairs:
        hun_in_doc = [r for r in hun.values() if r["document"] == hu_doc]
        eng_in_doc = [r for r in eng.values() if r["document"] == en_doc]
        hun_doc_ids = {r["rule_id"] for r in hun_in_doc}
        eng_doc_ids = {r["rule_id"] for r in eng_in_doc}

        miss = sorted(hun_doc_ids - eng_doc_ids)
        orph = sorted(eng_doc_ids - hun_doc_ids)
        chng = sorted(rid for rid in hun_doc_ids & eng_doc_ids if text_changed(hun[rid], eng[rid]))

        if miss:
            missing[hu_doc] = miss
        if orph:
            orphaned[en_doc] = orph
        if chng:
            changed[hu_doc] = chng

    # Write report
    w = out_file.write

    SEP = "=" * 72 + "\n"
    DIV = "-" * 72 + "\n"
    w(SEP)
    w("HU -> EN SYNC REPORT\n")
    w(SEP + "\n")

    # Summary
    total_missing = sum(len(v) for v in missing.values())
    total_orphaned = sum(len(v) for v in orphaned.values())
    total_changed = sum(len(v) for v in changed.values())
    w(f"Rules missing from EN (need translation): {total_missing}\n")
    w(f"Rules orphaned in EN (deleted from HU):   {total_orphaned}\n")
    w(f"Rules with likely text changes:           {total_changed}\n")
    if not include_combat:
        w("(COMBAT excluded -- run with --include-combat to include)\n")
    w("\n")

    # Section 1: Missing
    w(DIV)
    w("SECTION 1: MISSING FROM EN (translate these)\n")
    w(DIV + "\n")
    if not missing:
        w("  [OK] No missing rules.\n\n")
    else:
        for hu_doc, ids in sorted(missing.items()):
            en_doc = DOC_MAP.get(hu_doc, COMBAT_EN)
            w(f"[{hu_doc}] -> [{en_doc}]\n")
            for rid in ids:
                rule = hun[rid]
                snippet = rule.get("text", "")[:120].replace("\n", " ")
                w(f"  {rid:30s}  {snippet}\n")
            w("\n")

    if missing_only:
        return total_missing

    # Section 2: Orphaned
    w(DIV)
    w("SECTION 2: ORPHANED IN EN (no HU counterpart -- review/delete)\n")
    w(DIV + "\n")
    if not orphaned:
        w("  [OK] No orphaned rules.\n\n")
    else:
        for en_doc, ids in sorted(orphaned.items()):
            w(f"[{en_doc}]\n")
            for rid in ids:
                rule = eng[rid]
                snippet = rule.get("text", "")[:120].replace("\n", " ")
                w(f"  {rid:30s}  {snippet}\n")
            w("\n")

    # Section 3: Changed
    w(DIV)
    w("SECTION 3: LIKELY CHANGED (text length differs >20% -- review)\n")
    w(DIV + "\n")
    if not changed:
        w("  [OK] No significant changes detected.\n\n")
    else:
        for hu_doc, ids in sorted(changed.items()):
            w(f"[{hu_doc}]\n")
            for rid in ids:
                hu_len = len(hun[rid].get("text", ""))
                en_len = len(eng.get(rid, {}).get("text", ""))
                w(f"  {rid:30s}  HU={hu_len}ch  EN={en_len}ch\n")
            w("\n")

    return total_missing


def main() -> None:
    parser = argparse.ArgumentParser(description="HU->EN sync report")
    parser.add_argument(
        "--include-combat", action="store_true", help="Include COMBAT chapter in the report"
    )
    parser.add_argument(
        "--missing-only", action="store_true", help="Only show rules missing from EN"
    )
    parser.add_argument("--out", metavar="FILE", help="Write report to file instead of stdout")
    args = parser.parse_args()

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            run_report(args.include_combat, args.missing_only, f)
        print(f"Report written to {args.out}")
    else:
        # Ensure stdout can handle Hungarian characters on Windows
        stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        run_report(args.include_combat, args.missing_only, stdout)
        stdout.flush()


if __name__ == "__main__":
    main()
