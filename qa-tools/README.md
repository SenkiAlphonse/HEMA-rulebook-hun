# HEMA Rulebook Q&A Tools

AI-assisted question-answering system for the Hungarian HEMA (Historical European Martial Arts) rulebook.

## Quick Start

### 1. Create the Search Index

Parse all markdown rulebook files and create a searchable index:

```powershell
python qa-tools\parser.py
```

This will create `qa-tools/rules_index.json` containing all extracted rules.

### 2. Search the Rulebook

Run the interactive search CLI:

```powershell
python qa-tools\search.py
```

## Usage Examples

### Example Queries

**Hungarian queries:**
```
Query: találati felület
Query: hosszúkard vágás
Query: büntetés szabálytalanság
Query: felszerelés kesztyű
```

**English queries:**
```
Query: valid target areas
Query: longsword cut
Query: penalty rules
Query: equipment gloves
```

**Rule ID lookup:**
```
Query: GEN-1.1.1
Query: FEQ-2.3.4
```

### Search Results

The search engine returns:
- **Rule ID**: The unique identifier (e.g., GEN-1.1.1)
- **Document**: Source markdown file
- **Section/Subsection**: Hierarchical context
- **Rule Text**: Full rule description
- **Weapon Type & Variant**: If applicable (longsword VOR vs COMBAT)
- **Relevance Score**: How well the result matches your query

## System Architecture

### Components

1. **Parser (`parser.py`)**: 
   - Extracts rules from markdown files
   - Identifies rule IDs, sections, and anchors
   - Detects weapon types and variants from filenames
   - Outputs structured JSON index

2. **Search Engine (`search.py`)**:
   - Keyword-based search over rule text
   - Filters by weapon type and variant
   - Ranks results by relevance
   - Interactive CLI interface

3. **Index (`rules_index.json`)**:
   - Structured database of all rules
   - Fast lookup by ID, section, or keywords
   - Includes metadata for filtering

## How It Works

### Rule Extraction

The parser identifies rules using these patterns:

**Rule ID**: `**GEN-1.1.1**` (bold text with hierarchical numbering)
**Anchor ID**: `<span id="GEN-1"></span>` (HTML anchor for cross-references)
**Sections**: Markdown headings (#, ##, ###)

Example from `03-altalanos.md`:
```markdown
# Vívásra általánosan érvényes szabályok
<span id="GEN"></span>

## A mérkőzések menete
<span id="GEN-1"></span>

**GEN-1.1.1**  
Minden mérkőzés meghatározott ideig vagy meghatározott számú találatig...
```

### Search Scoring

Results are ranked using:
- **Exact rule ID match**: +100 points (highest priority)
- **Exact phrase in text**: +50 points
- **Exact phrase in section**: +30 points
- **Keyword frequency**: +10 points per occurrence
- **Section match**: +5 points
- **Weapon-specific bonus**: +10 points when relevant

## Extending the System

### Phase 2: Semantic Search

Upgrade to vector embeddings for natural language understanding:

```powershell
# Install dependencies
pip install sentence-transformers faiss-cpu

# Run semantic search (future enhancement)
python qa-tools\semantic_search.py
```

### Phase 3: Web Interface

Deploy a web application:

```powershell
# Install dependencies
pip install fastapi uvicorn

# Run web server
cd qa-tools
uvicorn web_api:app --reload

# Access at http://localhost:8000
```

### Phase 4: Conversational AI

Integrate with GPT-4 or Claude for multi-turn conversations:

```python
from qa_tools.rag import RulebookRAG

rag = RulebookRAG(index_path="qa-tools/rules_index.json")
response = rag.ask("Mik az érvényes találati felületek hosszúkardnál?")
```

## File Structure

```
qa-tools/
├── parser.py              # Markdown parser & indexer
├── search.py              # Keyword search engine
├── requirements.txt       # Python dependencies
├── rules_index.json       # Generated search index (after running parser)
└── README.md             # This file

docs/
└── qa-architecture.md     # Full system design document

.github/
└── copilot-instructions.md  # AI agent guidance
```

## Troubleshooting

**Index not found error**:
```
python qa-tools\parser.py
```

**No results found**:
- Try simpler keywords (e.g., "találat" instead of "találati felület")
- Use Hungarian terms (the rulebook is in Hungarian)
- Look up rule ID directly if you know it

**Parser errors**:
- Check that all markdown files follow the standard format
- Verify rule IDs use bold formatting: `**RULE-ID**`
- Ensure sections have proper heading markers (#, ##, ###)

## Future Enhancements

- [ ] Vector embeddings for semantic search
- [ ] Multilingual support (Hungarian ↔ English)
- [ ] Web interface with autocomplete
- [ ] Glossary term definitions in results
- [ ] Related rules suggestions
- [ ] Visual rule references (images, diagrams)
- [ ] PDF support for penalty tables
- [ ] Chatbot integration (Discord, Telegram)
- [ ] Judge certification quiz mode

## Contributing

To add support for new markdown files:

1. Add new .md file following naming convention
2. Update README.md navigation
3. Re-run parser: `python qa-tools\parser.py`
4. Test search: `python qa-tools\search.py`

No code changes needed—the parser auto-detects new files!

## License

Same as parent project (see LICENSE file).
