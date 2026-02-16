# Testing Best Practices & Guide

Comprehensive guide to understanding and maintaining the HEMA Rulebook test suite.

## Table of Contents
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Fixtures](#test-fixtures)
- [Mock Patterns](#mock-patterns)
- [Best Practices](#best-practices)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Test Structure

### Directory Organization

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Pytest configuration and fixtures
├── unit/                    # Fast, isolated tests
│   ├── __init__.py
│   ├── test_search.py      # Search engine tests
│   ├── test_parser.py      # Parser tests
│   └── test_utils.py       # Utility function tests
└── integration/            # Tests requiring multiple components
    ├── __init__.py
    └── test_api.py         # Flask endpoint tests
```

### Test File Naming Convention

- Files: `test_<module_name>.py`
- Classes: `Test<ComponentName>`
- Methods: `test_<functionality>_<scenario>`

**Examples:**
```python
# test_search.py
class TestRulebookSearch:
    def test_basic_search_returns_results(self):
        ...
    
    def test_search_empty_query_returns_empty_list(self):
        ...
    
    def test_search_case_insensitive_lookup(self):
        ...
```

### Test Categorization

**Unit Tests** (70-80% of tests)
- Test individual functions or methods
- Fast execution (< 10ms each)
- Mock external dependencies
- Isolated from I/O

**Integration Tests** (20-30% of tests)
- Test component interactions
- May use real file I/O
- Verify Flask API endpoints
- Test fixtures with actual data

### Test Markers

Mark tests for selective execution:

```python
import pytest

# Mark slow tests
@pytest.mark.slow
def test_large_dataset_search():
    ...

# Mark integration tests
@pytest.mark.integration
def test_api_endpoint():
    ...

# Mark expected failures
@pytest.mark.xfail
def test_known_issue():
    ...
```

Run marked tests:
```bash
pytest tests/ -m "not slow"       # Skip slow tests
pytest tests/ -m "integration"    # Only integration tests
pytest tests/ --co -m "slow"      # List all slow tests
```

## Running Tests

### Quick Test Runs

```bash
# Run all tests
pytest tests/ -v

# Run with minimal output
pytest tests/ -q

# Run and stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Run specific test file
pytest tests/unit/test_search.py -v

# Run specific test class
pytest tests/unit/test_search.py::TestRulebookSearch -v

# Run specific test method
pytest tests/unit/test_search.py::TestRulebookSearch::test_basic_search -v
```

### Advanced Test Execution

```bash
# Show print statements
pytest tests/ -v -s

# Drop into debugger on failure
pytest tests/ --pdb

# Show top 10 slowest tests
pytest tests/ --durations=10

# Run tests in parallel (requires pytest-xdist)
pytest tests/ -n 4

# Collect tests without running
pytest tests/ --collect-only

# Run with custom Python path
pytest tests/ --pythonpath=.
```

### Coverage Reports

```bash
# Generate coverage report
pytest tests/ --cov=app --cov=qa_tools --cov-report=html

# Show coverage in terminal
pytest tests/ --cov=app --cov=qa_tools --cov-report=term-missing

# Coverage for specific file
pytest tests/ --cov=qa_tools.search_engine --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Continuous Testing

```bash
# Run tests on file changes (requires pytest-watch)
ptw tests/ -- -v

# Run tests in watch mode with coverage
ptw tests/ -- --cov=app --cov=qa_tools
```

## Writing Tests

### Basic Unit Test Template

```python
import pytest
from qa_tools.search_engine import AliasAwareSearch

class TestRulebookSearch:
    """Test suite for RulebookSearch"""
    
    @pytest.fixture
    def search_engine(self):
        """Provide search engine instance"""
        return AliasAwareSearch()
    
    def test_basic_functionality(self, search_engine):
        """Test basic search functionality"""
        # Arrange
        query = "target areas"
        
        # Act
        results = search_engine.search(query)
        
        # Assert
        assert len(results) > 0
        assert results[0]['id'] is not None
    
    def test_edge_case_empty_query(self, search_engine):
        """Test search with empty query"""
        results = search_engine.search("")
        assert results == []
    
    def test_case_sensitivity(self, search_engine):
        """Test case-insensitive search"""
        # Search should work with different cases
        result_lower = search_engine.search("gen-1")
        result_upper = search_engine.search("GEN-1")
        assert len(result_lower) == len(result_upper)
```

### Integration Test Template

```python
import pytest
from app import create_app

class TestSearchAPI:
    """Test Flask search API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_search_endpoint_returns_json(self, client):
        """Test search endpoint returns valid JSON"""
        response = client.get('/api/search?query=target')
        assert response.status_code == 200
        assert response.json['success'] is True
    
    def test_rule_by_id_endpoint(self, client):
        """Test rule lookup endpoint"""
        response = client.get('/api/rule/GEN-1.1.1')
        assert response.status_code == 200
        assert 'data' in response.json
```

### Parameterized Tests

Test multiple scenarios with less code:

```python
import pytest

class TestSearchVariants:
    """Test search with multiple scenarios"""
    
    @pytest.mark.parametrize("query,expected_count", [
        ("target", 5),  # At least 5 results for "target"
        ("GEN-1", 3),   # At least 3 GEN-1 rules
        ("VOR", 2),     # At least 2 VOR-specific rules
    ])
    def test_search_returns_expected_count(self, search_engine, query, expected_count):
        """Test search returns reasonable number of results"""
        results = search_engine.search(query)
        assert len(results) >= expected_count
    
    @pytest.mark.parametrize("rule_id", [
        "GEN-1.1.1",
        "GEN-1.2.1",
        "VOR-1.1.1",
    ])
    def test_get_rule_by_id(self, search_engine, rule_id):
        """Test getting rule by ID for multiple IDs"""
        rule = search_engine.get_rule_by_id(rule_id)
        assert rule is not None
        assert rule['id'] == rule_id
```

### Testing Exceptions

```python
import pytest
from qa_tools.search_engine import AliasAwareSearch

class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_rule_id_raises_error(self, search_engine):
        """Test that invalid rule ID raises appropriate error"""
        with pytest.raises(ValueError):
            search_engine.get_rule_by_id("INVALID-99.99.99")
    
    def test_malformed_query_handled_gracefully(self, search_engine):
        """Test graceful handling of malformed queries"""
        # Should not raise, should return empty or default
        result = search_engine.search("@#$%^&*()")
        assert isinstance(result, list)
```

## Test Fixtures

### Understanding Fixtures

Fixtures provide reusable test data and setup/teardown:

```python
import pytest
from qa_tools.search_engine import AliasAwareSearch

# Function-scoped fixture (created for each test)
@pytest.fixture
def search_engine():
    """Provide search engine instance"""
    return AliasAwareSearch()

# Session-scoped fixture (created once for entire test session)
@pytest.fixture(scope="session")
def rules_index():
    """Load rules index once for all tests"""
    return load_rules_index()
```

### Fixture Lifecycle

```python
@pytest.fixture
def resource():
    """Fixture with setup and teardown"""
    # SETUP: This code runs before the test
    resource = expensive_setup()
    
    # The test runs here with 'resource' available
    yield resource
    
    # TEARDOWN: This code runs after the test
    resource.cleanup()
```

### Shared Fixtures (conftest.py)

The `conftest.py` file contains fixtures available to all tests:

```python
# tests/conftest.py
import pytest
from app import create_app
from qa_tools.search_engine import AliasAwareSearch

@pytest.fixture
def app():
    """Create app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def search_engine():
    """Create search engine instance"""
    return AliasAwareSearch()

# Now available in any test file:
class TestSomething:
    def test_example(self, search_engine):
        results = search_engine.search("test")
        assert len(results) >= 0
```

### Current conftest.py

See `tests/conftest.py` for all available fixtures:
- `app` - Flask test application
- `client` - Flask test client
- `search_engine` - Search engine instance
- `runner` - Flask CLI test runner

## Mock Patterns

### Mocking External Dependencies

```python
from unittest.mock import patch, MagicMock
import pytest

class TestAISummaries:
    """Test AI summary functionality with mocked Gemini API"""
    
    @patch('app.blueprints.ai_services.call_gemini_api')
    def test_summary_generation(self, mock_gemini):
        """Test summary generation calls Gemini"""
        # Setup mock
        mock_gemini.return_value = "Summary text"
        
        # Call code that uses Gemini
        from app.blueprints import ai_services
        result = ai_services.get_summary("GEN-1.1.1")
        
        # Verify mock was called
        mock_gemini.assert_called_once()
        assert result == "Summary text"
    
    @patch('app.blueprints.ai_services.call_gemini_api')
    def test_summary_handles_api_failure(self, mock_gemini):
        """Test summary generation handles API failures"""
        # Setup mock to raise error
        mock_gemini.side_effect = Exception("API Error")
        
        from app.blueprints import ai_services
        
        # Should handle error gracefully
        result = ai_services.get_summary("GEN-1.1.1")
        assert result is None or "error" in result.lower()
```

### Mocking File I/O

```python
from unittest.mock import mock_open, patch
import pytest

class TestRuleParser:
    """Test rule parser with mocked file I/O"""
    
    @patch('builtins.open', new_callable=mock_open, read_data='# Test Rule\n**GEN-1.1.1** Test content')
    def test_parse_markdown_file(self, mock_file):
        """Test parsing markdown without hitting filesystem"""
        from qa_tools.tools.parser import parse_markdown
        
        rules = parse_markdown("test.md")
        
        # Verify file was opened
        mock_file.assert_called_once_with("test.md", 'r')
        # Verify parsing worked
        assert len(rules) > 0
```

### Mocking Database Access

```python
from unittest.mock import patch, MagicMock
import pytest

class TestSearchWithDB:
    """Test search functionality with mocked database"""
    
    @patch('qa_tools.search_engine.load_rules_index')
    def test_search_with_custom_index(self, mock_load):
        """Test search with custom mocked index"""
        # Setup mock index data
        mock_index = {
            'rules': [
                {'id': 'TEST-1', 'text': 'Test rule'},
            ]
        }
        mock_load.return_value = mock_index
        
        from qa_tools.search_engine import AliasAwareSearch
        search = AliasAwareSearch()
        
        results = search.search("test")
        assert len(results) > 0
```

## Best Practices

### 1. Keep Tests Independent

❌ **Bad** - Tests depend on each other
```python
def test_1():
    global shared_state
    shared_state = "initialized"

def test_2():
    # Assumes test_1 ran first
    assert shared_state == "initialized"
```

✅ **Good** - Each test is independent
```python
@pytest.fixture
def setup():
    return "initialized"

def test_1(setup):
    assert setup == "initialized"

def test_2(setup):
    assert setup == "initialized"
```

### 2. Use Descriptive Names

❌ **Bad** - Unclear what is being tested
```python
def test_1():
    result = search.search("test")
    assert result
```

✅ **Good** - Clear intent
```python
def test_search_returns_nonempty_results_for_valid_query():
    result = search.search("valid query")
    assert len(result) > 0
```

### 3. Arrange-Act-Assert Pattern

```python
def test_search_with_query():
    # ARRANGE: Set up test data
    search = AliasAwareSearch()
    query = "target areas"
    
    # ACT: Execute the code being tested
    results = search.search(query)
    
    # ASSERT: Verify the results
    assert len(results) > 0
    assert all('id' in r for r in results)
```

### 4. Mock External Dependencies

```python
# ✅ Good: Mock external API
@patch('app.call_gemini_api')
def test_summary_with_mock_api(self, mock_api):
    mock_api.return_value = "summary"
    result = get_summary("rule")
    assert result == "summary"

# ❌ Bad: Actual API calls in tests
def test_summary_with_real_api():
    # Will fail if API is down, slow, or rate-limited
    result = get_summary("rule")
    assert result is not None
```

### 5. Use Fixtures for Setup

```python
# ✅ Good: Fixtures manage setup/teardown
@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    yield app
    # Cleanup happens automatically

class TestAPI:
    def test_endpoint(self, app):
        client = app.test_client()
        response = client.get('/api/search?query=test')
        assert response.status_code == 200

# ❌ Bad: Manual setup in each test
class TestAPI:
    def test_endpoint_1(self):
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()
        # ... test code ...
    
    def test_endpoint_2(self):
        app = create_app()  # Repeated setup
        app.config['TESTING'] = True
        client = app.test_client()
        # ... test code ...
```

### 6. Test Edge Cases

```python
def test_comprehensive_search():
    """Test search handles various edge cases"""
    search = AliasAwareSearch()
    
    # Normal case
    assert len(search.search("valid query")) > 0
    
    # Edge cases
    assert search.search("") == []           # Empty query
    assert search.search("@#$%") == []       # Special chars
    assert search.search(" " * 100) == []    # Whitespace only
    assert len(search.search("a")) >= 0      # Single char
```

### 7. Test Error Conditions

```python
def test_error_handling():
    """Test that errors are handled properly"""
    search = AliasAwareSearch()
    
    # Should raise ValueError for invalid rule ID
    with pytest.raises(ValueError):
        search.get_rule_by_id("INVALID-99.99.99")
    
    # Should return empty list instead of crashing
    result = search.search(None)
    assert isinstance(result, list)
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, '3.10', 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: pytest tests/ -v --cov=app --cov=qa_tools
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### Running Tests Locally Before Push

```bash
# Create a pre-commit hook to run tests
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
pytest tests/ -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Push cancelled."
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

## Troubleshooting

### Tests Pass Locally but Fail in CI

**Possible causes:**
- Different Python versions
- Environment variables not set
- File path issues (Windows vs Linux)
- Timing issues (tests too fast)

**Solutions:**
```bash
# Test with different Python versions
tox tests/

# Test with specific environment
python3.10 -m pytest tests/ -v

# Check file paths
pytest tests/ -v -s  # Show all output

# Add delays for timing issues
import time
time.sleep(0.1)  # Add delay if needed
```

### ModuleNotFoundError in Tests

```bash
# Ensure pythonpath is correct
export PYTHONPATH=.
pytest tests/ -v

# Or use pytest.ini configuration
# (Already configured in this project)
```

### Tests Hang or Timeout

```bash
# Add timeout to prevent hanging tests
pytest tests/ --timeout=10  # 10 second timeout

# Run with verbose output to see where it hangs
pytest tests/ -v -s

# Kill hung processes
pkill -f pytest
```

### Fixture Scope Issues

```bash
# Test fixture scoping
pytest tests/ -v --setup-show  # Show fixture setup/teardown

# Check fixture availability
pytest tests/ --fixtures | grep -A 5 "search_engine"
```

## Quick Command Reference

```bash
# Development workflow
pytest tests/ -v                    # Run all tests
pytest tests/ -x                    # Stop on first failure
pytest tests/ --lf                  # Run last failed
pytest tests/ -k "search"           # Run tests matching pattern

# Coverage
pytest tests/ --cov --cov-report=html   # HTML coverage report
pytest tests/ --cov --cov-report=term   # Terminal report

# Debugging
pytest tests/ -v -s                 # Show print output
pytest tests/ --pdb                 # Debug on failure
pytest tests/ -x --pdb              # Debug first failure

# Advanced
pytest tests/ --collect-only        # List all tests
pytest tests/ --durations=10        # Show slowest tests
pytest tests/ -n 4                  # Run parallel (requires pytest-xdist)
```

## References

- [pytest Documentation](https://docs.pytest.org/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

---

**Current Test Suite Status:**
- Total Tests: 59
- Passing: 59/59 (100%)
- Coverage: 46.07%
- Execution Time: ~2.3 seconds

For more information, see [CONTRIBUTING.md](./CONTRIBUTING.md) and [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md).
