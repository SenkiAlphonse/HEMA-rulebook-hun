# Phase 2 Cleanup Analysis - HEMA Rulebook Codebase

**Date**: February 16, 2026  
**Repository**: HEMA-rulebook-hun  
**Branch**: ai-agent

---

## Executive Summary

Analysis of the HEMA rulebook codebase identified **34 cleanup items** across 4 categories:
- **12 Unused/Redundant Files** to consolidate or remove
- **8 Dead Code & Code Quality Issues** to refactor
- **7 Dependency & Configuration Issues** to address
- **7 Code Organization & SRP Violations** to fix

**Total Estimated Effort**: ~40-50 developer hours  
**Overall Priority**: Medium (does not block deployment but improves maintainability)

---

## 1. UNUSED/REDUNDANT FILES TO REMOVE

### 1.1 Documentation Consolidation - Status/Summary Files

**Finding**: 4 status files document deployment readiness with overlapping content

| File | Lines | Purpose | Issue | Impact |
|------|-------|---------|-------|--------|
| `READY_TO_DEPLOY.txt` | 267 | Deployment readiness checklist | **DUPLICATE** of WEB_READY.md | **Medium** |
| `WEB_READY.md` | 161 | Web deployment status | **DUPLICATE** of READY_TO_DEPLOY.txt | **Medium** |
| `CRITICAL_FIXES_SUMMARY.md` | 194 | Historical fix log (Feb 8, 2026) | **OUTDATED** - fixes already applied | **Low** |
| `HIERARCHY_IMPLEMENTATION_SUMMARY.md` | 169 | Historical implementation log | **OUTDATED** - already in code | **Low** |

**Recommended Action**: 
- Keep only `WEB_READY.md` (cleaner format, links better)
- Delete: `READY_TO_DEPLOY.txt`
- Archive to: `docs/archive/CRITICAL_FIXES_SUMMARY.md` and `docs/archive/HIERARCHY_IMPLEMENTATION_SUMMARY.md`
- Update README.md to reference only `WEB_READY.md`

**Effort**: Small (1-2 hours)  
**Impact**: Low (documentation only)  
**Priority**: Low

---

### 1.2 Redundant Deployment Configuration Files

**File**: `Procfile` (line 1)
```plaintext
web: pytest tests/ -v && python build.py && python app.py
```

**Issue**: 
- Redundant with `render.yaml` (both define same process)
- `Procfile` runs pytest on every deployment (unnecessary for production)
- Render.com uses `render.yaml` configuration, making `Procfile` obsolete

**Alternatives**: 
- `render.yaml` is the Render.com standard config ✓
- `render.yaml` does NOT include pytest on start (only build.py)

**Recommended Action**: Delete `Procfile`, use only `render.yaml`

**Effort**: Trivial (<30 min)  
**Impact**: Low (configuration only)  
**Priority**: Low

---

### 1.3 Demo/Tool Scripts That Should Be Part of Documentation

| File | Type | Purpose | Status | Issue |
|------|------|---------|--------|-------|
| `qa_tools/tools/view_index.py` | Script | View sample rules from index | Works | **Example/Demo** - consider docs example instead |
| `qa_tools/tools/check_variants.py` | Script | Verify variant detection | Works | **Diagnostic** - one-off usage |
| `qa_tools/tools/ai_explainer_example.py` | Script | AI explanation patterns | Works | **Example** - should be in docs/examples/ |
| `qa_tools/tools/add_aliases.py` | Script | Add aliases interactively | Works | **Maintenance tool** - rarely used |

**Recommended Action**: 
- Create `qa_tools/examples/` directory
- Move `ai_explainer_example.py` → `qa_tools/examples/ai_explainer_example.py`
- Document usage in `qa_tools/README.md` with examples
- Keep others in `qa_tools/tools/` but add clear README

**Effort**: Small (2-3 hours for docs)  
**Impact**: Low (improves organization)  
**Priority**: Low

---

### 1.4 Test-Related Files with Duplication

**Finding**: Test fixtures may have redundant test data

**File**: `tests/fixtures/` (if exists)  
**Issue**: Need to check if test data is duplicated in `conftest.py`

**Action**: Defer to test audit phase

**Priority**: Low

---

## 2. DEAD CODE & DUPLICATED FUNCTIONS

