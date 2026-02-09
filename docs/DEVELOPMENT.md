# Development Guide

Complete guide for developers contributing to the HEMA Rulebook Q&A System.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Code Conventions](#code-conventions)
4. [Adding Features](#adding-features)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Logging](#logging)
8. [Environment Variables](#environment-variables)
9. [Git Workflow](#git-workflow)
10. [IDE Setup](#ide-setup)

---

## Getting Started

### Prerequisites

- Python 3.14+
- pip (Python package manager)
- Git
- VS Code (recommended) or any text editor

### Initial Setup

**1. Clone the repository**
```bash
git clone https://github.com/SenkiAlphonse/HEMA-rulebook-hun.git
cd HEMA-rulebook-hun
```

**2. Create a virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Verify installation**
```bash
python -c "import flask; import pytest; print('✓ All packages installed')"
```

**5. Run tests to verify setup**
```bash
pytest tests/ -v
# Expected: 59 passed
```

**6. Start development server**
```bash
python app.py
# Server runs on http://localhost:5000
```

---

## Project Structure

### Top-Level Organization

```
HEMA-rulebook-hun/
│
├── app/                           # Flask application
│   ├── __init__.py               # Flask app factory
│   ├── config.py                 # Configuration
│   ├── blueprints/               # Route blueprints
│   │   ├── search.py             # Search endpoints
│   │   ├── ai_services.py        # AI endpoints
│   │   └── rulebook.py           # Rulebook endpoints
│   └── utils/                    # Utility functions
│       ├── validation.py         # Input validation
│       ├── parsing.py            # Response formatting
│       ├── ai_helpers.py         # AI service helpers
│       └── logging.py            # Logging utilities
│
├── qa-tools/                     # Search engine & indexing
│   ├── search_aliases.py         # AliasAwareSearch class
│   ├── parser.py                 # Markdown parser
│   ├── aliases.json              # Alias mappings
│   ├── rules_index.json          # Parsed rules (487)
│   ├── demo_search.py            # Interactive demo
│   └── view_index.py             # Index viewer
│
├── tests/                        # Test suite (59 tests)
│   ├── unit/                     # Unit tests (41 tests)
│   │   ├── test_search.py        # Search engine tests
│   │   ├── test_parser.py        # Parser tests
│   │   └── test_utils.py         # Utility tests
│   ├── integration/              # Integration tests (13 tests)
│   │   └── test_api.py           # API endpoint tests
│   └── conftest.py               # pytest fixtures
│
├── templates/                    # HTML templates
│   └── index.html                # Web UI
│
├── docs/                         # Documentation
│   ├── INDEX.md                  # Nav hub (start here!)
│   ├── API.md                    # API reference
│   ├── ARCHITECTURE.md           # System design
│   ├── DEVELOPMENT.md            # You are here!
│   └── SEARCH_ENGINE.md          # Algorithm details
│
├── fuggelek/                     # Appendices
│   ├── 01-szojegyzek.md          # Glossary
│   ├── 02-elsobbseg.md           # Priority rules
│   └── [other weapons].md        # Rapier, etc.
│
├── [rulebook chapters]           # Markdown rulebook
│   ├── 01-altalanos.md           # Introduction
│   ├── 03-felszereles.md         # Equipment
│   ├── 04-altalanos.md           # General rules
│   ├── 05-hosszukard.md          # Longsword rules
│   ├── 05.a-hosszukard-VOR.md    # VOR variant
│   ├── 05.b-hosszukard-COMBAT.md # COMBAT variant
│   └── 05.c-hosszukard-AFTERBLOW.md # AFTERBLOW variant
│
├── requirements.txt              # Python dependencies
├── Procfile                      # Render deployment config
├── render.yaml                   # Render.com setup
├── app.py                        # Application entry point
└── README.md                     # Project overview
```

### Key Directories Explained

**app/** - Flask application code (production code)
- Must have type hints
- Must be tested (via tests/)
- Must follow code conventions (see below)

**qa-tools/** - Search engine and indexing logic
- Core business logic
- Indexes are regenerated when markdown files change
- Separate from Flask (can be used standalone)

**tests/** - Automated test suite
- 59 tests total (100% passing)
- Run before every commit
- Add tests for new features

**docs/** - Developer and user documentation
- Update when changing features/API
- Markdown format
- Cross-referenced for navigation

---

## Code Conventions

### Python Style Guide

Follow **PEP 8** with these preferences:

**1. Naming**
```python
# Functions and variables: snake_case
def search_rules(query):
    rule_count = 0
    return rule_count

# Constants: UPPER_SNAKE_CASE
MAX_QUERY_LENGTH = 500
DEFAULT_THRESHOLD = 0.5

# Classes: PascalCase
class AliasAwareSearch:
    pass
```

**2. Type Hints** (REQUIRED for all new code)
```python
from typing import List, Dict, Any, Optional, Tuple

def search_rules(
    query: str,
    threshold: float = 0.5,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search rulebook for matching rules.
    
    Args:
        query: Search query (3-500 chars)
        threshold: Relevance threshold (0.0-1.0)
        limit: Max results (1-50)
    
    Returns:
        List of matching rule dicts, sorted by score
    """
    results: List[Dict[str, Any]] = []
    # ... implementation
    return results
```

**3. Docstrings** (REQUIRED for all public functions/classes)
```python
def extract_rule_by_id(rule_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific rule by its ID.
    
    Args:
        rule_id: Rule identifier (e.g., "GEN-1.2.3")
    
    Returns:
        Rule dict if found, None otherwise
        
    Raises:
        ValueError: If rule_id format is invalid
    
    Example:
        >>> rule = extract_rule_by_id("GEN-1.2.3")
        >>> rule['title']
        'Valid Target Areas'
    """
```

**4. Line Length**
- Maximum: 100 characters per line
- Exceptions: URLs, very long strings

**5. Imports**
```python
# Order: standard lib, third-party, local
import os
import json
from typing import List, Dict, Any

import flask
from flask import request, jsonify

from qa_tools.search_aliases import AliasAwareSearch
from app.utils.validation import validate_query
```

**6. Blank Lines**
```python
# 2 blank lines between top-level functions/classes
def function1():
    pass


def function2():
    pass


class MyClass:
    # 1 blank line between methods
    def method1(self):
        pass
    
    def method2(self):
        pass
```

---

## Adding Features

### Example: Add a new search endpoint

**1. Create endpoint in blueprint**

Edit `app/blueprints/search.py`:

```python
from typing import Dict, Any
from flask import request, jsonify

@search_bp.route('/api/search/by-author', methods=['POST'])
def search_by_author() -> Dict[str, Any]:
    """Search rules by rule author.
    
    Request body:
        {"author": "John Doe", "limit": 10}
    
    Response:
        {"success": true, "results": [...]}
    """
    data = request.get_json() or {}
    author = data.get('author', '')
    limit = data.get('limit', 10)
    
    # Validate input
    if not author or len(author) < 2:
        return jsonify({
            "success": False,
            "error": "Author name too short"
        }), 400
    
    if not (1 <= limit <= 50):
        return jsonify({
            "success": False,
            "error": "Limit must be between 1-50"
        }), 400
    
    # Business logic
    results = search_engine.find_by_author(author, limit)
    
    # Return response
    return jsonify({
        "success": True,
        "author": author,
        "results": results,
        "result_count": len(results)
    }), 200
```

**2. Add business logic to search engine**

Edit `qa-tools/search_aliases.py`:

```python
def find_by_author(self, author: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Find rules by author (if available in metadata)."""
    results = []
    for rule in self.rules.values():
        # Check if author matches (case-insensitive)
        rule_author = rule.get('author', '').lower()
        if author.lower() in rule_author:
            results.append(rule)
            if len(results) >= limit:
                break
    
    return results
```

**3. Write unit tests**

Create `tests/unit/test_search_by_author.py`:

```python
import pytest
from qa_tools.search_aliases import AliasAwareSearch

@pytest.fixture
def search_engine_with_authors(sample_rules):
    """Search engine with author metadata."""
    # Add author to sample rule
    sample_rules[0]['author'] = 'John Doe'
    sample_rules[1]['author'] = 'Jane Smith'
    return AliasAwareSearch(sample_rules, {})

def test_find_by_author(search_engine_with_authors):
    """Test finding rules by author."""
    results = search_engine_with_authors.find_by_author('John', limit=10)
    assert len(results) == 1
    assert results[0]['author'] == 'John Doe'

def test_find_by_author_case_insensitive(search_engine_with_authors):
    """Test that search is case-insensitive."""
    results = search_engine_with_authors.find_by_author('JANE', limit=10)
    assert len(results) == 1
    assert results[0]['author'] == 'Jane Smith'

def test_find_by_author_limit(search_engine_with_authors):
    """Test that limit is respected."""
    results = search_engine_with_authors.find_by_author('', limit=1)
    assert len(results) <= 1
```

**4. Write integration tests**

Add to `tests/integration/test_api.py`:

```python
def test_api_search_by_author(client):
    """Test /api/search/by-author endpoint."""
    response = client.post(
        '/api/search/by-author',
        json={'author': 'John', 'limit': 10}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'results' in data
    assert 'result_count' in data
```

**5. Update documentation**

Add to `docs/API.md`:

```markdown
### Search by Author

**Endpoint:** `POST /api/search/by-author`

...endpoint documentation...
```

**6. Run tests**

```bash
pytest tests/ -v
# All tests should pass
```

**7. Commit**

```bash
git add .
git commit -m "feat: Add search by author endpoint"
git push origin [your-branch]
```

---

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/unit/test_search.py -v

# Specific test function
pytest tests/unit/test_search.py::test_exact_match -v

# With coverage
pytest tests/ --cov=app --cov=qa-tools --cov-report=html

# Watch mode (requires pytest-watch)
ptw tests/ -- -v
```

### Test Structure

Each test file follows this pattern:

```python
import pytest
from app.blueprints.search import search_bp
from qa_tools.search_aliases import AliasAwareSearch

# Fixtures (shared setup)
@pytest.fixture
def sample_data():
    return {"key": "value"}

# Test class (optional, for organization)
class TestSearchEngine:
    def test_something(self, sample_data):
        assert True
    
    def test_another_thing(self, sample_data):
        assert True

# Top-level test functions
def test_standalone_function():
    assert 1 + 1 == 2
```

### Writing Good Tests

**1. Test One Thing Per Test**
```python
# ❌ Bad: Tests multiple things
def test_search():
    results = search_engine.search("longsword")
    assert len(results) > 0
    assert results[0]['score'] > 0.5
    assert results[0]['rule_id'] is not None

# ✅ Good: Separate concerns
def test_search_returns_results():
    results = search_engine.search("longsword")
    assert len(results) > 0

def test_search_results_have_scores():
    results = search_engine.search("longsword")
    for result in results:
        assert result['score'] > 0

def test_search_results_have_rule_ids():
    results = search_engine.search("longsword")
    for result in results:
        assert result['rule_id'] is not None
```

**2. Use Descriptive Names**
```python
# ❌ Bad
def test_1():
    pass

# ✅ Good
def test_search_returns_empty_list_for_nonexistent_query():
    pass
```

**3. Test Edge Cases**
```python
def test_search_empty_query():
    with pytest.raises(ValueError):
        search_engine.search("")

def test_search_very_long_query():
    long_query = "a" * 1000
    results = search_engine.search(long_query)
    assert results == []
```

**4. Use Fixtures for Setup**
```python
@pytest.fixture
def populated_search_engine():
    rules = [
        {"rule_id": "TEST-1", "content": "test"},
        {"rule_id": "TEST-2", "content": "example"}
    ]
    return AliasAwareSearch(rules, {})

def test_search_finds_rule(populated_search_engine):
    results = populated_search_engine.search("test")
    assert len(results) > 0
```

---

## Debugging

### Using Python Debugger (pdb)

```python
def search_rules(query):
    import pdb; pdb.set_trace()  # Execution pauses here
    results = []
    # ... continue debugging with n (next), s (step), c (continue)
```

### Using VS Code Debugger

**1. Create `.vscode/launch.json`**:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {"FLASK_APP": "app.py"},
            "args": ["run", "--no-debugger"],
            "jinja": true
        },
        {
            "name": "pytest",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

**2. Set breakpoint** (click left of line number)

**3. Press F5 to start debugging**

### Common Debugging Scenarios

**Scenario 1: Search returning wrong results**
```python
# Add debug prints
def search_rules(query):
    print(f"Query: {query}")  # What are we searching for?
    
    results = []
    for rule in self.rules.values():
        print(f"Checking rule {rule['rule_id']}")
        score = calculate_score(query, rule)
        print(f"  Score: {score}")
        if score >= threshold:
            results.append(rule)
    
    print(f"Final results: {len(results)}")
    return results
```

**Scenario 2: API endpoint returning 500 error**
```python
@search_bp.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.get_json() or {}
        query = data.get('query', '')
        print(f"Received query: {query}")  # Debug
        
        results = search_engine.search_rules(query)
        print(f"Search returned: {len(results)}")  # Debug
        
        return jsonify({"success": True, "results": results})
    except Exception as e:
        print(f"ERROR: {e}")  # Print stack trace
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
```

---

## Logging

### Current Logging (Print Statements)

```python
print("Debug info:", variable)
print(f"Query: {query}, Results: {len(results)}")
```

### Recommended: Structured Logging

Create `app/utils/logging.py`:

```python
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def log_search(query: str, result_count: int, execution_time_ms: float):
    """Log search operation."""
    logger.info(
        "search_executed",
        extra={
            "query": query,
            "result_count": result_count,
            "execution_time_ms": execution_time_ms
        }
    )

def log_error(error_type: str, error_message: str, context: Dict[str, Any]):
    """Log error with context."""
    logger.error(
        f"{error_type}: {error_message}",
        extra=context
    )
```

### Usage

```python
from app.utils.logging import log_search, log_error

def search_endpoint(request):
    try:
        results = search_engine.search(query)
        log_search(query, len(results), 3.2)
        return jsonify({"success": True, "results": results})
    except Exception as e:
        log_error("SearchError", str(e), {"query": query})
        return jsonify({"success": False, "error": str(e)}), 500
```

---

## Environment Variables

### Development Environment Variables

Create `.env` file (NOT committed to git):

```bash
FLASK_ENV=development
FLASK_DEBUG=True
DEBUG=True
LOG_LEVEL=DEBUG
```

### Production Environment Variables

Set in Render.com dashboard or `render.yaml`:

```yaml
envVars:
  - key: FLASK_ENV
    value: production
  - key: DEBUG
    value: False
  - key: LOG_LEVEL
    value: INFO
```

### Usage in Code

```python
import os

DEBUG = os.getenv('DEBUG', 'False') == 'True'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
API_KEY = os.getenv('API_KEY', '')

if not API_KEY and os.getenv('FLASK_ENV') == 'production':
    raise RuntimeError("API_KEY must be set in production")
```

---

## Git Workflow

### Creating a Feature Branch

```bash
# Start from main or ai-agent branch
git checkout main
git pull origin main

# Create feature branch (use descriptive name)
git checkout -b feature/add-search-by-author
# or
git checkout -b fix/typo-in-validation
# or
git checkout -b docs/update-api-reference
```

### Committing Code

```bash
# Stage changes
git add app/blueprints/search.py
git add qa-tools/search_aliases.py
git add tests/

# Commit with descriptive message
git commit -m "feat: Add search by author endpoint

- Add find_by_author() method to AliasAwareSearch
- Add POST /api/search/by-author endpoint
- Add 3 unit tests + 1 integration test
- Update API documentation"

# Or use conventional commits shorthand:
# feat: new feature
# fix: bug fix
# docs: documentation
# test: test-related
# refactor: code restructuring
# perf: performance improvement
```

### Pushing & Creating Pull Request

```bash
# Push branch to GitHub
git push origin feature/add-search-by-author

# Go to GitHub website, create Pull Request
# - Write clear PR description
# - Link related issues
# - Ensure all tests pass
```

### Code Review & Merge

```bash
# After review & approval, merge to main
git checkout main
git pull origin main
git merge feature/add-search-by-author

# Delete feature branch
git branch -d feature/add-search-by-author
git push origin --delete feature/add-search-by-author
```

---

## IDE Setup

### VS Code Recommended Extensions

1. **Python** (ms-python.python)
   - IntelliSense, debugging, linting
   
2. **Pylance** (ms-python.vscode-pylance)
   - Advanced Python language support, type checking
   
3. **Pytest** (littlefoxteam.vscode-pytest)
   - Run tests from UI
   
4. **Python Docstring Generator** (njpwerner.autodocstring)
   - Auto-generate docstrings
   
5. **Code Spell Checker** (streetsidesoftware.code-spell-checker)
   - Catch typos in comments
   
6. **Better Comments** (aaron-bond.better-comments)
   - Highlight important comments

### VS Code Settings

Create `.vscode/settings.json`:

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "100"],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    "pytest.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.analysis.typeCheckingMode": "basic"
}
```

### PyCharm Setup (Alternative)

1. Open project in PyCharm
2. Configure Python interpreter: Settings → Project → Python Interpreter → Add Interpreter → venv
3. Enable pytest: Settings → Tools → Python Integrated Tools → pytest
4. Set code style: Settings → Editor → Code Style → Python → Line length 100
5. Enable type checking: Settings → Editor → Python → Type Checker

---

## Common Development Tasks

### Rebuild the rule index

```bash
cd qa-tools
python parser.py
# Output: "Indexed 487 rules to rules_index.json"
```

### Run interactive search demo

```bash
python qa-tools/demo_search.py
# Prompts: Enter query > search > display results
```

### View the parsed index

```bash
python qa-tools/view_index.py
# Displays all 487 rules in formatted output
```

### Check for syntax errors

```bash
python -m py_compile app/blueprints/search.py
# No output = success
```

### Format code

```bash
# Install formatter (if not already)
pip install black

# Format all Python files
black .

# Format specific file
black app/blueprints/search.py
```

### Lint code

```bash
# Install linter
pip install pylint

# Lint all code
pylint app/ qa-tools/

# Lint specific file
pylint app/blueprints/search.py
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Create venv | `python -m venv venv` |
| Activate venv | `venv\Scripts\activate` (Windows) |
| Install deps | `pip install -r requirements.txt` |
| Run dev server | `python app.py` |
| Run all tests | `pytest tests/ -v` |
| Run specific test | `pytest tests/unit/test_search.py::test_name -v` |
| Test with coverage | `pytest tests/ --cov=app --cov=qa-tools` |
| Debug with pdb | `import pdb; pdb.set_trace()` |
| Format code | `black .` |
| Lint code | `pylint app/ qa-tools/` |
| Rebuild index | `python qa-tools/parser.py` |

---

**Last Updated:** February 2026  
**Maintainer:** AI Agent, HEMA Development Team

For API reference, see [API.md](API.md).  
For system design, see [ARCHITECTURE.md](ARCHITECTURE.md).  
For search algorithm, see [SEARCH_ENGINE.md](SEARCH_ENGINE.md).
