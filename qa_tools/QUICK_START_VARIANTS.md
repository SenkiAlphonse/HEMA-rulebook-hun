# Quick Start: Using Variant-Specific Search

## The Problem You Asked About

When searching for `GEN-6.10.4` rules, you wanted to find **only VOR**, **only COMBAT**, or **only AFTERBLOW** rules instead of getting all three mixed together.

## The Solution

The system now **automatically detects and tags** variant-specific rules in the index, allowing you to filter by format.

## Search Examples

### Example 1: Find all VOR rules about reaching 5 hits

**Query**: `VOR 5 találat`

**Result**: Returns only VOR variant rules
```
GEN-6.10.4.1.1 [VOR]
**Vor**: Valamelyik vívó 5 találatot elért.
```

### Example 2: Find COMBAT-specific rules about tied scores

**Query**: `COMBAT 4-4`

**Result**: Returns only COMBAT variant rules
```
GEN-6.10.4.1.2 [COMBAT]
**Combat**: ha a versenyzők 4-4-es állásig jutnak...
```

### Example 3: Find AFTERBLOW scoring rules

**Query**: `AFTERBLOW 7 PONT`

**Result**: Returns only AFTERBLOW variant rules
```
GEN-6.10.4.1.3 [AFTERBLOW]
**Afterblow**: Valamelyik vívó legalább 7 PONTOT elért...
```

### Example 4: Look up specific variant rule by ID

**Query**: `GEN-6.10.4.1.1`

**Result**: Directly returns VOR sub-rule
```
GEN-6.10.4.1.1 [VOR]
**Vor**: Valamelyik vívó 5 találatot elért.
```

## How It Works Behind the Scenes

### Markdown Format
The rulebook uses this format for variant-specific rules:
```markdown
**GEN-6.10.4.1.1**
**Vor**: Rule text here...

**GEN-6.10.4.1.2**
**Combat**: Rule text here...

**GEN-6.10.4.1.3**
**Afterblow**: Rule text here...
```

### Detection
The parser automatically detects when a rule starts with `**Vor**:`, `**Combat**:`, or `**Afterblow**:` and tags it accordingly.

### Index Format
Each rule in the index now includes a `formatum` field:
```json
{
  "rule_id": "GEN-6.10.4.1.1",
  "text": "**Vor**: Valamelyik vívó 5 találatot elért.",
  "formatum": "VOR"
}
```

### Search Scoring
When you include a variant name in your query, it gets a **+25 point bonus** for matching rules.

## Tips for Best Results

1. **Be specific**: Include the variant name in your query
   - ✅ Good: `VOR mérkőzés`
   - ✓ OK: `VOR`
   - ⚠️ Less precise: `5 találat` (returns all variants)

2. **Use exact variant names**:
   - `VOR` or `Vor` (case-insensitive)
   - `COMBAT` or `Combat`
   - `AFTERBLOW` or `Afterblow`

3. **Combine with other filters**:
   - `VOR hosszúkard` (VOR + longsword)
   - `COMBAT rapier` (COMBAT + rapier)
   - `AFTERBLOW pontozás` (AFTERBLOW + scoring)

## Supported Variant Keywords

| Keyword | Maps To |
|---------|---------|
| VOR, Vor, vor | VOR |
| COMBAT, Combat, combat | COMBAT |
| AFTERBLOW, Afterblow, afterblow | AFTERBLOW |

## Test It Yourself

Run the interactive search:
```bash
cd qa-tools
python search.py
```

Then try these queries:
```
Query: VOR
Query: COMBAT döntő
Query: AFTERBLOW pont
Query: GEN-6.10.4.1.2
Query: VOR mérkőzés hosszúkard
```

## Programmatic Usage

If you're building on top of this system:

```python
from qa_tools.search import RulebookSearch

search = RulebookSearch("qa-tools/rules_index.json")

# Get VOR-only results
vor_results = search.search("mérkőzés", formatum_filter="VOR")

# Get COMBAT-only results
combat_results = search.search("döntő", formatum_filter="COMBAT")

# Get AFTERBLOW-only results
ab_results = search.search("pont", formatum_filter="AFTERBLOW")

# Get a specific variant rule by ID
vor_rule = search.get_rule_by_id("GEN-6.10.4.1.1")
```

## What Changed in the System

1. **Parser** (`qa-tools/parser.py`):
   - Detects variant keywords in rule text
   - Assigns `formatum` tag to each rule

2. **Search Engine** (`qa-tools/search.py`):
   - Recognizes variant keywords in queries
   - Awards bonus points for matching variants
   - Supports explicit filtering via `formatum_filter` parameter

3. **Index** (`qa-tools/rules_index.json`):
   - All 392 rules now have correct `formatum` tags
   - VOR, COMBAT, and AFTERBLOW rules are distinguishable

## Questions?

See the full documentation in `qa-tools/VARIANT_FILTERING.md`
