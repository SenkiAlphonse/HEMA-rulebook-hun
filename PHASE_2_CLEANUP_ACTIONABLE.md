# Phase 2 Cleanup - Actionable Items

## Priority 1: CRITICAL (Fix Before Any Deployment)

### Action 1.1: Add gunicorn to requirements.txt
**File**: `requirements.txt`

**Current** (line 5):
```txt
protobuf>=4.25.0,<6.0.0
```

**Add** (after Flask packages):
```txt
gunicorn==21.2.0
```

**Why**: Production servers need proper WSGI server, not Flask development `app.run()`

**Verify**:
```bash
pip install -r requirements.txt
which gunicorn
gunicorn --version
```

**Time**: 10 min  
**Criticality**: BLOCKING - production stability

---

## Priority 2: HIGH-VALUE QUICK WINS

### Action 2.1: Remove Unused Imports
**File 1**: `app/utils.py` (line 6)  
**Remove**: `import sys`

**File 2**: `qa_tools/tools/parser.py` (line 6)  
**Remove**: `import os`

**Verify**: All tests pass
```bash
pytest tests/ -v
```

**Time**: 5 min  
**Impact**: Cleanup

---

### Action 2.2: Delete Redundant Files

**File 1**: Delete `Procfile`
- Reason: Render.com uses `render.yaml` instead
- Reason: Procfile would run pytest on production (bad)

**File 2**: Delete `READY_TO_DEPLOY.txt`
- Reason: Duplicate of `WEB_READY.md`
- Keep: `WEB_READY.md` (better formatted)

**Update**: `README.md`
- Replace all references to `READY_TO_DEPLOY.txt` with `WEB_READY.md`

**Verify**: 
```bash
grep -r "READY_TO_DEPLOY" .
grep -r "WEB_READY" .
```

**Time**: 15 min  
**Impact**: Cleanup

---

### Action 2.3: Archive Outdated Documentation

**Files to Archive** (not delete - keep for history):
- `CRITICAL_FIXES_SUMMARY.md` → Already applied to code
- `HIERARCHY_IMPLEMENTATION_SUMMARY.md` → Already in docs/HIERARCHY_METADATA.md

**Move to**: `docs/archive/` directory
```bash
mkdir -p docs/archive
mv CRITICAL_FIXES_SUMMARY.md docs/archive/
mv HIERARCHY_IMPLEMENTATION_SUMMARY.md docs/archive/
```

**Update**: `README.md` - remove references to archived files

**Time**: 10 min  
**Impact**: Documentation clarity

---

## Priority 3: CODE QUALITY - DUPLICATE ELIMINATION

### Action 3.1: Eliminate Duplicate `get_rule_depth()`

**Step 1**: Verify the function exists in `search_utils.py`
```python
# qa_tools/search_engine/search_utils.py (lines 7-19)
def get_rule_depth(rule_id: str) -> int:
    """Calculate indentation depth from rule ID"""
    # ... implementation
```

**Step 2**: Remove private implementation in `parser.py`
- Location: `qa_tools/tools/parser.py` lines 415-423
- Replace with: Import statement

**Old Code**:
```python
def _get_rule_depth(self, rule_id: str) -> int:
    """Calculate nesting depth from rule ID"""
    if not rule_id or '-' not in rule_id:
        return 0
    parts = rule_id.split('-')
    numeric_part = parts[-1]
    return numeric_part.count('.') + 1
```

**New Code** (at top of parser.py):
```python
from qa_tools.search_engine.search_utils import get_rule_depth as calculate_rule_depth
```

**Step 3**: Replace usage in `_build_hierarchy_metadata()`
- Location: `parser.py` line 411
- Old: `rule.depth = self._get_rule_depth(rule.rule_id)`
- New: `rule.depth = calculate_rule_depth(rule.rule_id)`

**Verify**:
```bash
pytest tests/ -v
pytest tests/unit/test_parser.py -v
```

**Time**: 30 min  
**Impact**: Maintenance (eliminates duplicate)

---

