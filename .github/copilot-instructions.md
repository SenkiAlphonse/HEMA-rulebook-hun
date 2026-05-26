# AI Coding Instructions for the HEMA Rulebook Project

## Project Overview

This repository hosts the **Hungarian Historical European Martial Arts (HEMA)
rulebook** of the **Magyar Hosszúkardvívó Sportszövetség (MHS)** competition
ruleset, together with a small Flask web application that lets users browse
and search it in Hungarian and English.

The project is intentionally **not** an AI / RAG assistant. A previous
exploration into Retrieval-Augmented Generation with Gemini was abandoned and
all related code, configuration, and UI has been removed. Do **not** reintroduce
it without an explicit, deliberate change of scope.

## Mission

> A bilingual (HU/EN), searchable web rulebook for the MHS HEMA ruleset.
> It provides hierarchical rule lookup, alias-aware search, a pre-rendered
> rulebook viewer, and downloadable rule extracts — for fencers, referees,
> and organizers to quickly find authoritative rule passages.

The system is advisory in the sense that it surfaces rules; it does **not**
generate or summarize them.

## Audience

- **Fencers** — look up rules quickly by keyword, alias, or rule ID.
- **Referees** — find the precise wording when adjudicating.
- **Organizers** — reference disciplinary, organizational, and procedural rules.

## Repository Layout (high level)

```
rules/                Hungarian markdown rulebook chapters
rules_en/             English markdown rulebook chapters
fuggelek/             Appendices (glossary, penalty tables, etc.)
data/search/          Built JSON indexes and alias dictionaries
dist/                 Pre-rendered HTML rulebooks (built artifact)
src/app/              Flask application (factory, blueprints, utils, config)
src/qa_tools/         Parser, search engine, build/maintenance tools
templates/            Jinja2 templates for the web UI
tests/                pytest unit + integration tests
tools/                One-off and maintenance scripts (build, integrity checks)
examples/             Example/demo scripts for the qa_tools package
docs/                 Architecture, API, hierarchy, deployment notes
```

### Rule Chapter Files (`rules/`)

- `01-altalanos.md` — General rules (applies universally)
- `02-hosszukard.md` — Longsword base rules
- `02.a-hosszukard-VOR.md` — Longsword VOR variant
- `02.b-hosszukard-COMBAT.md` — Longsword COMBAT variant
- `02.c-hosszukard-AFTERBLOW.md` — Longsword AFTERBLOW variant
- `03-etikett_fegyelem.md` — Etiquette and discipline
- `04-szervezes.md` — Organization and refereeing

Future weapon chapters and appendices may be added under `rules/` and
`fuggelek/`.

## Rule IDs and Hierarchy

Rules use hierarchical, dotted IDs:

- `GEN-1`, `GEN-1.1`, `GEN-1.1.1`
- `DIS-2.1.2`, `ORG-3.4`, etc.

Anchors are stored with `<span id="...">` so the viewer can scroll directly to
any rule. Each indexed rule preserves:

- `rule_id`
- `text`
- `section` / `subsection`
- weapon type (`fegyvernem`)
- rule variant (`szabályváltozat`) — VOR / COMBAT / AFTERBLOW where applicable
- anchor id
- hierarchy (parent / children / lineage / depth)

**Rule IDs are authoritative.** If you change an ID anywhere, you must update
every reference to it. Use `tools/check_integrity.py` to detect duplicate IDs
and broken references.

## Search Behavior

- Alias-aware: HU/EN synonyms and common spelling variants resolve to canonical
  terms via `data/search/aliases.json`.
- Hierarchy-aware: more specific rules take precedence; parent context can be
  included when leaf rules are returned.
- Bilingual: separate indexes per language; the `rules_lang` request parameter
  selects which one is queried.
- The web UI offers keyword search, rule extracts by weapon/variant, and a
  pre-rendered full rulebook viewer.

There is no LLM call anywhere in the runtime path. Results are always
deterministic, computed from the indexed rules.

## What This Assistant May Do

When helping with this repository, AI agents should:

- Maintain and improve the parser, search engine, Flask app, and tests.
- Help fix rulebook content (typos, duplicate IDs, broken cross-references)
  — but **never** invent rules or change meaning. Domain edits go through the
  human maintainer.
