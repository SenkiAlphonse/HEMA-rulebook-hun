# HEMA Rulebook Q&A System - Documentation Index

Welcome to the HEMA Rulebook Q&A System documentation. This is a comprehensive AI-assisted search and Q&A solution for the "Kard Rendje" (Order of the Sword) rulebook, indexed with natural language querying capabilities and rule cross-referencing.

## Quick Navigation by Role

### 👨‍💻 **For Developers**
Start here if you're building features or maintaining the codebase.

- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Local setup, project structure, code conventions, adding features, testing workflow, debugging
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design, data flow, module responsibilities, how things work together

### 🔌 **For API Integrators**
Use this if you're building tools that query the rulebook programmatically.

- **[API.md](API.md)** - Complete REST endpoint reference with examples, parameters, response formats, error handling
- **[SEARCH_ENGINE.md](SEARCH_ENGINE.md)** - How the search algorithm works, scoring, aliases, performance characteristics

### 🚀 **For DevOps / Deployment**
References for deployment, CI/CD, environment configuration.

- **DEPLOYMENT.md** - Render deployment, GitHub Actions, environment variables
- **[ARCHITECTURE.md](ARCHITECTURE.md)** → "Deployment Architecture" section

### 🧪 **For QA / Testing**
Test coverage, test suite documentation, validation procedures.

- **TESTING.md** - Test suite overview, running tests, coverage reports
- **[DEVELOPMENT.md](DEVELOPMENT.md)** → "Testing" section for adding new tests

---

## Project Overview

**What is this?**  
A Flask-based Q&A system that indexes the HEMA rulebook (Hungarian martial arts rules) and enables fast natural language queries to find relevant rules. Users ask questions in Hungarian or English, and the system returns specific rule references with hierarchical context.

**Example Query:**
- **User asks:** "What are valid target areas for longsword?"
- **System returns:** Rules from `03-altalanos.md` (general) + `05-hosszukard.md` (longsword-specific) with rule IDs (e.g., GEN-1.2.3), sections, and cross-references

**Key Features:**
- ⚡ **O(1) Rule Lookup** - Sub-millisecond searches via indexed hash tables
- 🏷️ **Alias Resolution** - Maps Hungarian terms to English + finds synonyms automatically
- 🎯 **Multi-Factor Scoring** - Ranks results by exact match → partial match → fuzzy match
- 🔀 **Variant Support** - Handles longsword VOR/COMBAT/AFTERBLOW rule differences
- 📚 **Glossary Integration** - Automatically resolves HEMA terminology
- 🌐 **REST API** - Full HTTP API for programmatic access

---

## Documentation Map

| Document | Purpose | Audience | Pages |
|----------|---------|----------|-------|
| **INDEX.md** | You are here! Navigation hub | Everyone | 1 |
| **API.md** | REST endpoint reference with examples | API users, integrators | 15+ |
| **ARCHITECTURE.md** | System design, data flow, algorithms | Developers, architects | 18+ |
| **DEVELOPMENT.md** | Dev setup, code conventions, workflow | Developers, contributors | 20+ |
| **SEARCH_ENGINE.md** | Search algorithm deep dive, scoring | Advanced developers, data scientists | 16+ |

### Supplementary Documentation

- **GETTING_STARTED.md** - Initial project overview (legacy, see DEVELOPMENT.md for current setup)
- **PROJECT_SUMMARY.md** - High-level feature list (being replaced by INDEX.md)
- **TESTING.md** - Test execution and coverage details
- **DEPLOYMENT.md** - Render/GitHub Actions configuration
- **ALIASES_IMPLEMENTATION.md** - Alias system technical details
- **INTERFACES_PREVIEW.md** - UI mockups and interface design

---

## Quick Start

### I want to...

**...understand the system**
1. Read **ARCHITECTURE.md** → System Overview section
2. Skim **SEARCH_ENGINE.md** → Algorithm section

**...set up a dev environment**
1. Follow **DEVELOPMENT.md** → Setup section
2. Run `pytest tests/ -v` to validate installation

**...integrate with the API**
1. Read **API.md** → Endpoints section
2. Copy example from **API.md** → Use Cases
3. Test with curl: `curl http://localhost:5000/api/search -d '{"query":"longsword target"}'`

**...add a new feature**
1. Read **DEVELOPMENT.md** → Adding Features section
2. Check **ARCHITECTURE.md** → Module Responsibilities section
3. Write tests first (see **DEVELOPMENT.md** → Testing)
4. Submit PR with test coverage