### Action 3.2: Eliminate Duplicate `get_rule_lineage()`

**Step 1**: Verify existing in `search_utils.py`
```python
# qa_tools/search_engine/search_utils.py (lines 31-70)
def get_rule_lineage(rule_id: str) -> List[str]:
    """Get list of parent rule IDs for a given rule"""
    # ... implementation
```

**Step 2**: Remove private implementation in `parser.py`
- Location: `parser.py` lines 424-443
- This duplicates the `get_rule_lineage()` function

**Step 3**: Add import (if not already added in Action 3.1)
```python
from qa_tools.search_engine.search_utils import (
    get_rule_depth as calculate_rule_depth,
    get_rule_lineage
)
```

**Step 4**: Replace usage in `_build_hierarchy_metadata()`
- Location: `parser.py` line 412
- Old: `rule.lineage = self._get_rule_lineage(rule.rule_id)`
- New: `rule.lineage = get_rule_lineage(rule.rule_id)`

**Step 5**: Remove duplicate `_get_parent_id()` and use lineage
- The parent_id can be computed from lineage or extracted via new helper
- Alternative: Add to search_utils.py:
```python
def get_parent_id(rule_id: str) -> str:
    """Get direct parent rule ID"""
    lineage = get_rule_lineage(rule_id)
    return lineage[-1] if lineage else ""
```

**Verify**:
```bash
pytest tests/ -v
pytest tests/unit/test_parser.py::TestRulebookParser -v
```

**Time**: 45 min  
**Impact**: Maintenance (eliminates 2 duplicates)

---

### Action 3.3: Remove Dead Code

**File**: `qa_tools/tools/parser.py`

**Step 1**: Delete lines 390-430 (two dead methods)
```python
# DELETE THESE:
def _extract_variant_subrules(self, ...):  # Never called
def _variant_to_subrule_index(self, ...):   # Only used by dead code
```

**Reason**: 
- `_extract_variant_subrules()` - experimental, never integrated
- `_variant_to_subrule_index()` - only used by the above

**Alternative**: If might be needed later:
- Create `qa_tools/experimental/variant_subrules.py`
- Move functions there with comment explaining why they're experimental

**Verify**:
```bash
grep -n "_extract_variant_subrules" qa_tools/tools/parser.py  # Should be 0 results
grep -n "_variant_to_subrule_index" qa_tools/tools/parser.py  # Should be 0 results
pytest tests/ -v
```

**Time**: 15 min  
**Impact**: Cleanup (40 lines removed)

---

## Priority 4: DEPENDENCIES - REORGANIZATION

### Action 4.1: Separate Development Dependencies

**Step 1**: Create `requirements-dev.txt`
```txt
-r requirements.txt

pytest==9.0.2
pytest-flask==1.3.0
pytest-mock==3.15.1
```

**Step 2**: Update `requirements.txt` - Remove testing packages
```txt
# REMOVE these lines:
# pytest==9.0.2
# pytest-flask==1.3.0
# pytest-mock==3.15.1
```

**Step 3**: Update `.gitignore` if needed (already handles)

**Step 4**: Update documentation
- Add to `GETTING_STARTED.md`:
```bash
# For development
pip install -r requirements-dev.txt

# For production
pip install -r requirements.txt
```

**Step 5**: Update deployment config
- `render.yaml` - uses `requirements.txt` (correct)
- Local development - use `requirements-dev.txt`

**Verify**:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pytest tests/ -v
```

**Time**: 45 min  
**Impact**: Medium (cleaner deployments, smaller footprint)

---

### Action 4.2: Tighten Protobuf Constraint (Optional)

**File**: `requirements.txt` (line 5)

**Current**: `protobuf>=4.25.0,<6.0.0`

**Change to**: `protobuf>=4.25.0,<5.0.0`

**Reason**: Protobuf 5.x might have breaking changes; better to pin to tested version

**Time**: 1 min  
**Impact**: Low (version stability)

---

## Priority 5: COMPLEX FUNCTIONS - REFACTORING

### Action 5.1: Refactor `parse_file()` in parser.py

**Current Complexity**: 95 lines, cyclomatic complexity 7 (too high)

**Step 1**: Create helper methods for subtasks
```python
# In RulebookParser class, after __init__:

def _process_heading_line(self, line, line_num):
    """Process heading lines and update tracking"""
    # Extract logic from parse_file for heading detection
    pass

def _process_anchor_line(self, line):
    """Process anchor span lines"""
    # Extract anchor detection logic
    pass

def _process_rule_id_line(self, line, line_num):
    """Process rule ID lines"""
    # Extract rule ID detection logic
    pass

def _accumulate_rule_text(self, line):
    """Add line to current rule text"""
    # Extract text accumulation logic
    pass
```

**Step 2**: Simplify `parse_file()`:
```python
def parse_file(self, filepath: Path):
    """Parse a single markdown file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    weapon_type, variant = self._extract_weapon_info(filepath.name)
    
    # Initialize tracking variables
    current_section = ""
    current_subsection = ""
    current_anchor = ""
    current_rule_id = ""
    rule_text_lines = []
    rule_start_line = 0
    
    for i, line in enumerate(lines, start=1):
        # Process each line type
        if self.heading_pattern.match(line):
            self._handle_heading(line, current_rule_id, rule_text_lines, 
                               filepath.name, current_anchor, rule_start_line,
                               current_section, current_subsection, 
                               weapon_type, variant)
            current_rule_id, rule_text_lines = "", []
            current_section, current_subsection = self._extract_section_from_heading(line)
            continue
        
        # ... similar refactored structure
```

**Verify**:
```bash
pytest tests/unit/test_parser.py -v
# All tests should pass
```

**Time**: 3-4 hours  
**Impact**: HIGH (maintainability, testability)

---

### Action 5.2: Refactor `search()` in search_aliases.py

**Current Complexity**: 65 lines, cyclomatic complexity 8

**Step 1**: Extract query expansion logic
```python
def _expand_query_with_aliases(self, query):
    """Expand query based on aliases and return filters"""
    # Extract from current _expand_query method
    return expanded_query, variant_filter, weapon_filter, concept_terms
```

**Step 2**: Extract filtering and scoring logic
```python
def _filter_and_score_rules(self, expanded_query, variant_filter, 
                            weapon_filter, concept_terms):
    """Filter and score all rules"""
    results = []
    for rule in self.rules:
        # ... filtering logic
        score = self._calculate_score(rule, expanded_query, concept_terms)
        results.append((rule, score))
    return results
```

**Step 3**: Extract ranking and grouping logic
```python
def _rank_and_limit_results(self, scored_results, max_results):
    """Rank results and limit to max_results"""
    # ... ranking logic
    return final_results
```

**Step 4**: Simplify main `search()` method:
```python
def search(self, query, max_results=5, variant_filter=None, weapon_filter=None):
    expanded_query, detected_variant, detected_weapon, concept_terms, _ = (
        self._expand_query_with_aliases(query)
    )
    
    variant_filter = variant_filter or detected_variant
    weapon_filter = weapon_filter or detected_weapon
    
    scored_results = self._filter_and_score_rules(
        expanded_query, variant_filter, weapon_filter, concept_terms
    )
    
    return self._rank_and_limit_results(scored_results, max_results)
```

**Verify**:
```bash
pytest tests/unit/test_search.py -v
pytest tests/integration/test_api.py -v
```

**Time**: 3-4 hours  
**Impact**: HIGH (maintainability, testability)

---

## Priority 6: CODE ORGANIZATION - SRP VIOLATIONS

### Action 6.1: Split app/utils.py

**Current**: 258 lines with 5 different responsibilities

**Step 1**: Create directory structure
```bash
mkdir -p app/utils
touch app/utils/__init__.py
touch app/utils/markdown_utils.py
touch app/utils/filter_utils.py
touch app/utils/extract_utils.py
```

**Step 2**: Move markdown-related functions to `markdown_utils.py`
- `preprocess_rulebook_markdown()`
- `RuleIDRenderer` class
- `create_mistune_markdown()`

**Step 3**: Move filter-related functions to `filter_utils.py`
- `normalize_filter()`
- `build_document_order()`
- `filter_rules_for_extract()`

**Step 4**: Move extraction functions to `extract_utils.py`
- `format_extract_text()`
- File reading utilities

**Step 5**: Update `app/utils/__init__.py`
```python
"""Shared utilities for HEMA rulebook app"""

from app.utils.markdown_utils import (
    preprocess_rulebook_markdown,
    RuleIDRenderer,
    create_mistune_markdown,
)
from app.utils.filter_utils import (
    normalize_filter,
    build_document_order,
    filter_rules_for_extract,
)
from app.utils.extract_utils import format_extract_text

__all__ = [
    'preprocess_rulebook_markdown',
    'RuleIDRenderer',
    'create_mistune_markdown',
    'normalize_filter',
    'build_document_order',
    'filter_rules_for_extract',
    'format_extract_text',
]
```

**Step 6**: Update imports in other files
- `app/blueprints/search.py` - update imports
- `app/blueprints/rulebook.py` - update imports

**Verify**:
```bash
pytest tests/ -v
# All imports should work
# All tests should pass
```

**Time**: 4-5 hours  
**Impact**: HIGH (testability, maintainability)

---

### Action 6.2: Split parser.py Concerns

**Current**: 452 lines with mixed concerns

**Step 1**: Extract patterns into separate class
```python
# New file: qa_tools/tools/parser_patterns.py

class ParserPatterns:
    """All regex patterns for parsing"""
    
    def __init__(self):
        self.rule_id_pattern = re.compile(r'\*\*([A-Z]+(?:-[A-Z]+)*-[\d.]+)\*\*')
        self.anchor_pattern = re.compile(r'<span id="([^"]+)"></span>')
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
        self.comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
        self.reference_pattern = re.compile(r'\[([A-Z]+(?:-[A-Z]+)*(?:-\d+(?:\.\d+)*)?)\]')
```

**Step 2**: Extract hierarchy building into separate class
```python
# New file: qa_tools/tools/hierarchy_builder.py

from qa_tools.search_engine.search_utils import (
    get_rule_depth, get_rule_lineage
)

class HierarchyBuilder:
    """Build hierarchy metadata for rules"""
    
    def build_hierarchy(self, rules):
        """Compute all hierarchy relationships"""
        # Extract logic from _build_hierarchy_metadata
        pass
```

**Step 3**: Extract cross-references into separate class
```python
# New file: qa_tools/tools/cross_reference_builder.py

class CrossReferenceBuilder:
    """Build cross-reference index"""
    
    def __init__(self, reference_pattern):
        self.reference_pattern = reference_pattern
    
    def build_references(self, rules):
        """Build reference index"""
        # Extract logic from _build_cross_references
        pass
```

**Step 4**: Simplify RulebookParser
```python
# parser.py now orchestrates:

from parser_patterns import ParserPatterns
from hierarchy_builder import HierarchyBuilder
from cross_reference_builder import CrossReferenceBuilder

class RulebookParser:
    def __init__(self):
        self.patterns = ParserPatterns()
        self.hierarchy_builder = HierarchyBuilder()
        self.cross_ref_builder = CrossReferenceBuilder(self.patterns.reference_pattern)
        self.rules = []
    
    def parse_all(self):
        """Parse all markdown files"""
        # ... file discovery
        for md_file in md_files:
            self.parse_file(md_file)
        
        self.cross_ref_builder.build_references(self.rules)
        self.hierarchy_builder.build_hierarchy(self.rules)
        
        return {
            "rules": [asdict(rule) for rule in self.rules],
            "total_rules": len(self.rules),
            "documents": list(set(r.document for r in self.rules))
        }
```

**Verify**:
```bash
pytest tests/unit/test_parser.py -v
pytest tests/ -v  # All tests
```

**Time**: 6-8 hours  
**Impact**: HIGH (testability, maintainability)

---

## Priority 7: NAMING & TYPE HINTS

### Action 7.1: Fix Naming Inconsistency (variant vs formatum)

**Files to Update**:
1. `qa_tools/search_engine/search.py` - uses `formatum`
2. `qa_tools/search_engine/search_aliases.py` - uses both

**Search & Replace**:
```bash
grep -r "formatum" qa_tools/
# Replace with "variant"
```

**Specific Changes**:
- `_detect_formatum_in_query()` → `_detect_variant_in_query()`
- `formatum_filter` → `variant_filter` (in code comments)

**Verify**:
```bash
grep -r "formatum" qa_tools/  # Should return 0
pytest tests/ -v
```

**Time**: 1-2 hours  
**Impact**: MEDIUM (code clarity)

---

### Action 7.2: Add Missing Type Hints

**File**: `qa_tools/search_engine/search.py`

**Function**: `_detect_variant_in_query()` (around line 112)

**Current**:
```python
def _detect_variant_in_query(self, query: str):  # Missing return type
```

**Change to**:
```python
def _detect_variant_in_query(self, query: str) -> str:
```

**Similar fixes needed**:
- Check all scoring functions in search_aliases.py

**Verify**:
```bash
pytest tests/ -v
# Use mypy if available: mypy qa_tools/search_engine/search.py
```

**Time**: 30 min  
**Impact**: LOW (IDE support, documentation)

---

## Testing & Verification

### Full Test Suite
```bash
# Run all tests
pytest tests/ -v --tb=short

# Run with coverage
pytest tests/ -v --cov=app --cov=qa_tools --cov-report=html

# Run specific test files
pytest tests/unit/test_parser.py -v
pytest tests/unit/test_search.py -v
pytest tests/integration/test_api.py -v
```

### Manual Verification
```bash
# Check for unused imports
python -m pyflakes app/ qa_tools/

# Check for syntax errors
python -m py_compile app/*.py qa_tools/**/*.py

# Check imports are resolvable
python -c "from app import create_app; print('OK')"
python -c "from qa_tools.search_engine import AliasAwareSearch; print('OK')"
```

### Deployment Verification
```bash
# Build the search index
python qa_tools/tools/parser.py

# Test the app starts
python app.py &
sleep 2
curl http://localhost:5000/ | head -20
kill %1
```

---

## Timeline

| Phase | Tasks | Duration | Status |
|-------|-------|----------|--------|
| 2A-Critical | Add gunicorn | 30 min | TODO |
| 2A-Critical | Remove unused imports | 15 min | TODO |
| 2A-Critical | Delete redundant files | 15 min | TODO |
| 2A-Critical | Archive old docs | 10 min | TODO |
| **2A Total** | | **1-1.5 hours** | |
| 2B-High | Remove duplicate functions | 1.5 hours | TODO |
| 2B-High | Remove dead code | 30 min | TODO |
| 2B-High | Separate dev dependencies | 1.5 hours | TODO |
| **2B Total** | | **3.5 hours** | |
| 2C-Medium | Refactor parse_file() | 4 hours | TODO |
| 2C-Medium | Refactor search() | 4 hours | TODO |
| 2C-Medium | Split app/utils.py | 5 hours | TODO |
| 2C-Medium | Split parser.py | 8 hours | TODO |
| 2C-Medium | Fix naming | 2 hours | TODO |
| **2C Total** | | **23 hours** | |
| 2D-Low | Add type hints | 1 hour | TODO |
| 2D-Low | Organize test data | 3 hours | TODO |
| **2D Total** | | **4 hours** | |
| **GRAND TOTAL** | **20 items** | **31.5-32 hours** | |

**Team of 2**: ~16 days at 2 hours/day  
**Team of 1**: ~7 days at 4-5 hours/day  
**Recommended**: Complete 2A this week, 2B-2C next 2 weeks

---

**Document Status**: ✅ Ready for Implementation  
**Last Updated**: February 16, 2026