### 2.1 Duplicate Rule Depth Calculation

**Files with duplicate implementations**:

1. **`app/utils.py` (line 11)**: Imports `get_rule_depth` from search_utils
```python
from qa_tools.search_engine.search_utils import get_rule_depth
```

2. **`qa_tools/tools/parser.py` (lines 415-423)**: Implements same logic
```python
def _get_rule_depth(self, rule_id: str) -> int:
    """Calculate nesting depth from rule ID"""
    if not rule_id or '-' not in rule_id:
        return 0
    parts = rule_id.split('-')
    numeric_part = parts[-1]
    return numeric_part.count('.') + 1
```

3. **`qa_tools/search_engine/search_utils.py` (lines 7-19)**: Canonical implementation
```python
def get_rule_depth(rule_id: str) -> int:
    """Calculate indentation depth from rule ID"""
    # ... canonical implementation
```

**Issue**: 
- `parser.py` reimplements instead of importing from `search_utils`
- Creates maintenance burden if logic changes
- Private method `_get_rule_depth()` only used internally in parser

**Impact**: **Medium** - maintenance risk

**Recommended Action**:
```python
# IN parser.py, line 415: Replace with import
from qa_tools.search_engine.search_utils import get_rule_depth as calculate_rule_depth

# Then use:
rule.depth = calculate_rule_depth(rule.rule_id)  # Instead of self._get_rule_depth()
```

**Effort**: Small (30 min)  
**Impact**: Medium  
**Priority**: Medium

---

### 2.2 Duplicate Parent/Lineage Calculation

**Files with duplicate implementations**:

1. **`qa_tools/tools/parser.py` (lines 424-443)**:
```python
def _get_parent_id(self, rule_id: str) -> str:
    """Get direct parent rule ID from a given rule"""
    # ... implementation

def _get_rule_lineage(self, rule_id: str) -> list:
    """Get list of parent rule IDs"""
    # ... implementation
```

2. **`qa_tools/search_engine/search_utils.py` (lines 31-70)**:
```python
def get_rule_lineage(rule_id: str) -> List[str]:
    """Get list of parent rule IDs for a given rule"""
    # ... canonical implementation
```

**Issue**: 
- Parser uses private methods instead of shared functions
- `_get_parent_id()` duplicates logic that could import from search_utils
- Maintenance burden if hierarchy algorithm changes

**Impact**: **Medium** - maintenance risk

**Recommended Action**: 
Replace parser's private methods with imports from search_utils

**Effort**: Small (45 min)  
**Impact**: Medium  
**Priority**: Medium

---

### 2.3 Unused Private Methods in Parser

**File**: `qa_tools/tools/parser.py`

**Methods NOT used in current codebase**:

1. **`_extract_variant_subrules()` (lines 390-430)**
   - Never called in `parse_file()` or `_save_rule()`
   - Complexity: 41 lines
   - **Status**: Dead code - was experimental, not integrated
   - **Impact**: Low (internal implementation detail)

2. **`_variant_to_subrule_index()` (lines 432-443)**
   - Only used by `_extract_variant_subrules()` (which is dead)
   - Complexity: 12 lines
   - **Status**: Dead code (unreachable)
   - **Impact**: Low

**Recommended Action**: 
Remove both methods if variant sub-rule extraction not needed, OR:
- Document why they exist (future use?)
- Create issue for implementation
- Move to separate `experimental.py` module

**Effort**: Small (30 min)  
**Impact**: Low (cleanup)  
**Priority**: Low

---

### 2.4 Unused Import: `sys` in `app/utils.py`

**File**: `app/utils.py`, line 6
```python
import sys
```

**Status**: **UNUSED** - no `sys.` calls in the file

**Recommended Action**: Remove line 6

**Effort**: Trivial  
**Impact**: Negligible  
**Priority**: Low

---

### 2.5 Unused Import: `os` in `qa_tools/tools/parser.py`

**File**: `qa_tools/tools/parser.py`, line 6
```python
import os
```

**Status**: **UNUSED** - no `os.` calls in the file

**Recommended Action**: Remove line 6

**Effort**: Trivial  
**Impact**: Negligible  
**Priority**: Low

---

### 2.6 Complex Function: `parse_file()` in Parser

