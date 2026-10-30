# Alias-Aware Search System

## What's New

Your Q&A system now supports **intelligent alias matching** to make searches more flexible and user-friendly.

## Alias Types

### 1. **Variant Aliases** (Változat Aliasok)
Map alternative names to competition rule variants:
- **VOR** → "right of way", "row", "right-of-way", "priority", "prio"
- **COMBAT** → "free fencing", "combat", "free-fencing"
- **AFTERBLOW** → "afterblow", "after-blow", "ab", "after blow"

**Example:** Query `"right of way rules"` finds rules that contain "rules" and any of the VOR
phrases (e.g. "priority"). It does not restrict results to the VOR ruleset; use the Variant
filter for that.

### 2. **Weapon Aliases** (Fegyvernem Aliasok)
Map alternative names to weapons:
- **longsword** → "sword", "ls", "long sword", "longsword", "hosszúkard"
- **rapier** → "rapier", "rp", "rapira", "rapier sword"
- **padded_weapons** → "padded", "padded weapons", "padded weapon", "párnázott"

**Example:** Query `"sword target areas"` finds rules that mention any of the longsword terms and
"target areas". Use the Weapon filter to restrict results to one weapon.

### 3. **Concept Aliases** (Koncepció Aliasok)
Map related terms to important concepts:
- **target** → "target area", "valid target", "Finding", "találati felület"
- **penalty** → "penalty", "punishment", "büntetés", "sanctioned"
- **equipment** → "gear", "felszerelés", "protective gear"
- **illegal** → "forbidden", "not allowed", "prohibited", "tilos"

**Example:** Query `"illegal techniques"` finds rules that contain "techniques" and any of the
terms above, such as "prohibited" or "tilos"

### How Matching Works

The three categories are only a way to organise `aliases.json`: every list is a group of
interchangeable phrases. A rule matches when each alias group named in the query is found in the
rule's own text or one of its headings, as a whole word or phrase, and every remaining keyword is
found too. A rule's variant or weapon metadata never makes it a match.

## How to Use

### Basic Search
```
Query: longsword target areas
→ Returns rules that mention a longsword term and a target-area term
```

### With Format Filter
```
Query: equipment, variant_filter="VOR"
→ Returns only general + VOR-specific equipment rules
```

### With Weapon Filter
```
Query: strike, weapon_filter="longsword"
→ Returns longsword-specific and general strike rules
```

### Using Aliases
```
Query: right of way priority
→ Finds rules that mention "right of way", "priority" or the other VOR terms

Query: free fencing cut
→ Finds rules that mention "free fencing" or "combat", and "cut"

Query: padded weapon target
→ Finds rules that mention "padded" or "padded weapon", and "target"
```

## Customizing Aliases

Edit `data/search/aliases.json` to add your own aliases:

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

Each alias group named in the query adds one bonus per search, not one per alias:
- Group found in the rule text: +40 points
- Group found only in a heading: +20 points
- Exact rule ID match: ranked in its own tier above all other results

Results are sorted by total relevance score.

## Search Tools Available

1. **`search_aliases.py`** - New alias-aware search (recommended)
   ```powershell
  python -m qa_tools.search_engine.search_aliases
   ```

2. **`search.py`** - Original basic search (still works)
   ```powershell
  python -m qa_tools.search_engine.search
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
