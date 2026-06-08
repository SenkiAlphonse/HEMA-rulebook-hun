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