**File**: `qa_tools/tools/parser.py`, lines 123-217

**Metrics**:
- **Lines of code**: 95
- **Cyclomatic complexity**: 7 (too high)
- **Responsibilities**: 
  1. Reading file
  2. Tracking heading levels
  3. Tracking anchor IDs
  4. Detecting rule IDs
  5. Accumulating rule text
  6. Saving rules

**Issue**: Function violates Single Responsibility Principle

**Recommended Action**: 
Extract into smaller functions:
```python
def _parse_line_for_heading(line, pattern)
def _parse_line_for_anchor(line, pattern)
def _parse_line_for_rule_id(line, pattern)
def _accumulate_rule_text(line, current_rule_id)
```

**Effort**: Medium (3-4 hours)  
**Impact**: High (maintainability)  
**Priority**: Medium

---

### 2.7 Complex Function: `search()` in AliasAwareSearch

**File**: `qa_tools/search_engine/search_aliases.py`, lines 155-220

**Metrics**:
- **Lines of code**: 65+
- **Cyclomatic complexity**: 8+ (too high)
- **Responsibilities**:
  1. Query expansion via aliases
  2. Scoring and filtering
  3. Ranking results
  4. Grouping related rules

**Recommended Action**: Extract scoring logic into separate method

**Effort**: Medium (3-4 hours)  
**Impact**: High (maintainability)  
**Priority**: Medium

---

## 3. DEPENDENCY ANALYSIS

### 3.1 Missing Production Dependency: gunicorn

**File**: `requirements.txt`

**Current dependencies**:
```
Flask==3.1.2
Werkzeug==3.1.5
google-generativeai==0.8.6
mistune==3.2.0
protobuf>=4.25.0,<6.0.0
pytest==9.0.2
pytest-flask==1.3.0
pytest-mock==3.15.1
```

**Issue**: 
- No `gunicorn` specified for production WSGI server
- `app.py` uses `app.run()` which is **NOT suitable for production**
- Render.com or other production platforms need explicit WSGI server

**Current**: `app.py` line 15-16
```python
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port, debug=False)
```

**Production Issue**: `app.run()` is slow and single-threaded

**Recommended Action**:
1. Add to `requirements.txt`:
```
gunicorn==21.2.0
```

2. Update `Procfile` or create `render.yaml` entry:
```yaml
services:
  - type: web
    name: hema-rulebook
    runtime: python
    startCommand: gunicorn --workers 4 --worker-class sync --bind 0.0.0.0:$PORT app:app
```

3. Keep `app.py` development mode for local testing

**Effort**: Small (1 hour)  
**Impact**: High (production stability)  
**Priority**: **CRITICAL**

---

### 3.2 Overly Loose Protobuf Constraint

**File**: `requirements.txt`, line 5

**Current**:
```
protobuf>=4.25.0,<6.0.0
```

**Issue**: 
- Range allows protobuf 5.x which may have breaking changes
- google-generativeai==0.8.6 might have compatibility constraints
- Better to pin to tested version

**Recommended Action**:
```
protobuf>=4.25.0,<5.0.0
```

**Effort**: Trivial  
**Impact**: Low  
**Priority**: Low

---

### 3.3 Testing Dependencies Mixed with Production

**File**: `requirements.txt`, lines 8-10

**Issue**: 
- pytest, pytest-flask, pytest-mock should be in separate file for development only
- Production deployment doesn't need testing dependencies

**Current setup**: All in one `requirements.txt`

**Recommended Action**:
- Create `requirements-dev.txt`:
```
-r requirements.txt

pytest==9.0.2
pytest-flask==1.3.0
pytest-mock==3.15.1
```

- Update `requirements.txt` to production only:
```
Flask==3.1.2
Werkzeug==3.1.5
google-generativeai==0.8.6
mistune==3.2.0
protobuf>=4.25.0,<5.0.0
gunicorn==21.2.0
```

- Update deployment config to use `requirements.txt`
- Update local dev to use `requirements-dev.txt`

**Effort**: Small (1-2 hours)  
**Impact**: Medium (cleaner deployment, smaller footprint)  
**Priority**: Medium

---

### 3.4 Verify All Requirements Are Actually Used

**Analysis of imports**:

