# Getting Started with HEMA Rulebook Project

This guide will help you set up the HEMA Rulebook search application and start working with it.

## Table of Contents
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Using the Search Interface](#using-the-search-interface)
- [Using Search Programmatically](#using-search-programmatically)
- [Troubleshooting](#troubleshooting)

## Quick Start

Get the app running in 5 minutes:

```bash
# Clone repository
git clone https://github.com/SenkiAlphonse/HEMA-rulebook-hun.git
cd HEMA-rulebook-hun

# Set up environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Visit http://localhost:5000
```

## Installation

### System Requirements
- **Python**: 3.9 or higher
- **OS**: Windows, macOS, or Linux
- **Disk**: ~50MB for app and dependencies

### Step 1: Clone the Repository

```bash
git clone https://github.com/SenkiAlphonse/HEMA-rulebook-hun.git
cd HEMA-rulebook-hun
```

### Step 2: Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
# Run tests to verify everything works
pytest tests/ -v

# You should see: ===== 59 passed in X.XXs =====
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Optional: Gemini AI integration (for rule summarization)
GEMINI_API_KEY=your_api_key_here

# Optional: Flask configuration
FLASK_ENV=development
FLASK_DEBUG=true
```

### Getting a Gemini API Key (Optional)

The app works without Gemini, but you can enable AI-powered summaries:

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Create new API key
3. Add to `.env`: `GEMINI_API_KEY=your_key`

### Configuration File

Main settings in `app/config.py`:

```python
# Model selection for Gemini
GEMINI_MODEL_CANDIDATES = ['gemini-2.0-flash', 'gemini-1.5-pro']

# Summary generation
SUMMARY_CHUNK_SIZE = 2000  # Characters per chunk
SUMMARY_MAX_RETRIES = 3    # Retry failed summaries

# Search data paths
RULES_INDEX_PATH = 'qa_tools/data/rules_index.json'
ALIASES_PATH = 'qa_tools/data/aliases.json'
```

## Running the Application

### Development Mode

```bash
# With hot reload (recommended for development)
python app.py

# Flask will start at http://localhost:5000
# The app auto-reloads when you modify Python files
```

### Production Mode

```bash
# Set environment variable
export FLASK_ENV=production  # On Windows: set FLASK_ENV=production

# Run with gunicorn (production WSGI server)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Accessing the Application

- **Web Interface**: http://localhost:5000
- **Search API**: http://localhost:5000/api/search?query=example
- **Rule by ID API**: http://localhost:5000/api/rule/GEN-1.1.1

## Running Tests

### Basic Test Runs

```bash
# Run all tests
pytest tests/ -v

# Run quickly (exit on first failure)
pytest tests/ -x

# Run quietly (minimal output)
pytest tests/ -q
```

### Targeted Testing

```bash
# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run specific test class
pytest tests/unit/test_search.py::TestRulebookSearch -v

# Run specific test
pytest tests/unit/test_search.py::TestRulebookSearch::test_basic_search -v
```

### Coverage Report

```bash
# Generate coverage report
pytest tests/ --cov=app --cov=qa_tools --cov-report=html

# View report
open htmlcov/index.html  # On macOS/Linux
start htmlcov/index.html  # On Windows
```

### Test Markers

```bash
# Run only fast tests (skip slow ones)
pytest tests/ -m "not slow" -v

# Run only marked tests
pytest tests/ -m "integration" -v
```

## Using the Search Interface

### Web Interface

1. Open http://localhost:5000
2. Enter your search query in the search box
3. Results appear below with rule references
4. Click on results to expand details

### Features

- **Natural language search**: "What are the target areas for longsword?"
- **Rule ID search**: "GEN-1.1.1"
- **Fuzzy matching**: Handles typos and variations
- **Alias support**: Search by common alternative names
- **Variant aware**: Different rules for VOR, COMBAT, AFTERBLOW variants

### Search Examples

```
"target areas"              → Rules about valid target areas
"GEN-1.1"                   → Rules starting with GEN-1.1
"szúrás"                    → Hungarian term (thrust)
"longsword"                 → Weapon-specific rules
"VOR variant"               → Variant-specific rules
```

## Using Search Programmatically

### Python API

```python
from qa_tools.search_engine import AliasAwareSearch

# Initialize search engine
search = AliasAwareSearch()

# Basic search
results = search.search("target areas")
for result in results:
    print(f"Rule: {result['id']}")
    print(f"Text: {result['text'][:100]}...")

# Search by rule ID
rule = search.get_rule_by_id("GEN-1.1.1")
print(f"Found: {rule['id']}")

# Get related rules
children = search.get_children_rules("GEN-1")
print(f"Child rules: {[r['id'] for r in children]}")

# Get rule hierarchy
depth = search.get_rule_depth("GEN-1.1.1")
print(f"Hierarchy depth: {depth}")
```

### REST API

```bash
# Search for rules
curl "http://localhost:5000/api/search?query=target+areas"

# Get specific rule
curl "http://localhost:5000/api/rule/GEN-1.1.1"

# Get summary with AI
curl "http://localhost:5000/api/rule/GEN-1.1.1/summary"
```

### API Response Format

```json
{
  "success": true,
  "data": [
    {
      "id": "GEN-1.1.1",
      "section": "GEN-1",
      "text": "Rule text...",
      "weapon": "general",
      "variant": null,
      "source_file": "03-altalanos.md"
    }
  ],
  "count": 1
}
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'qa_tools'"

**Solution**: Install in development mode:
```bash
pip install -e .
```

### "pytest: command not found"

**Solution**: Install test dependencies:
```bash
pip install pytest pytest-cov
```

### Tests fail with "FileNotFoundError: rules_index.json"

**Solution**: Rebuild index:
```bash
cd qa_tools/tools
python parser.py
```

### Flask app won't start

**Solution**: Check port is available:
```bash
# Change port in app.py
if __name__ == '__main__':
    app.run(debug=True, port=8000)  # Use 8000 instead
```

### Gemini AI summaries not working

**Solution**: Verify API key is set:
```bash
# Check if GEMINI_API_KEY is in .env
cat .env | grep GEMINI_API_KEY

# Or check if environment variable is set
echo $GEMINI_API_KEY  # On Windows: echo %GEMINI_API_KEY%
```

### Out of memory errors

**Solution**: Process rules in batches (for large-scale indexing):
```python
# In parser.py or custom script
BATCH_SIZE = 100
for i in range(0, len(rules), BATCH_SIZE):
    batch = rules[i:i + BATCH_SIZE]
    # Process batch
```

## Next Steps

### For Users
- Explore the [search interface](http://localhost:5000)
- Read the [rulebook chapters](../README.md#rulebook-structure)
- Check the [glossary](../fuggelek/02-szojegyzek.md)

### For Developers
- Read [CONTRIBUTING.md](./CONTRIBUTING.md) for development workflow
- Check [ARCHITECTURE.md](./docs/ARCHITECTURE.md) for system design
- See [API.md](./docs/API.md) for endpoint documentation
- Review [TESTING.md](./docs/TESTING.md) for testing patterns

### For Operators
- Read [DEPLOYMENT.md](./DEPLOYMENT.md) for production setup
- Check [RENDER_DEPLOY.md](./RENDER_DEPLOY.md) for cloud deployment

## Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Search [GitHub Issues](https://github.com/SenkiAlphonse/HEMA-rulebook-hun/issues)
- **Examples**: See `teszt/` directory for test cases and examples

## Key Directories Reference

| Directory | Purpose |
|-----------|---------|
| `app/` | Flask web application and API |
| `qa_tools/` | Search engine and indexing tools |
| `tests/` | Unit and integration tests |
| `docs/` | Technical documentation |
| `templates/` | HTML templates for web interface |
| `fuggelek/` | Appendices (glossary, penalties) |
| (root) | Rulebook markdown files |

## Quick Command Reference

```bash
# Development
python app.py                    # Start dev server
pytest tests/ -v                 # Run all tests
pytest tests/ --cov             # Coverage report

# Installation
pip install -r requirements.txt  # Install dependencies
pip install -e .                # Install package in dev mode

# Maintenance
python -m qa_tools.tools.parser.py  # Rebuild search index
python -m qa_tools.tools.add_aliases.py  # Manage aliases

# Production
export FLASK_ENV=production     # Set production mode
gunicorn -w 4 app:app          # Run with gunicorn
```

---

Ready to dive in? Start with `python app.py` and visit http://localhost:5000! 🚀