- Suggest structural cleanups, but avoid reintroducing AI/LLM features.
- Treat Hungarian terminology with care; preserve it accurately.
- Distinguish *mandatory rules* from *referee discretion* when discussing
  content — but it is not the assistant's job to write referee advice.

## What This Assistant May NOT Do

- Do not add Gemini, OpenAI, Anthropic, LangChain, llama-index, vector stores,
  embeddings, or any other RAG/LLM infrastructure without an explicit,
  reviewed scope change.
- Do not generate "referee advice" or "tactical advice" features.
- Do not modify rule wording silently. Content changes must be obvious in the
  diff and reviewed by the maintainer.
- Do not renumber rule IDs without simultaneously updating every reference.

## Useful Entry Points

| Task                              | File / Folder                                         |
| --------------------------------- | ----------------------------------------------------- |
| App factory & route wiring        | `src/app/__init__.py`                                 |
| Search blueprint                  | `src/app/blueprints/search.py`                        |
| Rulebook viewer blueprint         | `src/app/blueprints/rulebook.py`                      |
| Search engine                     | `src/qa_tools/search_engine/`                         |
| Markdown rule parser              | `src/qa_tools/tools/parser.py`                        |
| Build the indexes + rendered HTML | `build.py` / `tools/build.py`                         |
| Integrity check (IDs & refs)      | `tools/check_integrity.py` (when present)             |
| Alias dictionary                  | `data/search/aliases.json`                            |
| Tests                             | `tests/unit/`, `tests/integration/`                   |
# AI Coding Instructions for HEMA Rulebook RAG Assistant

## Project Overview

This is a **Hungarian Historical European Martial Arts (HEMA) rulebook
repository** for the magyar Hosszúkardvívó Sportszövetség competition Ruleset.

The long-term goal is to build an **AI-assisted Retrieval-Augmented
Generation (RAG) system** that supports:

-   **Fencers** looking up rules quickly in natural language\
-   **Referees** handling unclear or stressful situations consistently\
-   **Organizers** clarifying disciplinary procedures and edge cases\
-   Future: **basic tactical/coaching guidance**, when safely possible

This is not just a keyword search tool --- it is intended to become a
**rule-grounded advisor**:

> Retrieve the relevant rule passages first, then generate a helpful
> answer strictly supported by those sources.

The assistant must remain **faithful to the rulebook**, avoid
hallucinating penalties, and always cite rule IDs.

------------------------------------------------------------------------

## Core Vision: RAG-Based Rules Advisor

The system follows a **Retrieval-Augmented Generation (RAG)**
architecture:

1.  User asks a question in natural language (Hungarian first)
2.  The system retrieves the most relevant rule chunks (plus parent
    context)
3.  The AI generates an answer **only using retrieved sources**
4.  The answer includes citations by `rule_id`
5.  If the rulebook does not contain enough information, the assistant
    must say so and ask clarifying questions

This ensures:

-   Accuracy and trust
-   No invented rules or sanctions
-   Maintainability as rules evolve

------------------------------------------------------------------------

## Ultimate Use Cases

### 1. Rule Lookup (Strict Mode)

-   "Is shouting a penalty?"
-   "What are valid target areas?"
-   "Does afterblow apply here?"

Answers must be grounded and cited.

------------------------------------------------------------------------

### 2. Refereeing Advisor (Nuanced Support)

The assistant should eventually help referees with:

-   Interpreting unclear situations
-   Applying proportional penalties
-   De-escalation language and soft skills
-   Match control guidance

Example:

-   "Is this emotional celebration or disruptive misconduct?"
-   "What warning ladder is appropriate?"

Important:

-   The assistant must distinguish **mandatory rules** vs **referee
    discretion**
-   It must never invent penalties not present in sources

------------------------------------------------------------------------

### 3. Fencer Support and Summaries

The assistant may provide:

-   Simple explanations of rules in plain language
-   Summaries of key obligations
-   "What should I know before fencing this variant?"

------------------------------------------------------------------------

### 4. Future Extension: Tactical/Coaching Advice (Optional)

Later, the assistant may provide limited tactical guidance such as:

-   Safe, general training suggestions
-   Tactical decision frameworks
-   Common referee expectations

But tactical advice must remain:

-   Clearly separated from rule authority
-   Conservative and non-hallucinatory
-   Never presented as official rules

------------------------------------------------------------------------

## Current Project Structure

### Rulebook Chapters (`rules/`)

-   `01-altalanos.md` --- General rules (applies universally)
-   `02-hosszukard.md` --- Longsword base rules
-   `02.a-hosszukard-VOR.md` --- Longsword VOR rule variant
-   `02.b-hosszukard-COMBAT.md` --- Longsword COMBAT rule variant
-   `02.c-hosszukard-AFTERBLOW.md` --- Longsword AFTERBLOW rule variant
-   `03-etikett_fegyelem.md` --- Etiquette and discipline
-   `04-szervezes.md` --- Organization and refereeing

### Future Content (`fuggelek/`)

Not yet indexed, but planned for expansion:

-   Additional weapon rule chapters
-   Penalty tables and disciplinary guidance
-   Forms and documents

------------------------------------------------------------------------

## Rule Numbering and Structure

Rules use hierarchical IDs:

-   `GEN-1`
-   `GEN-1.1`
-   `GEN-1.1.1`

Anchor IDs are stored with `<span id="...">` for precise referencing.

Each rule chunk should preserve:

-   `rule_id`
-   hierarchy level and lineage
-   parent-child relationships

------------------------------------------------------------------------

## Indexing and Retrieval Design

### Index Requirements

Each indexed rule chunk must include metadata:

-   `rule_id`
-   `text`
-   `section` / `subsection`
-   weapon type (`fegyvernem`)
-   rule variant (`szabályváltozat`)
-   anchor ID
-   hierarchy: parent/child/lineage

### Retrieval Rules

-   Specific overrides general
-   Leaf rules should include parent context when needed
-   The assistant must cite rule IDs in every answer

------------------------------------------------------------------------

## Query + Answer Contract


### Answer Output Format (Required)

All answers must use the following structure, with each section clearly labeled:

**A) Rule Summary**
- Plain language summary of the relevant rule(s), strictly grounded in cited sources
- Must include rule IDs and anchor IDs where possible

**B) Referee Advice**
- Interpretive, context-sensitive guidance for referees
- Must be clearly labeled as advice, not mandatory rule
- De-escalatory, proportional, and always cite supporting rules

**C) Coaching Advice**
- Optional, only if query is tactical or training-related
- Must be clearly separated from rule authority
- Never overrides or contradicts rules

**D) Clarifying Questions**
- If the query is ambiguous or could be interpreted as either referee or coaching advice, prompt the user for clarification
- Ask for more context if the rules do not provide a definitive answer

All sections should be present in the output, even if some are empty (e.g., "No coaching advice applicable.").

------------------------------------------------------------------------

## Development Workflow

### Phase 1 --- Parsing

-   Extract markdown rules
-   Build hierarchical rule nodes
-   Preserve anchors and IDs

### Phase 2 --- Indexing

-   Store rules in structured JSON
-   Add alias mappings
-   Support parent inclusion for deep rules

### Phase 3 --- RAG Answering

-   Retrieve top rule passages
-   Generate grounded responses via OpenAI API
-   Require citations and safe fallback behavior

### Phase 4 --- Scenario Library (Referee "Case Law")

-   Add curated examples for nuanced officiating
-   Improve consistency for soft-skill situations

------------------------------------------------------------------------

## Notes for AI Agents (Copilot, Claude, ChatGPT)

-   Rules are authoritative; the assistant is advisory
-   Preserve IDs and hierarchy at all times
-   Hungarian terminology must remain accurate
-   Variant awareness is essential
-   Referee guidance must be proportional, calm, and de-escalatory
-   Tactical advice is optional and must never override rules

------------------------------------------------------------------------

## File References

  Task                     File
  ------------------------ ------------------------------
    Rule parsing/indexing    `src/qa_tools/tools/` scripts
    Alias expansion          `data/search/aliases.json`
  Add scenario exemplars   `docs/scenarios.md` (future)
  Extend rulebook          `rules/*.md`
