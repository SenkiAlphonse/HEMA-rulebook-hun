# Changelog

All notable changes to the **MHS HEMA rulebook** and the rulebook web app are
recorded here. The list is curated by hand.

This file has two independent histories:

- **Ruleset** — changes to the published rules (wording, IDs, structure).
  Each entry has a version number (e.g. `2026.1`) shown in the site footer.
- **App / site** — changes to the search engine, web UI, build tooling, etc.
  Dated, but not versioned — these have no effect on rulings.

---

## Ruleset

### [2026.1] — 2026-06-02

First versioned snapshot of the MHS HEMA ruleset published on the site.
**No rule wording changes** from the previous unversioned state; this entry
exists only to anchor the version number that the site footer now displays.

[2026.1]: https://github.com/SenkiAlphonse/HEMA-rulebook-hun

---

## App / site

### 2026-06-02

- Per-rule **copy-link** buttons in search results and the full rulebook
  viewer. Copied links preserve the language (`?lang=hun`/`eng`) the reader
  is currently viewing.
- **"Did you mean…"** suggestion when a search returns no results, using
  the existing alias-aware fuzzy matcher.
- English translation of chapter `02.b — Longsword COMBAT`
  (`rules_en/02.b-longsword-COMBAT.en.md`). Pending human review.
- Structured search-query logging (no PII; stdout only) so future alias
  audits can be driven by real user queries.
- Print stylesheet for the full rulebook viewer.
- Larger tap targets on touch devices for the copy-link buttons.
- 404 handler for browsers now redirects to the canonical home page instead
  of re-rendering the full app shell.
- Internal cleanups: consolidated `src/app/utils/`, replaced the
  `_expand_query` 5-tuple with an `ExpandedQuery` dataclass, added a
  `pre-commit` config.
