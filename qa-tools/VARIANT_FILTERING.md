# Variant-Specific Rule Filtering Guide

## Overview

The enhanced parser now automatically detects and indexes **variant-specific sub-rules** (VOR, COMBAT, AFTERBLOW) as separate indexed entries. This allows precise searching for rules that apply to specific competition formats.

## Problem Solved

### Before
Searching for "VOR 5 találat" would return the entire `GEN-6.10.4` rule containing all three variants mixed together:

```json
{
  "rule_id": "GEN-6.10.4",
  "text": "...VOR: Valamelyik vívó 5 találatot elért...COMBAT: Valamelyik vívó 5 találatot elért...AFTERBLOW: Valamelyik vívó legalább 7 PONTOT elért...",
  "formatum": ""
}
```

### After
Now the parser automatically splits this into separate rules:

```json
{
  "rule_id": "GEN-6.10.4.1",
  "text": "**VOR**: Valamelyik vívó 5 találatot elért.",
  "formatum": "VOR"
},
{
  "rule_id": "GEN-6.10.4.2",
  "text": "**COMBAT**: Valamelyik vívó 5 találatot elért, illetve...",
  "formatum": "COMBAT"
},
{
  "rule_id": "GEN-6.10.4.3",
  "text": "**AFTERBLOW**: Valamelyik vívó legalább 7 PONTOT elért...",
  "formatum": "AFTERBLOW"
}
```

## How It Works

### Parser Enhancement

The `parser.py` now includes intelligent variant detection:

1. **Detection**: Scans rule text for pattern: `**Vor**:`, `**Combat**:`, `**Afterblow**:`
2. **Extraction**: Splits multi-variant rules into individual sub-rules
3. **Tagging**: Assigns `formatum` field (VOR/COMBAT/AFTERBLOW) to each sub-rule
4. **Indexing**: Creates unique sub-rule IDs (GEN-6.10.4.1, GEN-6.10.4.2, etc.)

### Key Changes in `Rule` Dataclass

```python
@dataclass
class Rule:
    rule_id: str              # e.g., "GEN-6.10.4.1"
    text: str                 # VOR-specific text only
    section: str
    subsection: str
    document: str
    anchor_id: str
    line_number: int
    weapon_type: str = ""     # e.g., "longsword", "general"
    formatum: str = ""        # e.g., "VOR", "COMBAT", "AFTERBLOW"
```

## Searching with Variant Filters

### Automatic Detection

Simply include the variant name in your query:

```
Query: VOR mérkőzés
→ Results automatically filtered to VOR-only rules
  with bonus scoring for formatum matches

Query: COMBAT 5 találat
→ Returns only COMBAT variant rules
```

### Explicit Filtering (API)

```python
from qa_tools.search import RulebookSearch

search = RulebookSearch("qa-tools/rules_index.json")

# Search VOR variant only
vor_results = search.search(
    "mérkőzés",
    formatum_filter="VOR"
)

# Search COMBAT + longsword only
combat_longsword = search.search(
    "támadás",
    weapon_filter="longsword",
    formatum_filter="COMBAT"
)

# Search AFTERBLOW variant only
afterblow_results = search.search(
    "pontok",
    formatum_filter="AFTERBLOW"
)
```

## Search Query Examples

### Hungarian Examples

| Query | Returns |
|-------|---------|
| `VOR 5 találat` | Only VOR variant rules about reaching 5 hits |
| `COMBAT döntő` | Only COMBAT variant rules about deciding hits |
| `AFTERBLOW 7 pont` | Only AFTERBLOW variant rules about scoring 7+ points |
| `hosszúkard COMBAT` | COMBAT rules specifically for longsword |

### English Examples

| Query | Returns |
|-------|---------|
| `VOR match` | Only VOR variant rules |
| `COMBAT decisive` | Only COMBAT variant rules |
| `AFTERBLOW scoring` | Only AFTERBLOW variant rules |
| `longsword COMBAT` | COMBAT rules for longsword |

### Rule ID Lookup

```
Query: GEN-6.10.4.1
→ Returns specific VOR sub-rule

Query: GEN-6.10.4.2
→ Returns specific COMBAT sub-rule

Query: GEN-6.10.4.3
→ Returns specific AFTERBLOW sub-rule
```

