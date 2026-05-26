# QA Tools Examples

This directory contains example and demo scripts that show how to use the HEMA Rulebook QA tools.

## Available Examples

### 1. `view_index.py`
View sample rules from the generated index file.

**Usage:**
```bash
python examples/qa_tools/view_index.py
```

**Purpose:** Quick inspection tool to verify the rules index structure and content.

---

### 2. `check_variants.py`
Diagnostic script to verify variant detection (VOR, COMBAT, AFTERBLOW).

**Usage:**
```bash
python examples/qa_tools/check_variants.py
```

**Purpose:** Validates that variant-specific rules are correctly tagged during parsing.

---

## For Production Tools

Production tools (parser, search, alias management) live in `src/qa_tools/tools/` and are used by the build process.

For detailed documentation on the QA tools architecture, see:
- `qa_tools/README.md` - Main QA tools documentation
- `docs/qa_tools/README.md` - QA tools docs (this repo)
- `docs/qa-architecture.md` - System architecture
- `docs/SEARCH_ENGINE.md` - Search algorithm details