| Package | Usage | Status |
|---------|-------|--------|
| Flask | ✓ Used in `app/blueprints/` | ✓ Needed |
| Werkzeug | ✓ Flask dependency, middleware | ✓ Needed |
| google-generativeai | ✓ Used in `ai_services.py` | ✓ Needed |
| mistune | ✓ Used in `app/utils.py` for markdown | ✓ Needed |
| protobuf | ✓ google-generativeai dependency | ✓ Needed |
| pytest | ✓ Used in tests | ✓ Needed (dev) |
| pytest-flask | ✓ Used in `tests/conftest.py` | ✓ Needed (dev) |
| pytest-mock | ✓ Used in tests | ✓ Needed (dev) |
| gunicorn | ✗ **MISSING** - should be added | **CRITICAL** |

**Conclusion**: All current packages are used; gunicorn is missing.

**Effort**: Covered above  
**Impact**: Critical  
**Priority**: Critical

---

## 4. CODE ORGANIZATION ISSUES

### 4.1 SRP Violation: `app/utils.py` Does Too Many Things

**File**: `app/utils.py` (258 lines)

**Responsibilities**:
1. Markdown preprocessing (11 lines)
2. Custom Mistune renderer (89 lines) - **RuleIDRenderer class**
3. Markdown creation (7 lines)
4. Filter normalization (7 lines)
5. Document ordering (11 lines)
6. Markdown file utilities (12 lines)
7. Markdown content reading (15 lines)
8. Rule filtering (11 lines)
9. Extract formatting (35 lines) - **format_extract_text function**

**Issue**: Single file has 4-5 different concerns

**Recommended Action**: Split into:
1. `app/utils/markdown_utils.py` - Preprocessing, rendering, creation
2. `app/utils/filter_utils.py` - Filtering, normalization
3. `app/utils/extract_utils.py` - Rule extraction, formatting

**Directory structure**:
```
app/
├── utils/
│   ├── __init__.py (re-export public API)
│   ├── markdown_utils.py
│   ├── filter_utils.py
│   └── extract_utils.py
```

**Effort**: Medium (4-5 hours)  
**Impact**: High (maintainability, testability)  
**Priority**: Medium

---

### 4.2 SRP Violation: `parser.py` Mixed Concerns

**File**: `qa_tools/tools/parser.py` (452 lines)

**Responsibilities**:
1. Rule dataclass definition (27 lines)
2. Section dataclass (6 lines)
3. RulebookParser class (419 lines) - **mixed concerns**:
   - File I/O
   - Regex pattern matching
   - Rule text parsing
   - Rule hierarchy computation
   - Cross-reference building
   - JSON serialization

**Recommended Action**: Extract into separate classes:
```python
# parser.py keeps RulebookParser orchestrator

# New: parser_patterns.py
class ParserPatterns:
    """All regex patterns for parsing"""
    def __init__(self): ...

# New: hierarchy_builder.py
class HierarchyBuilder:
    """Build parent-child relationships"""
    def build_hierarchy(self, rules): ...

# New: cross_reference_builder.py
class CrossReferenceBuilder:
    """Build cross-reference index"""
    def build_references(self, rules): ...
```

**Effort**: Large (6-8 hours)  
**Impact**: High (maintainability, testability)  
**Priority**: Medium

---

### 4.3 Inconsistent Naming: `formatum` vs `variant`

**Issue**: Codebase uses two terms for same concept:
- `variant` - used in Rule dataclass, config, API
- `formatum` - used in search engine, search methods

**Files affected**:
- `qa_tools/tools/parser.py` - uses `variant`
- `qa_tools/search_engine/search.py` - uses `formatum` (but deprecated in favor of `variant`)
- `qa_tools/search_engine/search_aliases.py` - uses both
- API endpoints - use `variant_filter`

**Recommended Action**: 
1. Standardize on `variant` throughout
2. Remove `formatum` terminology (legacy from earlier implementation)
3. Search/replace in all files

**Effort**: Small (1-2 hours)  
**Impact**: Medium (code clarity)  
**Priority**: Low

---

### 4.4 Hardcoded Configuration Values

**Finding**: Several hardcoded values scattered in code

