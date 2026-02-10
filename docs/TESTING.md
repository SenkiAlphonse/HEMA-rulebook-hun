# Testing Infrastructure

This project includes comprehensive automated testing with CI/CD integration.

## Test Structure

```
tests/
├── unit/              # Unit tests for individual modules
│   ├── test_search.py      # Search engine tests
│   ├── test_parser.py      # Parser tests
│   └── test_utils.py       # Utility function tests
├── integration/       # Integration tests
│   └── test_api.py         # Flask API endpoint tests
└── conftest.py        # Shared test fixtures
```

## Running Tests Locally

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run Specific Test Suites
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_search.py -v

# Specific test
pytest tests/unit/test_search.py::TestRulebookSearch::test_search_basic -v
```

### Run Tests with Verbose Output
```bash
# Run with detailed output
pytest tests/ -v

# Run with extra verbosity
pytest tests/ -vv
```

### Run Tests by Marker
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## CI/CD Integration

### GitHub Actions
Tests run automatically on:
- Every push to `main` or `ai-agent` branches
- Every pull request to `main`

View results in the **Actions** tab on GitHub.

### Render Deployment
Tests run during deployment:
- Tests must pass before app deploys
- Failed tests block deployment
- View results in Render build logs

## Test Results

Current test statistics:
- **Unit tests**: Core modules (search, parser, utils)
- **Integration tests**: API endpoints  
- **Total test cases**: 59 (100% passing)

View test results in the **Actions** tab on GitHub.

## Pre-commit Hook (Optional)

Run tests automatically before each commit:

```bash
# Enable pre-commit hook
git config core.hooksPath .githooks

# On Unix/macOS, make executable
chmod +x .githooks/pre-commit
```

To skip pre-commit tests temporarily:
```bash
git commit --no-verify
```

## Test Configuration

- **pytest.ini**: Pytest configuration and options
- **conftest.py**: Shared fixtures and test setup

## Writing New Tests

### Unit Test Example
```python
# tests/unit/test_my_module.py
import pytest

class TestMyFeature:
    def test_basic_functionality(self, search_engine):
        """Test basic feature"""
        result = search_engine.my_function("test")
        assert result is not None
```

### Integration Test Example
```python
# tests/integration/test_api.py
def test_my_endpoint(client):
    """Test API endpoint"""
    response = client.post('/api/my-endpoint',
                          json={"param": "value"})
    assert response.status_code == 200
```

## Troubleshooting

### Tests Fail Locally
1. Ensure dependencies are installed: `pip install -r requirements.txt`
2. Regenerate index: `python build.py`
3. Check Python version: Python 3.10+ required

### Tests Pass Locally but Fail in CI
1. Check for hardcoded paths
2. Verify all files are committed
3. Check environment-specific code
4. Verify Python version matches CI (3.10+)
