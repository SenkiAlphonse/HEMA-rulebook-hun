# Phase 2 Cleanup - Quick Reference

**Total Issues Found**: 34 items across 4 categories

---

## 🚨 CRITICAL ISSUES (Fix Before Deployment)

### 1. MISSING: gunicorn in requirements.txt
- **Why**: Production deployment needs proper WSGI server, not `app.run()`
- **Fix**: Add `gunicorn==21.2.0` to requirements.txt
- **Time**: 1 hour
- **Impact**: HIGH - affects production stability

---

## ⚠️ HIGH-PRIORITY ISSUES (Fix in Phase 2A)

### 2. Duplicate Functions - Code Duplication
**Files**: `parser.py` and `search_utils.py`
- `get_rule_depth()` - duplicated (19 lines)
- `get_rule_lineage()` - duplicated (19 lines)  
- `_get_parent_id()` - duplicated (13 lines)

**Fix**: Replace private methods in parser with imports  
**Time**: 1.5 hours  
**Impact**: MEDIUM - maintenance burden

### 3. Dead Code - Unused Methods
**File**: `qa_tools/tools/parser.py`
- `_extract_variant_subrules()` (41 lines) - never called
- `_variant_to_subrule_index()` (12 lines) - only called by dead code

**Fix**: Remove or archive to experimental/  
**Time**: 30 min  
**Impact**: LOW - cleanup only

### 4. Unused Imports
- `sys` in `app/utils.py` (line 6)
- `os` in `qa_tools/tools/parser.py` (line 6)

**Fix**: Delete 2 lines  
**Time**: 5 min  
**Impact**: Negligible

---

## 📋 MEDIUM-PRIORITY ISSUES (Fix in Phase 2B)

### 5. Separate Dev Dependencies
**Current**: All packages in `requirements.txt`  
**Issue**: Production doesn't need pytest, pytest-flask, pytest-mock

**Fix**: 
- Create `requirements-dev.txt`
- Move test packages there
- Update deployment to use `requirements.txt`

**Time**: 1.5 hours  
**Impact**: MEDIUM - cleaner deployments

### 6. Complex Functions Need Refactoring
**Files**: 
- `parser.py::parse_file()` - 95 lines, cyclomatic complexity 7
- `search_aliases.py::search()` - 65 lines, complexity 8

**Fix**: Extract into smaller functions  
**Time**: 6-8 hours (both)  
**Impact**: HIGH - maintainability

### 7. SRP Violations - Single Responsibility Principle
**File**: `app/utils.py` (258 lines)
- Markdown preprocessing, rendering, creation
- Filter normalization
- Document ordering
- Rule extraction and formatting

**Fix**: Split into 3 modules:
- `app/utils/markdown_utils.py`
- `app/utils/filter_utils.py`
- `app/utils/extract_utils.py`

**Time**: 4-5 hours  
**Impact**: HIGH - testability, maintainability

**File**: `qa_tools/tools/parser.py` (452 lines)
- Parsing, hierarchy building, cross-references all mixed

**Fix**: Extract into separate classes  
**Time**: 6-8 hours  
**Impact**: HIGH - testability, maintainability

---

## 🟡 LOW-PRIORITY ISSUES (Phase 2C & Beyond)

### 8. Documentation Consolidation
- `READY_TO_DEPLOY.txt` (267 lines) - **DUPLICATE** of WEB_READY.md
- `CRITICAL_FIXES_SUMMARY.md` (194 lines) - outdated
- `HIERARCHY_IMPLEMENTATION_SUMMARY.md` (169 lines) - outdated

**Fix**: 
- Keep WEB_READY.md only
- Archive others to `docs/archive/`
- Update README.md references

**Time**: 1-2 hours  
**Impact**: LOW - documentation only

### 9. Remove Redundant Config
**File**: `Procfile` (1 line)

**Issue**: Redundant with `render.yaml`, includes unnecessary pytest  

**Fix**: Delete Procfile  

**Time**: 5 min  

**Impact**: LOW - config only

### 10. Organize Demo Scripts
**Files in `qa_tools/tools/`**:
- `view_index.py` - example script
- `check_variants.py` - diagnostic script
- `ai_explainer_example.py` - example script
- `add_aliases.py` - maintenance tool

**Fix**: Move examples to `qa_tools/examples/`, document usage  

**Time**: 2-3 hours  

**Impact**: LOW - organization only

### 11. Fix Naming Inconsistency
**Terms used**: `variant` vs `formatum` (same concept)

**Files affected**: search.py, search_aliases.py  

**Fix**: Standardize on `variant` throughout  

**Time**: 1-2 hours  

**Impact**: MEDIUM - code clarity

### 12. Add Missing Type Hints
**File**: `search.py::_detect_variant_in_query()` missing return type

**Fix**: Add `-> str` return type  

**Time**: 30 min  

**Impact**: LOW - IDE support

### 13. Organize Test Data
**Issue**: No `tests/fixtures/` directory for shared data

**Fix**: Create fixtures directory, move sample data  

**Time**: 2-3 hours  

**Impact**: LOW - testing organization

---

## 📊 EFFORT BREAKDOWN

| Priority | Count | Effort | Total Hours |
|----------|-------|--------|-------------|
| 🚨 CRITICAL | 1 | 1h | 1 |
| ⚠️ HIGH | 7 | 1-8h each | 20-30 |
| 🟡 LOW | 5 | 0.5-3h each | 10-15 |
| **TOTAL** | **20** | - | **31-46 hours** |

---

## 🎯 IMPLEMENTATION PHASES

### Phase 2A: CRITICAL (Must Fix Before Production)
- [ ] Add gunicorn to requirements.txt
- [ ] Verify all tests pass
- [ ] Test deployment with gunicorn

**Time**: 2-3 hours  
**Blocking**: YES - affects production

### Phase 2B: HIGH-PRIORITY (Quality Improvements)
- [ ] Remove duplicate functions
- [ ] Remove unused imports
- [ ] Separate dev dependencies
- [ ] Refactor parse_file() and search()

**Time**: 8-10 hours  
**Blocking**: NO - improves code quality

### Phase 2C: MEDIUM-PRIORITY (Organization)
- [ ] Split app/utils.py
- [ ] Split parser.py concerns
- [ ] Fix naming (variant/formatum)
- [ ] Add type hints

**Time**: 10-15 hours  
**Blocking**: NO - improves maintainability

### Phase 2D: LOW-PRIORITY (Nice to Have)
- [ ] Consolidate docs
- [ ] Remove Procfile
- [ ] Organize demo scripts
- [ ] Organize test data

**Time**: 6-10 hours  
**Blocking**: NO - cleanup only

---

## 📝 FULL DETAILS

See `PHASE_2_CLEANUP_ANALYSIS.md` for complete analysis with:
- Line numbers and file locations
- Code examples
- Detailed impact assessment
- Verification checklist

---

## ✅ QUICK START

**What to fix TODAY**:
1. Add gunicorn to requirements.txt (5 min)
2. Remove unused imports (5 min)
3. Delete Procfile (5 min)

**Total**: 15 minutes → Production-ready

**What to plan for NEXT WEEK**:
- Remove duplicate functions (1.5h)
- Separate dev dependencies (1.5h)
- Refactor parse_file() (4-5h)
- Refactor search() (4-5h)

**Total**: ~12 hours focused work

---

Generated: February 16, 2026  
Analysis Status: ✅ Complete  
Ready for Phase 2 Implementation
