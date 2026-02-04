# AI-Assisted Q&A Solution Architecture

## System Overview

Build a semantic Q&A system that allows users to query the HEMA rulebook using natural language in both Hungarian and English, returning precise rule citations with full context.

## Architecture Components

### 1. Document Parser & Indexer
**Purpose**: Extract structured data from markdown rulebooks

**Input**: Markdown files from root and `fuggelek/` directories
**Output**: Structured JSON index with rules, metadata, and relationships

**Key Features**:
- Parse markdown headings, bold rule IDs (e.g., `**GEN-1.1.1**`), and anchor spans (`<span id="...">`)
- Extract hierarchical structure: Document → Section → Subsection → Rule
- Build glossary mapping from `fuggelek/01-szojegyzek.md`
- Track cross-references between rules
- Extract image references for visual rule representation

**Technology Options**:
- Python + `markdown` library + regex for parsing
- Node.js + `markdown-it` for processing
- Save index as JSON for fast retrieval

### 2. Semantic Search Engine
**Purpose**: Enable natural language queries over rulebook content

**Approach A: Vector Embeddings (Recommended)**
- Use sentence transformers (e.g., `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`)
- Embed each rule text + metadata
- Store in vector database (Chroma, Pinecone, or FAISS for local)
- Query: Convert user question to embedding, find nearest neighbors

**Approach B: Traditional Search (Simpler)**
- Use full-text search (Elasticsearch, Lunr.js)
- Support Hungarian + English keywords
- Weight by rule hierarchy (specific weapon rules > general rules)

**Hybrid Approach** (Best for accuracy):
- Combine vector similarity with keyword matching
- Use BM25 algorithm for keyword relevance
- Re-rank results using semantic similarity

### 3. Query Interface
**Purpose**: User-facing application to ask questions

**Option A: Web Application**
- Simple HTML/CSS/JS frontend
- FastAPI/Flask backend (Python) or Express (Node.js)
- Real-time search with autocomplete suggestions
- Display: Rule ID, full text, section context, related rules

**Option B: CLI Tool**
- Command-line interface for quick lookups
- Example: `python qa.py "Mik az érvényes találati felületek hosszúkardnál?"`
- Returns formatted rule citations

**Option C: Chatbot Integration**
- Integrate with Discord, Telegram, or Slack
- Conversational interface for fencers and judges
- Example: "@hemabot what are valid target areas for longsword?"

### 4. Context Enhancement
**Purpose**: Provide comprehensive answers by including related information

**Features**:
- **Glossary lookup**: If query contains Hungarian HEMA term, include definition
- **Variant detection**: Flag when rules differ by weapon variant (VOR vs COMBAT)
- **Hierarchy traversal**: Show parent section context for clarity
- **Related rules**: Suggest cross-referenced or semantically similar rules
- **Visual aids**: Include links to images (target areas, referee signals)

## Implementation Roadmap

### Phase 1: MVP (Minimum Viable Product)
1. **Parser**: Extract all rules from markdown files into JSON
2. **Simple search**: Keyword-based search over rule text
3. **CLI interface**: Basic command-line query tool
4. **Testing**: Verify with sample queries

**Estimated effort**: 1-2 days

### Phase 2: Semantic Search
1. **Embeddings**: Generate vector embeddings for all rules
2. **Vector database**: Set up Chroma or FAISS locally
3. **Hybrid search**: Combine keyword + semantic matching
4. **Multilingual support**: Handle both Hungarian and English queries

**Estimated effort**: 2-3 days

### Phase 3: Web Interface
1. **Frontend**: Simple React or vanilla JS search UI
2. **Backend API**: REST endpoints for querying
3. **Result display**: Show rule ID, text, context, related rules
4. **Deployment**: Host on GitHub Pages + serverless function

**Estimated effort**: 3-4 days

### Phase 4: Advanced Features (Optional)
1. **Conversational AI**: Multi-turn conversations using GPT-4 or Claude with RAG
2. **Admin panel**: Update rules, retrain index without redeploying
3. **Analytics**: Track popular queries, improve ranking
4. **PDF support**: Extract and index penalty tables

**Estimated effort**: 1 week+

## Technology Stack Recommendations

### Option A: Python Stack (Recommended for ML capabilities)
```
- Parser: Python + markdown library
- Search: sentence-transformers + FAISS/Chroma
- Backend: FastAPI
- Frontend: Static HTML/JS with Fetch API
- Deployment: Docker container or Python anywhere
```

### Option B: JavaScript Stack (Simpler for web deployment)
```
- Parser: Node.js + markdown-it
- Search: Lunr.js or Fuse.js (client-side)
- Backend: Express.js
- Frontend: React or Vue.js
- Deployment: Vercel/Netlify
```

### Option C: Hybrid (Best of both worlds)
```
- Parser: Python (better text processing)
- Search: Python backend with REST API
- Frontend: Modern JS framework
- Deployment: Backend on Render/Railway, frontend on Netlify
```

## Sample Usage Flows

### Flow 1: Judge Looking for Target Area Rule
**Query**: "Mik az érvényes találati felületek hosszúkardnál?"
(What are valid target areas for longsword?)

**System Response**:
```
Found 2 relevant rules:

[04-hosszukard.md] Rule: Érvényes találati felület
Section: A Hosszúkardvívás általános szabályai

1. Csak azok a találatok érvényesek, amelyek az érvényes találati felületre esnek.

2. Érvényes találati felület magában foglalja a vívó egész testét, beleértve a 
fegyver markolatát, a ruházatot és a védőfelszerelést, kivéve a fej hátulja, 
a gerinc, a lábfejek és a térdek hátsó része.

[Image: target_blue.png - Blue areas show valid targets]

Related rules:
- GEN-1.3 (General target rules)
- 04.c-3.2 (AFTERBLOW specific target rules)
```

### Flow 2: Competitor Checking Equipment
**Query**: "Can I use gloves without thumb protection?"

**System Response**:
```
Found 1 relevant rule:

[02-felszereles.md] Rule: FEQ-2.3.4
Section: Védőfelszerelés követelményei

A kezeket védő kesztyűknek legalább 1,5mm-es, kemény markolat alakú kézfej 
protektornak kell lenniük. A kesztyűk megfelelő ujjvédelemmel kell 
rendelkezzenek...

Glossary term: "ujjvédelem" = finger protection

⚠ Answer: No. All gloves must include finger and thumb protection.
```

## Extensibility

### Adding New Weapon Types
1. Add markdown file following naming convention: `05-rapir.md`
2. Update `README.md` navigation
3. Re-run parser to index new rules
4. System automatically includes in search

### Multilingual Support
- Extend parser to detect language
- Add English translations as metadata
- Query in either language, return in user's language
- Use translation API (DeepL, Google Translate) for dynamic translation

### Future Data Sources
- Competition results (who violated which rules)
- Video examples of rules in action
- Interactive rule quizzes for judges and competitors

## Next Steps

1. **Choose technology stack** based on your preferences:
   - Python for ML-heavy approach
   - JavaScript for web-first approach
   
2. **Start with Phase 1 MVP**: Get basic indexing and search working

3. **Iterate based on user feedback**: Test with real fencers and judges

Would you like me to proceed with implementing the Q&A system? If so, which technology stack do you prefer?
