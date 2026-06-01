"""
Rule integrity checker for the HEMA rulebook indexes.

Checks for:
  - Duplicate rule IDs within the same index
  - Broken cross-references (references_to pointing to non-existent rule IDs)

Exit codes:
  0  — all checked indexes are clean
  1  — at least one ERROR-level issue found (HUN by default)

Usage:
  python tools/check_integrity.py           # check both, fail on HUN errors
  python tools/check_integrity.py --lang hun
  python tools/check_integrity.py --lang eng
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATHS = {
    "hun": PROJECT_ROOT / "data" / "search" / "rules_index_hun.json",
    "eng": PROJECT_ROOT / "data" / "search" / "rules_index_eng.json",
}

# Languages that cause a non-zero exit on failure.
# ENG is warn-only until it is synced with the HUN source.
FAIL_LANGS = {"hun"}
WARN_LANGS = {"eng"}


def check_index(lang: str, path: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for a single index file."""
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        errors.append(f"Index file not found: {path}")
        return errors, warnings

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    rules = data.get("rules", [])
    ids = [r["rule_id"] for r in rules]
    valid_ids = set(ids)

    # Duplicate IDs
    for rule_id, count in sorted(Counter(ids).items()):
        if count > 1:
            errors.append(f"Duplicate rule ID: {rule_id} (appears {count}x)")

    # Broken cross-references
    for rule in rules:
        for ref in rule.get("references_to", []):
            if ref not in valid_ids:
                errors.append(
                    f"Broken reference: [{rule['rule_id']}] in {rule['document']}"
                    f" -> [{ref}] (not found)"
                )

    return errors, warnings


def main(langs: list[str] | None = None) -> int:
    langs_to_check = langs or list(INDEX_PATHS.keys())
    exit_code = 0

    for lang in langs_to_check:
        path = INDEX_PATHS[lang]
        errors, warnings = check_index(lang, path)
        is_fail_lang = lang in FAIL_LANGS

        label = lang.upper()
        prefix = "ERROR" if is_fail_lang else "WARN"

        if not errors and not warnings:
            print(f"[{label}] OK — no issues found")
            continue

        for msg in errors:
            print(f"[{label}] {prefix}: {msg}")
        for msg in warnings:
            print(f"[{label}] WARN: {msg}")

        if errors and is_fail_lang:
            exit_code = 1
        elif errors:
            # warn-only language: print summary but don't fail
            print(f"[{label}] {len(errors)} issue(s) — not blocking (ENG sync pending)")

    return exit_code


if __name__ == "__main__":
    # Simple --lang hun / --lang eng filtering
    requested: list[str] | None = None
    if "--lang" in sys.argv:
        idx = sys.argv.index("--lang")
        try:
            requested = [sys.argv[idx + 1]]
        except IndexError:
            print("Error: --lang requires a value (hun or eng)", file=sys.stderr)
            sys.exit(2)

    sys.exit(main(requested))
