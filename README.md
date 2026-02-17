# Magyar Hosszúkardvívó Sportszövetség (Hungarian Longsword Federation, MHS) - HEMA Rulebook Project

[![Tests](https://img.shields.io/badge/tests-59%2F59%20passing-brightgreen)](./tests)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-CC%20BY--NC--SA%204.0-green)](./LICENSE)

A comprehensive AI-assisted Hungarian Historical European Martial Arts (HEMA) rulebook for the "Magyar Hosszúkardvívó Sportszövetség" (Hungarian Longsword Federation, MHS) competition ruleset. This project provides a searchable web interface with natural language query support and optional AI-powered rule summarization.

## Quick Links

📚 **Documentation**
- [Getting Started](./GETTING_STARTED.md) - Setup and first run
- [Contributing Guide](./CONTRIBUTING.md) - Development workflow
- [Architecture Documentation](./docs/ARCHITECTURE.md) - System design
- [API Reference](./docs/API.md) - REST endpoints

🎯 **For Different Roles**
- **Fencers/Judges**: [Start here](./GETTING_STARTED.md#quick-start) to use the search interface
- **Developers**: [Contributing guide](./CONTRIBUTING.md) for development setup
- **Operators**: [Deployment guide](./DEPLOYMENT.md) for production setup

## Features

✨ **Core Features**
- 🔍 **Natural Language Search** - Ask questions in Hungarian or English
- 📋 **Hierarchical Rule Structure** - Organized by weapon type and category
- 🎯 **Rule ID Navigation** - Direct lookup by rule identifier (e.g., GEN-1.1.1)
- 🔗 **Cross-References** - Related rules and glossary terms
- 🤖 **AI Summaries** (Optional) - Rule summarization via Gemini AI
- 📱 **Web Interface** - Clean, responsive search interface
- ⚔️ **Variant Support** - Different rules for VOR, COMBAT, AFTERBLOW variants
- 🇭🇺 **Hungarian Content** - Complete rulebook in Hungarian with glossary

## Quick Start

Get the app running in minutes:

```bash
# Clone and setup
git clone https://github.com/SenkiAlphonse/HEMA-rulebook-hun.git
cd HEMA-rulebook-hun

# Create environment and install
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the app
python app.py
# Visit http://localhost:5000
```

See [Getting Started](./GETTING_STARTED.md) for detailed setup instructions.

## Usage Examples

### Web Interface
1. Visit http://localhost:5000
2. Enter search query: "What are valid target areas for longsword?"
3. Results show matching rules with rule IDs and clickable links

### Search Examples
- `"target areas"` - Rules about valid target areas
- `"GEN-1.1"` - Hierarchical rule lookup
- `"szúrás"` - Hungarian terms (thrust)
- `"VOR variant"` - Variant-specific rules

### REST API
```bash
# Search for rules
curl "http://localhost:5000/api/search?query=target+areas"

# Get specific rule
curl "http://localhost:5000/api/rule/GEN-1.1.1"

# Get AI summary (requires GEMINI_API_KEY)
curl "http://localhost:5000/api/rule/GEN-1.1.1/summary"
```

See [API Documentation](./docs/API.md) for complete endpoint reference.

## Rulebook Structure

### 📖 Main Rulebook Chapters

| Chapter | Content |
|---------|---------|
| [Introduction](01-altalanos.md) | Project and competition overview |
| [Equipment](02-szojegyzek.md) | Gear and safety requirements |
| [General Rules](03-felszereles.md) | Rules applying to all weapons |
| [Organization](04-biraskodas.md) | Tournament and refereeing |
| **Longsword** | |
| [Longsword General](05-hosszukard.md) | Base longsword rules |
| [Longsword VOR](05.a-hosszukard-VOR.md) | VOR variant specific rules |
| [Longsword COMBAT](05.b-hosszukard-COMBAT.md) | COMBAT variant specific rules |
| [Longsword AFTERBLOW](05.c-hosszukard-AFTERBLOW.md) | AFTERBLOW variant specific rules |
| [Other Weapons](fuggelek/06-rapir.md) | Rapier, armored sword, etc. |
| [Etiquette & Discipline](08-etikett_fegyelem.md) | Code of conduct |
| [Organization & Refereeing](09-szervezes.md) | Tournament management |

### 📑 Appendices

- [Glossary (Szójegyzék)](fuggelek/01-szojegyzek.md) - Hungarian HEMA terminology
- [Priority Rules](fuggelek/02-elsobbseg.md) - Rule hierarchy explanation
- [Penalties Table](fuggelek/Buntetesek_tablazata.html) - Sanctions and penalties

## Project Structure

```
HEMA-rulebook-hun/
├── app/                          # Flask web application
│   ├── blueprints/              # API endpoints
│   ├── config.py                # Configuration
│   ├── utils.py                 # Utilities
│   └── validation.py            # Input validation
│
├── qa_tools/                    # Search & indexing package
│   ├── search_engine/           # Search implementations
│   ├── tools/                   # Utility scripts
│   └── data/                    # Index files
│
├── tests/                       # Test suite (59 tests)
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
│
├── docs/                        # Technical documentation
├── templates/                   # Web interface templates
├── [0X]-*.md                   # Rulebook chapters
└── fuggelek/                   # Appendices
```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.9+, Flask |
| Search | Custom hierarchical indexing |
| AI Summaries | Google Gemini API (optional) |
| Database | JSON indexes |
| Testing | pytest, pytest-cov |
| Deployment | Gunicorn, Render.com ready |

## Recent Improvements

### Phase 2 Code Quality Enhancements
- ✅ Professional Python package structure (`qa_tools/`)
- ✅ Consolidated search engines (single production implementation)
- ✅ Improved exception handling and logging
- ✅ Centralized configuration management
- ✅ Comprehensive test suite (59 tests, 46% coverage)

### Phase 1 Critical Fixes
- ✅ Bare exception handling → specific exception types
- ✅ Hardcoded values → centralized config
- ✅ Code duplication → single source of truth
- ✅ Test organization → clean professional structure

## Development

### Requirements
- Python 3.9+
- pip
- Virtual environment (recommended)

### Development Setup

```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/ -v

# Generate coverage report
pytest tests/ --cov=app --cov=qa_tools --cov-report=html
```

### Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for:
- Development workflow
- Code standards
- Testing requirements
- Pull request process

### Code Quality

- **Style**: PEP 8 with 100-character soft limit
- **Type Hints**: Required for public APIs
- **Docstrings**: Google-style format
- **Tests**: Unit + integration tests required
- **Coverage**: Target 50%+ code coverage

## Configuration

### Environment Variables

```bash
# Optional: Enable AI rule summaries
GEMINI_API_KEY=your_api_key_here

# Optional: Flask settings
FLASK_ENV=development
FLASK_DEBUG=true
```

### Main Configuration (app/config.py)

```python
GEMINI_MODEL_CANDIDATES = ['gemini-2.0-flash', 'gemini-1.5-pro']
SUMMARY_CHUNK_SIZE = 2000
SUMMARY_MAX_RETRIES = 3
```

## Running the Application

### Development Mode (Local)

```bash
python app.py
# App starts at http://localhost:5000
# Auto-reloads on Python changes
```

### Production Mode

```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for containerization.

## Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/unit/test_search.py::TestRulebookSearch::test_basic_search -v

# With coverage
pytest tests/ --cov=app --cov=qa_tools
```

### Test Statistics
- **Total Tests**: 59
- **Passing**: 59/59 (100%)
- **Coverage**: 46.07%
- **Time**: ~2.3 seconds

See [TESTING.md](./docs/TESTING.md) for detailed testing guide.

## Documentation

| Document | Purpose |
|----------|---------|
| [GETTING_STARTED.md](./GETTING_STARTED.md) | Setup and first run |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Development workflow |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design and structure |
| [docs/API.md](./docs/API.md) | REST API reference |
| [docs/TESTING.md](./docs/TESTING.md) | Testing guide and patterns |
| [docs/DEVELOPMENT.md](./docs/DEVELOPMENT.md) | Development guidelines |
| [DEPLOYMENT.md](./DEPLOYMENT.md) | Production deployment |

## Performance

- **Search Speed**: < 100ms for typical queries
- **Index Size**: ~500KB (all rules indexed)
- **Memory Usage**: ~50MB running with search loaded
- **Concurrent Users**: Tested up to 50 concurrent searches

## Known Limitations

- Rulebook is Hungarian only (English translation planned)
- PDF penalty table requires OCR for full-text search
- Gemini API integration is optional (works without it)
- Some visual rules (diagrams, referee signals) are images only

## Deployment

### Render.com (Cloud)
- See [RENDER_DEPLOY.md](./RENDER_DEPLOY.md)
- One-click deployment from GitHub
- Automatic updates on push

### Local/VPS
- See [DEPLOYMENT.md](./DEPLOYMENT.md)
- Nginx + Gunicorn setup
- SSL certificate configuration

## Support & Issues

- 📖 **Questions?** Check [docs/](./docs/) directory
- 🐛 **Found a bug?** [Open an issue](https://github.com/SenkiAlphonse/HEMA-rulebook-hun/issues)
- 💬 **Want to contribute?** See [CONTRIBUTING.md](./CONTRIBUTING.md)

## License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. See [LICENSE](./LICENSE) file for details.

## Acknowledgments

- **HEMA Community**: For supporting and testing the Magyar Hosszúkardvívó Sportszövetség (Hungarian Longsword Federation, MHS) ruleset
- **FIE - International Fencing Federation**: Their comprehensive rulebooks have provided guidance and structural inspiration, enabling us to develop a detailed and well-organized ruleset for the Hungarian HEMA competition scene
- **Contributors**: For development, testing, and feedback
- **Google Gemini**: For AI-powered rule summarization (optional)

---

## Rulebook Navigation Index

### Quick Reference
- **Starting out?** → [Getting Started](./GETTING_STARTED.md)
- **Want to code?** → [Contributing Guide](./CONTRIBUTING.md)
- **Need APIs?** → [API Reference](./docs/API.md)
- **Deploying?** → [Deployment Guide](./DEPLOYMENT.md)

### Complete Rulebook Structure

**Introduction**
- [Bevezetés](01-altalanos.md)

**Equipment & Organization**
- [Felszerelés](02-szojegyzek.md)
- [Szervezés, bíráskodás](09-szervezes.md)
- [Vívó etikett és fegyelmi szabályzat](08-etikett_fegyelem.md)

**Fighting Rules**
- [Általánosan érvényes szabályok](03-felszereles.md)
- [Hosszúkardvívás általánosan érvényes szabályai](05-hosszukard.md)
- [Hosszúkardvívás VOR szabályai](05.a-hosszukard-VOR.md)
- [Hosszúkardvívás COMBAT szabályai](05.b-hosszukard-COMBAT.md)
- [Hosszúkardvívás AFTERBLOW szabályai](05.c-hosszukard-AFTERBLOW.md)
- [Párnázott fegyverek szabályai](fuggelek/06-rapir.md)

**References**
- [Szójegyzék (Glossary)](fuggelek/01-szojegyzek.md)
- [Az egyezményes elsőbbségi szabályok magyarázata](fuggelek/02-elsobbseg.md)
- [Szabálytalanságok és büntetések táblázatai](fuggelek/Buntetesek_tablazata.html)

---

**Last Updated**: 2024 | **Status**: Active Development | **Tests**: 59/59 Passing ✅

