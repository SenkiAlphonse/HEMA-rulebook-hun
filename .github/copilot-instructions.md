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
  Rule parsing/indexing    `qa-tools/` scripts
  Alias expansion          `qa_tools/aliases.json`
  Add scenario exemplars   `docs/scenarios.md` (future)
  Extend rulebook          `rules/*.md`