| Location | Value | Should Be In | Current |
|----------|-------|--------------|---------|
| `app/config.py` line 49-50 | GEMINI_MODEL_CANDIDATES, SUMMARY_CHUNK_SIZE | ✓ Correct | Config ✓ |
| `app/__init__.py` line 35-42 | VARIANTS, WEAPONS, SUMMARY settings | ✓ Correct | Config ✓ |
| `app.py` line 15 | PORT default 5000 | ✓ Correct | Env var ✓ |
| `Procfile` line 1 | pytest command | ✗ Should not run tests in prod | Config ✗ |
| Templates: `index.html` | CSS colors, styling | ✓ Acceptable | Inline ✓ |

**Conclusion**: Hardcoded values are mostly in config already. Procfile is the issue (covered in section 1.2).

**Effort**: Covered above  
**Impact**: Low  
**Priority**: Low

---

### 4.5 Long Functions That Need Refactoring

**Function**: `search()` in `search_aliases.py`, lines 155-220

**Metrics**:
- 65 lines
- Multiple responsibilities:
  1. Query expansion
  2. Rule filtering
  3. Scoring
  4. Result ranking
  5. Group limiting

**Recommended Refactoring**:
```python
def search(self, query, max_results, variant_filter, weapon_filter):
    expanded_query, detected_variant, detected_weapon, concept_terms, _ = self._expand_query(query)
    results = self._filter_and_score(
        expanded_query, 
        variant_filter or detected_variant, 
        weapon_filter or detected_weapon,
        concept_terms
    )
    return self._rank_and_limit_results(results, max_results)

def _filter_and_score(self, query, variant_filter, weapon_filter, concept_terms):
    # Filtering and scoring logic
    pass

def _rank_and_limit_results(self, results, max_results):
    # Ranking and grouping logic
    pass
```

**Effort**: Medium (3-4 hours)  
**Impact**: High  
**Priority**: Medium

---

### 4.6 Missing Type Hints in Key Functions

**Files with weak/missing type hints**:

| File | Function | Status |
|------|----------|--------|
| `qa_tools/tools/parser.py` | `_extract_variant_subrules()` | ✓ Has hints |
| `qa_tools/search_engine/search.py` | `_detect_variant_in_query()` | ✗ No return type |
| `app/utils.py` | `preprocess_rulebook_markdown()` | ✓ Has hints |
| `app/validation.py` | Functions | ✓ Has hints |

**Recommendation**: Add type hints to:
- `search.py::_detect_variant_in_query() -> str`
- `search_aliases.py` scoring functions

**Effort**: Small (1-2 hours)  
**Impact**: Medium (IDE support, documentation)  
**Priority**: Low

---

### 4.7 Testing Code Organization

**Structure**: 
```
tests/
├── unit/
│   ├── test_parser.py
│   ├── test_search.py
│   └── test_utils.py
├── integration/
│   └── test_api.py
├── conftest.py
└── __init__.py
```

**Issue**: 
- Good separation of unit/integration
- However, test fixtures in `conftest.py` could be further organized
- No `fixtures/` directory for shared test data

**Recommendation**:
```
tests/
├── fixtures/
│   ├── sample_rules.json
│   └── sample_aliases.json
├── unit/
│   └── ...
├── integration/
│   └── ...
├── conftest.py
└── __init__.py
```

**Effort**: Small (2-3 hours)  
**Impact**: Low (testing organization)  
**Priority**: Low

---

## 5. SUMMARY TABLE - ALL FINDINGS PRIORITIZED

