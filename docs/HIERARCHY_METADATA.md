# Hierarchy Metadata for AI-Assisted Explanations

## Overview

The parser now includes **explicit hierarchy metadata** in every rule to enable rich, contextual AI-assisted explanations. Instead of computing parent-child relationships on-the-fly, all hierarchy information is **pre-computed at index time** and stored in the JSON index.

## New Fields

Each rule now includes:

| Field | Type | Purpose |
|-------|------|---------|
| `parent_id` | `str` | Direct parent rule ID (e.g., `"GEN-3.2.1"` for `"GEN-3.2.1.1"`) |
| `child_ids` | `list[str]` | All direct child rule IDs |
| `lineage` | `list[str]` | Path from root to parent (e.g., `["GEN", "GEN-3", "GEN-3.2", "GEN-3.2.1"]`) |
| `depth` | `int` | Nesting level (1=root/prefix only, 5=deepest nested) |
| `is_leaf` | `bool` | `true` if rule has no children |
| `sibling_ids` | `list[str]` | All rules with the same parent (excluding self) |

## Example: GEN-3.2.1.1

```json
{
  "rule_id": "GEN-3.2.1.1",
  "text": "**Támadás** - az a kitörést vagy...",
  "section": "",
  "subsection": "Támadó és védekező akciók",
  "depth": 4,
  "parent_id": "GEN-3.2.1",
  "child_ids": [],
  "lineage": ["GEN", "GEN-3", "GEN-3.2", "GEN-3.2.1"],
  "is_leaf": true,
  "sibling_ids": ["GEN-3.2.1.2", "GEN-3.2.1.3"]
}
```

### Hierarchy Breakdown

- **Depth 4**: This is a deep nested rule
- **Parent**: `GEN-3.2.1` (Támadó akciók - Supporting attack actions)
- **Lineage**: Shows path: `GEN` → `GEN-3` (Definitions) → `GEN-3.2` (Attack & Defense Actions) → `GEN-3.2.1` (Attack Actions)
- **Is Leaf**: No children; this is a terminal definition
- **Siblings**: `GEN-3.2.1.2` (Riposzt), `GEN-3.2.1.3` (Kontrariposzt) - related attack types

## Example: GEN-3.2.1 (Parent Rule)

```json
{
  "rule_id": "GEN-3.2.1",
  "text": "Támadó akciók (a támadás, a riposzt...)",
  "depth": 3,
  "parent_id": "GEN-3.2",
  "child_ids": ["GEN-3.2.1.1", "GEN-3.2.1.2", "GEN-3.2.1.3", ...],
  "lineage": ["GEN", "GEN-3", "GEN-3.2"],
  "is_leaf": false,
  "sibling_ids": ["GEN-3.2.2", "GEN-3.2.3", "GEN-3.2.4", ...]
}
```

## Use Cases for AI Explanations

### 1. Contextual Lookups
When a user asks "What is GEN-3.2.1.1?", AI can show:
```
Rule: GEN-3.2.1.1 (Támadás)
Part of: GEN-3.2.1 (Attack Actions)
  which is part of: GEN-3.2 (Attack & Defense Definitions)
  which is part of: GEN-3 (General Definitions)

Related attack types: GEN-3.2.1.2 (Riposzt), GEN-3.2.1.3 (Kontrariposzt)
```

### 2. Rule Relationships
When explaining a parent rule like GEN-3.2.1, AI can say:
```
This rule defines the three main attack actions:
- GEN-3.2.1.1: Támadás (Attack)
- GEN-3.2.1.2: Riposzt (Riposte)
- GEN-3.2.1.3: Kontrariposzt (Counter-Riposte)
```

### 3. Breadcrumb Navigation
Show hierarchy context inline:
```
General Rules > Definitions > Attack & Defense > Attack Actions > Attack (Támadás)
```

### 4. Cross-Reference Resolution
When a rule references another, AI can immediately show:
```
See GEN-3.2.1.1 (Attack/Támadás)
  which is in: GEN-3.2.1 (Attack Actions)
  sibling rules: GEN-3.2.1.2, GEN-3.2.1.3
```

## Statistics

As of the latest build:

```
Total rules: 545
Depth distribution:
- Depth 2: 18 rules
- Depth 3: 342 rules (most common)
- Depth 4: 170 rules
- Depth 5: 15 rules

Leaf vs Parent:
- Leaf rules (no children): 511
- Parent rules (have children): 34
```


## Benefits for LLM Integration

1. **Explicit Metadata**: LLMs no longer need to parse rule IDs; hierarchy is pre-computed
2. **Contextual Grounding**: AI can cite entire hierarchical paths, improving credibility
3. **Relationship Awareness**: AI understands rule families, siblings, and parent-child relationships
4. **Performance**: No runtime computation; all lookups are O(1) array access
5. **Future-Proof**: Enables fine-tuning LLMs on structured hierarchical rule data

## Breaking Changes

None. Old fields remain unchanged; new fields are additive.

## Index Size Impact

+~200-300 bytes per rule. For 545 rules, approximately +100-150 KB to the index.