**...debug a search issue**
1. Check **SEARCH_ENGINE.md** → Debugging Guide
2. Run `python qa-tools/demo_search.py` with your query
3. Inspect `qa-tools/rules_index.json` for data

**...understand the search ranking**
1. Read **SEARCH_ENGINE.md** → Scoring Formula section
2. Calculate expected score manually
3. Compare with actual via demo_search.py

---

## Project Structure at a Glance

```
HEMA-rulebook-hun/
├── app/                          # Flask application (3 blueprints)
│   ├── blueprints/
│   │   ├── search.py             # /api/search endpoint
│   │   ├── ai_services.py        # /api/ai/* endpoints
│   │   └── rulebook.py           # /api/rulebook/* endpoints
│   ├── utils/                    # Helpers (validation, parsing, AI calls)
│   └── __init__.py               # Flask app factory
├── qa-tools/                     # Search engine & indexing
│   ├── search_aliases.py         # AliasAwareSearch class (core engine)
│   ├── parser.py                 # Markdown → JSON parser
│   ├── aliases.json              # Rule aliases (Hungarian↔English)
│   └── rules_index.json          # Parsed rules (487 rules)
├── tests/                        # Test suite (59 tests, 100% passing)
│   ├── unit/                     # Unit tests (41 tests)
│   ├── integration/              # API tests (13 tests)
│   └── conftest.py               # pytest fixtures
├── templates/                    # HTML templates (web UI)
├── docs/                         # Documentation (you are here!)
├── fuggelek/                     # Appendices (glossary, priority rules, other weapons)
├── requirements.txt              # Python dependencies
└── [rulebook chapters]           # Markdown rulebook files (01-*.md, 05-*.md, etc.)
```

---

## Technology Stack

- **Language:** Python 3.14
- **Framework:** Flask 3.1.2
- **Testing:** pytest 9.0.2 with pytest-cov, pytest-flask, pytest-mock
- **Search:** Custom O(1) hash-based engine with multi-factor scoring
- **Deployment:** Render.com with GitHub Actions CI/CD
- **Type System:** Full Python type hints (PEP 484)

---

## Common Tasks

### Run tests
```bash
pytest tests/ -v                    # All tests with verbose output
pytest tests/unit/ -v               # Unit tests only
pytest tests/ --cov=app --cov=qa-tools  # With coverage report
```

### Start development server
```bash
python app.py                       # Runs on http://localhost:5000
```

### Search the rulebook
```bash
python qa-tools/demo_search.py      # Interactive search demo
```

### View the index
```bash
python qa-tools/view_index.py       # See parsed rules and structure
```

---

## FAQ

**Q: How do I add a new rule?**  
A: Edit the relevant markdown file (e.g., `05-hosszukard.md`), then run `python qa-tools/parser.py` to rebuild the index. See **DEVELOPMENT.md** → Adding Features.

**Q: Can I query in English?**  
A: Yes! The system handles both Hungarian and English. See **API.md** → Search Endpoint for examples.

**Q: Why is this rule not showing up?**  
A: Check **SEARCH_ENGINE.md** → Debugging Guide. Common issues: rule not indexed, alias not mapped, threshold too high.

**Q: How do I report a bug?**  
A: File an issue on GitHub with: (1) Query used, (2) Expected result, (3) Actual result. Include screenshots if UI-related.

**Q: Is the API rate-limited?**  
A: Not in dev mode. In production, implement rate limiting via reverse proxy (nginx) or middleware. See **API.md** → Rate Limiting.

**Q: How do I deploy this?**  
A: See **DEPLOYMENT.md** or **ARCHITECTURE.md** → Deployment Architecture. TL;DR: Push to main branch, GitHub Actions runs tests, Render auto-deploys if all pass.

---

## Support & Contributing

- **Found a bug?** Check **DEVELOPMENT.md** → Debugging, then open an issue
- **Want to add a feature?** Read **DEVELOPMENT.md** → Adding Features, then submit a PR
- **Have a question?** Check the relevant documentation first, then ask in discussions
- **Found docs missing?** File an issue or submit a PR with the missing content

---

## Document Maintenance

This documentation is maintained alongside the code. When making changes:

1. **Code change?** Update relevant docs (ARCHITECTURE.md if design changes, API.md if endpoints change)
2. **New feature?** Add to DEVELOPMENT.md → Features section + relevant technical doc
3. **Bug fix?** No doc change needed unless it affects user-facing behavior

---

**Last Updated:** February 2026  
**Version:** 2.0 (Comprehensive Modular Documentation)  
**Maintainers:** AI Agent, HEMA Development Team

---

**Ready to dive in?** Pick your role above and start with the recommended document! 🎯