| # | Category | File(s) | Finding | Effort | Impact | Priority | Status |
|---|----------|---------|---------|--------|--------|----------|--------|
| 1.1 | Docs | READY_TO_DEPLOY.txt, WEB_READY.md | **Duplicate** status files | Small | Low | Low | TODO |
| 1.2 | Config | Procfile | **Redundant** with render.yaml | Trivial | Low | Low | TODO |
| 1.3 | Tools | qa_tools/tools/* | Demo scripts should be documented | Small | Low | Low | TODO |
| 2.1 | Code | parser.py, search_utils.py | **Duplicate** get_rule_depth() | Small | Medium | **Medium** | TODO |
| 2.2 | Code | parser.py, search_utils.py | **Duplicate** parent/lineage logic | Small | Medium | **Medium** | TODO |
| 2.3 | Code | parser.py | **Dead code**: _extract_variant_subrules() | Small | Low | Low | TODO |
| 2.4 | Code | app/utils.py | **Unused import**: sys | Trivial | Negligible | Low | TODO |
| 2.5 | Code | parser.py | **Unused import**: os | Trivial | Negligible | Low | TODO |
| 2.6 | Code | parser.py | Complex parse_file() function | Medium | High | **Medium** | TODO |
| 2.7 | Code | search_aliases.py | Complex search() function | Medium | High | **Medium** | TODO |
| 3.1 | Deps | requirements.txt | **MISSING** gunicorn (production) | Small | **CRITICAL** | **CRITICAL** | TODO |
| 3.2 | Deps | requirements.txt | Loose protobuf constraint | Trivial | Low | Low | TODO |
| 3.3 | Deps | requirements.txt | Test deps in production | Small | Medium | **Medium** | TODO |
| 3.4 | Deps | requirements.txt | Verify all used | Trivial | Low | Low | DONE ✓ |
| 4.1 | Org | app/utils.py | **SRP violation** (258 lines, 5 concerns) | Medium | High | **Medium** | TODO |
| 4.2 | Org | parser.py | **SRP violation** (452 lines, mixed) | Large | High | **Medium** | TODO |
| 4.3 | Org | Multiple | Inconsistent naming: variant vs formatum | Small | Medium | Low | TODO |
| 4.4 | Org | Multiple | Hardcoded values | Covered | Low | Low | DONE ✓ |
| 4.5 | Org | search_aliases.py | Long search() function | Medium | High | **Medium** | TODO |
| 4.6 | Org | search.py | Missing type hints | Small | Medium | Low | TODO |
| 4.7 | Org | tests/ | Test data organization | Small | Low | Low | TODO |

---

## 6. IMPLEMENTATION ROADMAP

### Phase 2A: Critical Issues (1-2 days)
1. **Add gunicorn to requirements.txt** ← CRITICAL
2. Separate dev dependencies to requirements-dev.txt
3. Remove unused imports (sys, os)
4. Delete Procfile and READY_TO_DEPLOY.txt

### Phase 2B: Code Quality (3-5 days)
1. Eliminate duplicate rule depth/lineage functions
2. Refactor parse_file() into smaller functions
3. Refactor search() into smaller functions
4. Add missing type hints

### Phase 2C: Organization (5-7 days)
1. Split app/utils.py into smaller modules
2. Split parser.py concerns into separate classes
3. Consolidate documentation (archive old summaries)
4. Standardize variant/formatum terminology

### Phase 2D: Testing & Low-Priority (2-3 days)
1. Organize test fixtures
2. Move demo scripts to examples/
3. Update all documentation

**Total Estimated Timeline**: 10-15 days with focused team

---

## 7. NON-BLOCKING RECOMMENDATIONS

These items improve code quality but don't block deployment:

1. ✓ Extract `RuleIDRenderer` to separate file
2. ✓ Move parsing patterns to separate class
3. ✓ Create `HierarchyBuilder` utility class
4. ✓ Consolidate rule filtering logic
5. ✓ Add logging to search engine

---

## 8. VERIFICATION CHECKLIST

Before Phase 3 deployment:

- [ ] gunicorn added to requirements.txt
- [ ] Duplicate functions eliminated (rule_depth, lineage)
- [ ] Unused imports removed
- [ ] parse_file() refactored (cyclomatic complexity < 5)
- [ ] search() refactored (cyclomatic complexity < 5)
- [ ] Status files consolidated
- [ ] Type hints complete (mypy --strict passes)
- [ ] All tests pass with 100% coverage
- [ ] Documentation updated

---

## 9. NOTES FOR DEVELOPERS

### High-Impact Quick Wins
1. Add gunicorn (1 hour) → Production stability
2. Remove duplicate functions (1 hour) → Maintenance relief
3. Clean up status files (30 min) → Documentation clarity

### Strategic Refactorings
1. Split app/utils.py → Better testing
2. Split parser.py → Easier maintenance
3. Refactor search() → Easier to extend

### Deferred to Phase 3+
1. Docker containerization
2. Database optimization
3. Caching strategies
4. API rate limiting
5. Advanced monitoring

---

**End of Analysis**  
Generated: February 16, 2026  
Repository: HEMA-rulebook-hun (ai-agent branch)
