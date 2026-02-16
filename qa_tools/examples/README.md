# QA Tools Examples

This directory contains example and demo scripts that show how to use the HEMA Rulebook QA tools.

## Available Examples

### 1. `ai_explainer_example.py`
Demonstrates how to use hierarchy metadata for AI-assisted rule explanations.

**Usage:**
```bash
python qa_tools/examples/ai_explainer_example.py
```

**Purpose:** Shows how to leverage parent_id, child_ids, lineage, depth, and sibling_ids fields to build contextual explanations.

---

### 2. `view_index.py`
View sample rules from the generated index file.

**Usage:**
```bash
python qa_tools/examples/view_index.py
```

**Purpose:** Quick inspection tool to verify the rules index structure and content.

---

### 3. `check_variants.py`
Diagnostic script to verify variant detection (VOR, COMBAT, AFTERBLOW).

**Usage:**
```bash
cd qa_tools
python examples/check_variants.py
```

**Purpose:** Validates that variant-specific rules are correctly tagged during parsing.

---

## For Production Tools

Production tools (parser, search, alias management) remain in `qa_tools/tools/` and are used by the build process.

For detailed documentation on the QA tools architecture, see:
- `qa_tools/README.md` - Main QA tools documentation
- `docs/qa-architecture.md` - System architecture
- `docs/SEARCH_ENGINE.md` - Search algorithm details