## Output Format

Search results now display variant information clearly:

```
======================================================================
Rule ID: GEN-6.10.4.1
Document: 01-altalanos.md
Category: [VOR]

Section: Vívásra általánosan érvényes szabályok
Subsection: A mérkőzés időtartama

Text:
**VOR**: Valamelyik vívó 5 találatot elért.

[Relevance Score: 95.3]
======================================================================
```

## Scoring Algorithm

The search engine now includes variant-aware scoring:

1. **Exact Rule ID Match**: +100.0 points
2. **Exact Text Match**: +50.0 points
3. **Exact Section Match**: +30.0 points
4. **Term Frequency**: +10.0 per occurrence
5. **Variant Match** (NEW): +25.0 bonus if query variant matches rule formatum
6. **Section/Subsection Terms**: +5.0 bonus
7. **Weapon-Specific Rule**: +10.0 bonus if weapon detected in query

## Supported Variant Keywords

### English
- `VOR` → VOR variant
- `COMBAT` → COMBAT variant
- `AFTERBLOW` → AFTERBLOW variant

### Hungarian (Extended Support)
- `VOR`, `VORBEIGEHEN` → VOR variant
- `COMBAT`, `SZABADHARC` → COMBAT variant
- `AFTERBLOW`, `UTÁN` → AFTERBLOW variant

## Regenerating the Index

After parser.py updates, regenerate the index:

```powershell
python qa-tools/parser.py
```

This will:
1. Parse all rulebook markdown files
2. Detect and extract variant-specific sub-rules
3. Create `rules_index.json` with new formatum tags
4. Display statistics on variant rules found

## API Usage Examples

### Example 1: Find all VOR-specific rules about timeouts

```python
search = RulebookSearch("qa-tools/rules_index.json")
results = search.search(
    "időlimit limit timeout",
    formatum_filter="VOR",
    max_results=10
)
```

### Example 2: Compare COMBAT vs AFTERBLOW scoring rules

```python
combat_scoring = search.search(
    "pontok scoring points",
    formatum_filter="COMBAT",
    max_results=5
)

afterblow_scoring = search.search(
    "pontok scoring points", 
    formatum_filter="AFTERBLOW",
    max_results=5
)
```

### Example 3: Find all variants of a rule

```python
# Get the base rule
base_rule = search.get_rule_by_id("GEN-6.10.4")

# Manually fetch all variants
variants = {
    "VOR": search.get_rule_by_id("GEN-6.10.4.1"),
    "COMBAT": search.get_rule_by_id("GEN-6.10.4.2"),
    "AFTERBLOW": search.get_rule_by_id("GEN-6.10.4.3")
}

for variant_name, rule in variants.items():
    if rule:
        print(f"{variant_name}: {rule['text']}")
```

## Limitations & Future Enhancements

### Current Limitations
- Variant detection relies on specific formatting: `**VOR**:`, `**Combat**:`, `**Afterblow**:`
- Rules must follow strict structure with variant headers
- Only detects 3 variants (VOR, COMBAT, AFTERBLOW)

### Potential Enhancements
- Support for other weapon-specific variants (rapier, padded weapons)
- Nested variant rules (variants within variants)
- Variant inheritance rules (base + variant-specific overrides)
- Visual highlighting of variant differences in search results
- Variant comparison mode (side-by-side display)

## Troubleshooting

### "No results found" for variant queries

Check that:
1. Index was regenerated after parser.py updates
2. Query includes exact variant name (VOR, COMBAT, or AFTERBLOW)
3. Variant name is spelled correctly (case-insensitive, but must match)

### Results include unrelated rules

The search uses keyword matching. Narrow results by:
- Adding more specific keywords to query
- Using formatum filter explicitly: `formatum_filter="VOR"`
- Reducing `max_results` parameter

### Some rules not split into variants

Ensure the rule text follows the expected format:
```markdown
**Rule ID**
**Format1**: Text for format 1...
**Format2**: Text for format 2...
```

Check alignment and spacing in the markdown source.
