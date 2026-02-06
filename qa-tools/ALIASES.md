# Alias-Aware Search System

## What's New

Your Q&A system now supports **intelligent alias matching** to make searches more flexible and user-friendly.

## Alias Types

### 1. **Format Aliases** (Formátum Aliasok)
Map alternative names to competition formats:
- **VOR** → "right of way", "row", "right-of-way", "priority", "prio"
- **COMBAT** → "free fencing", "combat", "cf", "free-fencing"
- **AFTERBLOW** → "afterblow", "after-blow", "ab", "after blow"

**Example:** Query `"right of way rules"` will find all VOR format rules

### 2. **Weapon Aliases** (Fegyver Aliasok)
Map alternative names to weapons:
- **longsword** → "sword", "ls", "long sword", "longsword", "hosszúkard"
- **rapier** → "rapier", "rp", "rapira", "rapier sword"
- **padded_weapons** → "padded", "padded weapons", "padded weapon", "párnázott"

**Example:** Query `"sword target areas"` finds longsword rules

### 3. **Concept Aliases** (Koncepció Aliasok)
Map related terms to important concepts:
- **target** → "target area", "valid target", "Finding", "találati felület"
- **penalty** → "penalty", "punishment", "büntetés", "sanctioned"
- **equipment** → "gear", "felszerelés", "protective gear"
- **illegal** → "forbidden", "not allowed", "prohibited", "tilos"

**Example:** Query `"illegal techniques"` boosts scoring for rules about prohibited actions

## How to Use

### Basic Search
```
Query: longsword target areas
→ Returns longsword rules about targets
```

### With Format Filter
```
Query: VOR equipment
→ Returns only general + VOR-specific equipment rules
```

### With Weapon Filter
```
Query: longsword strike
→ Returns longsword-specific strike rules
```

### Using Aliases
```
Query: right of way priority
→ Finds VOR rules (aliases: "right of way", "priority")

Query: free fencing cut
→ Finds COMBAT format rules (alias: "free fencing")

Query: padded weapon target
→ Finds padded weapons rules (alias: "padded")
```

## Customizing Aliases

Edit `qa-tools/aliases.json` to add your own aliases:

```json
{
  "variants": {
    "VOR": ["your", "custom", "aliases"]
  },
  "weapons": {
    "longsword": ["your", "aliases"]
  },
  "concepts": {
    "your_concept": ["aliases", "here"]
  }
}
```

Then restart the search tool—changes take effect immediately!

## How Scoring Works

Alias matches get bonus points:
- Format alias match: +40 points
- Weapon alias match: +20 points
- Concept alias match: +15 points
- Direct rule ID match: +100 points (still highest priority)

Results are sorted by total relevance score.

## Search Tools Available

1. **`search_aliases.py`** - New alias-aware search (recommended)
   ```powershell
   python qa-tools\search_aliases.py
   ```

2. **`search.py`** - Original basic search (still works)
   ```powershell
   python qa-tools\search.py
   ```

## Example Session

```
Query: right of way target

Found 3 results:

1. [LS-VOR-2.1.1] 05.a-hosszukard-VOR.md
   Format: VOR
   Section: VOR Finding Rules
   
   The valid target area in VOR format includes...
   [Score: 85.3]

2. [GEN-1.2.5] 01-altalanos.md
   Section: General Target Rules
   
   Valid targets apply to all formats including...
   [Score: 45.2]
```

## Next Steps

1. **Test the searches** with your domain knowledge
2. **Refine aliases** in `aliases.json` based on what works best
3. **Add more concepts** for frequently asked questions
4. **Consider multilingual aliases** for English/Hungarian terms

Happy searching! 🤺
