# Contributing to HEMA Rulebook Project

Thank you for your interest in contributing! This guide will help you get started with development.

## Table of Contents
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Quality Standards](#code-quality-standards)
- [Testing](#testing)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)

## Development Setup

### Prerequisites
- Python 3.9+
- pip
- Virtual environment (recommended)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/SenkiAlphonse/HEMA-rulebook-hun.git
cd HEMA-rulebook-hun

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests to verify setup
pytest tests/ -v
```

### Install in Development Mode
```bash
# Install the qa_tools package in editable mode
pip install -e .
```

## Project Structure

```
HEMA-rulebook-hun/
├── src/app/                        # Flask web application
│   ├── __init__.py               # App factory
│   ├── blueprints/               # Flask blueprints
│   │   ├── search.py            # Search API endpoints
│   │   ├── ai_services.py       # AI/Gemini integration
│   │   └── rulebook.py          # Rulebook display endpoints
│   ├── config.py                # Centralized configuration
│   ├── utils.py                 # Shared utilities
│   └── validation.py            # Input validation
│
├── src/qa_tools/                   # Search and indexing package
│   ├── search_engine/            # Search implementations
│   │   ├── search_aliases.py    # AliasAwareSearch (production)
│   │   ├── search.py            # RulebookSearch (wrapper/backward compat)
│   │   ├── search_utils.py      # Shared search utilities
│   │   └── __init__.py
│   ├── tools/                    # Utility scripts
│   │   ├── parser.py            # Rule parser
│   │   ├── add_aliases.py       # Alias management
│   │   ├── demo_search.py       # Interactive search demo
│   │   └── __init__.py
│   ├── data/                     # Index and configuration files
│   │   ├── rules_index.json
│   │   └── aliases.json
│   └── __init__.py
│
├── tests/                         # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/                    # Unit tests
│   │   ├── test_search.py
│   │   ├── test_parser.py
│   │   └── test_utils.py
│   └── integration/             # Integration tests
│       └── test_api.py
│
├── templates/                     # Jinja2 templates for Flask
├── docs/                         # Documentation
├── rules/                        # Markdown rulebook files
└── fuggelek/                     # Appendices (glossary, penalties, etc.)
```

## Code Quality Standards

### Style Guide
- Follow **PEP 8** for Python code
- Use **type hints** for function parameters and return values
- Maximum line length: **100 characters** (soft limit)
- Use **snake_case** for variables/functions, **PascalCase** for classes

### Example:
```python
from typing import List, Optional, Dict, Any

def search_rules(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search for rules matching the query.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
    
    Returns:
        List of matching rule dictionaries
    """
    pass
```

### Docstrings
- Use triple-quoted docstrings for all public functions/classes
- Include description, Args, Returns, and Raises sections
- Follow Google-style docstring format

### Imports
- Group imports: standard library, third-party, local
- Use `from module import name` for clarity
- Avoid wildcard imports (`from module import *`)

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_search.py -v

# Run specific test
pytest tests/unit/test_search.py::TestRulebookSearch::test_basic_search -v

# Run with coverage
pytest tests/ --cov=app --cov=qa_tools --cov-report=html

# Run only fast tests (exclude slow marker)
pytest tests/ -m "not slow" -v
```

### Test Structure

**Unit Tests** (`tests/unit/`):
- Test individual functions/methods in isolation
- Use mocks for external dependencies (Gemini API, filesystem)
- Fast execution, no I/O

**Integration Tests** (`tests/integration/`):
- Test interaction between components
- Test actual Flask API endpoints
- May use real test data from fixtures

### Adding New Tests

1. Identify if it's a unit test or integration test
2. Create test file in appropriate directory
3. Use descriptive test names: `test_<function>_<scenario>`
4. Use fixtures from `conftest.py` for shared test data

```python
# Example: tests/unit/test_new_feature.py
import pytest
from qa_tools.search_engine import AliasAwareSearch

class TestNewFeature:
    """Test suite for new feature"""
    
    def test_basic_functionality(self, search_engine):
        """Test basic functionality"""
        result = search_engine.search("query")
        assert len(result) > 0
    
    def test_edge_case(self, search_engine):
        """Test edge case"""
        result = search_engine.search("")
        assert result == []
```

## Making Changes

### Before You Start
1. Check existing issues and PRs
2. Create a new branch: `git checkout -b feature/your-feature-name`
3. Make sure tests pass: `pytest tests/ -v`

### During Development
1. Write tests first (TDD approach recommended)
2. Implement the feature
3. Ensure all tests pass: `pytest tests/ -v`
4. Check code style: Follow PEP 8 standards
5. Add docstrings and type hints
6. Update relevant documentation

### Code Changes Checklist
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Code follows PEP 8
- [ ] Type hints added to functions
- [ ] Docstrings added/updated
- [ ] Related documentation updated
- [ ] No console logging (use logging module)
- [ ] No hardcoded values (use config.py)

## Submitting Changes

### Pull Request Process

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub:
   - Clear title describing the change
   - Description explaining what and why
   - Reference any related issues (#123)

3. **PR Description Template**:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Code refactoring
   
   ## Testing
   Describe tests added/modified
   
   ## Checklist
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] Code follows style guide
   ```

4. **Review Process**:
   - Code review by maintainers
   - Address feedback
   - Ensure CI/CD passes
   - Merge when approved

### Commit Messages

Use clear, descriptive commit messages:

```
# Good
git commit -m "Add case-insensitive rule ID lookup"
git commit -m "Fix: Handle empty search queries gracefully"
git commit -m "Docs: Add testing best practices guide"

# Avoid
git commit -m "fix stuff"
git commit -m "update"
```

## Architecture & Design Principles

### Single Responsibility Principle
- Each module has one clear purpose
- Example: `search_utils.py` only contains search utility functions

### DRY (Don't Repeat Yourself)
- Avoid code duplication
- Extract common patterns into utilities
- Use composition over inheritance

### Configuration Over Hardcoding
- All configurable values in `src/app/config.py`
- Environment variables for secrets (API keys)
- No magic numbers in code

### Error Handling
- Use specific exception types (not bare `except Exception:`)
- Log with `logger.exception()` for debugging
- Provide helpful error messages

## Documentation Standards

When adding features, update relevant documentation:

- **API changes**: Update `docs/API.md`
- **Architecture changes**: Update `docs/ARCHITECTURE.md`
- **New features**: Add to `docs/DEVELOPMENT.md`
- **Testing**: Update `docs/TESTING.md` if test patterns change

## Questions?

- Check existing documentation in `docs/`
- Review similar code patterns in the codebase
- Open an issue for clarification

## License

By contributing, you agree that your contributions will be licensed under the same license as this project.

---

Happy coding! 🎉
