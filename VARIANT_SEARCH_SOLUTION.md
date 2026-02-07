# Solution: Variant-Specific Rule Filtering

## Problem Solved ✓

When searching for rules like **GEN-6.10.4**, the old system would return a single massive rule containing all three variants (VOR, COMBAT, AFTERBLOW) mixed together. Now, you can search for **variant-specific sub-rules** and get exactly what you need.

## How It Works

### 1. **Automatic Detection**
The parser now detects when rules contain variant-specific content and automatically tags them:

```
**GEN-6.10.4.1.1**: Vor: Valamelyik vívó 5 találatot elért.
  → formatum: "VOR"

**GEN-6.10.4.1.2**: Combat: Valamelyik vívó 5 találatot elért...
  → formatum: "COMBAT"

**GEN-6.10.4.1.3**: Afterblow: Valamelyik vívó legalább 7 PONTOT elért...
  → formatum: "AFTERBLOW"
```

### 2. **Smart Search**
The search engine now understands variant keywords:

| Query | Result |
|-------|--------|
| `VOR mérkőzés` | Only VOR variant rules |
| `COMBAT 5 találat` | Only COMBAT variant rules |
| `AFTERBLOW pont` | Only AFTERBLOW variant rules |
| `5 találat` | All rules mentioning "5 találat" (ranked by relevance) |

### 3. **Scoring Algorithm**
Variant-aware scoring gives bonuses when query matches rule format:

- **Variant match**: +25 points bonus
- **Exact rule ID**: +100 points
- **Exact text match**: +50 points
- **General rules**: +5 points bonus (if no specific variant)

## Implementation Details

### Parser Changes (`parser.py`)

Added `_detect_formatum_in_rule_text()` method:

```python
def _detect_formatum_in_rule_text(self, text: str) -> str:
    """Detect formatum from rule text like **Vor**: or **Combat**: or **Afterblow**:"""
    pattern = re.compile(r'^\*\*(vor|combat|afterblow)\*\*:', re.IGNORECASE)
    match = pattern.match(text.strip())
    if match:
        return match.group(1).upper()
    return ''
```

### Search Enhancement (`search.py`)

- `_detect_formatum_in_query()`: Extracts variant keywords from queries
- Enhanced `_calculate_score()`: Awards variant match bonuses
- Updated `search()`: Supports `formatum_filter` parameter

## Test Results

### Test 1: Generic Search
```
Query: "5 találat"
Results:
  1. GEN-6.10.6.1 (general) - Score: 110.0
  2. LS-AB-1.2.5.1 [AFTERBLOW] - Score: 95.0
  3. GEN-6.10.4.1.2 [COMBAT] - Score: 80.0
```

### Test 2: Variant-Specific Search
```
Query: "VOR"
Results:
  1. GEN-6.10.4.1.1 [VOR] - Score: 85.0 ✓
  2. GEN-6.10.5.1.1 [VOR] - Score: 85.0 ✓
  3. LS-VOR-1.1.1 [VOR] - Score: 85.0 ✓
```

### Test 3: Explicit Filter
```
Query: "pont" with formatum_filter="AFTERBLOW"
Results:
  1. GEN-6.10.4.1.3 [AFTERBLOW] - Score: 100.0 ✓
  2. LS-AB-1.2.8 [AFTERBLOW] - Score: 100.0 ✓
  3. LS-AB-1.2.9 [AFTERBLOW] - Score: 100.0 ✓
```

## Usage Examples

### Interactive CLI
```bash
python qa-tools/search.py

Query: VOR mérkőzés
→ Returns only VOR variant rules

Query: AFTERBLOW 7 pont
→ Returns only AFTERBLOW variant rules

Query: GEN-6.10.4.1.1
→ Returns specific VOR sub-rule
```

### Programmatic API
```python
from qa_tools.search import RulebookSearch

search = RulebookSearch("qa-tools/rules_index.json")

# VOR variant only
results = search.search("mérkőzés", formatum_filter="VOR")

# COMBAT variant only  
results = search.search("támadás", formatum_filter="COMBAT")

# AFTERBLOW variant only
results = search.search("pontok", formatum_filter="AFTERBLOW")
```

## Key Files Modified

| File | Changes |
|------|---------|
| `qa-tools/parser.py` | Added variant detection in `_save_rule()` and `_detect_formatum_in_rule_text()` |
| `qa-tools/search.py` | Enhanced scoring, added formatum filtering, improved result formatting |
| `qa-tools/VARIANT_FILTERING.md` | Complete documentation (created) |
| `qa-tools/rules_index.json` | Regenerated with formatum tags on all 392 rules |

## Index Statistics

- **Total rules indexed**: 392
- **Rules with VOR tag**: 15+
- **Rules with COMBAT tag**: 15+
- **Rules with AFTERBLOW tag**: 15+
- **General (no variant) rules**: 350+

## Benefits

✅ **Precision**: Find exact variant rules without wading through alternatives  
✅ **Clarity**: Search results clearly show which variant applies  
✅ **Efficiency**: Automatic detection - no manual tagging needed  
✅ **Scalability**: Supports other variants/weapons in future (rapier, padded, etc.)  
✅ **Natural**: Query works with Hungarian or English keywords

## Future Enhancements

- Support for other weapon variants (rapier, padded weapons)
- Nested variants (variants within variants)
- Side-by-side variant comparison mode
- Visual highlighting of variant differences
- Export rules by variant for tournament prep
