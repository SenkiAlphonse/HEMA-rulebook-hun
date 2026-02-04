# AI Coding Instructions for HEMA Rulebook Project

## Project Overview

This is a **Hungarian Historical European Martial Arts (HEMA) rulebook repository** for the "Kard Rendje" (Order of the Sword) competition ruleset. The goal is to create an **AI-assisted Q&A solution** that indexes and queries rulebook markdown files to help fencers, judges, and organizers find relevant rules quickly using natural language.

### Current Project Structure

- **Main rulebook chapters** (8 numbered markdown files):
  - `01-bevezetes.md` - Introduction
  - `02-felszereles.md` - Equipment and gear requirements
  - `03-altalanos.md` - General rules applying to all weapons
  - `04-hosszukard.md` - Longsword general rules
  - `04.a-hosszukard-VOR.md` - Longsword VOR (Vorbeigehen) variant
  - `04.b-hosszukard-COMBAT.md` - Longsword COMBAT variant
  - `04.c-hosszukard-AFTERBLOW.md` - Longsword AFTERBLOW variant
  - `07-szervezes-biraskodas.md` - Organization and refereeing
  - `08-etikett_fegyelem.md` - Etiquette and discipline

- **Appendices** (`fuggelek/`):
  - `01-szojegyzek.md` - Glossary of terms
  - `02-elsobbseg.md` - Convention priority rules explanation

- **Metadata**: README.md contains the complete index/navigation structure

## Key Content Patterns

### Rule Numbering System
Rules follow a hierarchical numbering scheme using hyphens (e.g., `GEN-1.1.1`, `GEN-1.2.3`):
- First part (e.g., `GEN`) = section code
- Numbers = hierarchical level (1 = main section, 1.1 = subsection, 1.1.1 = rule)
- Anchor IDs use `<span id="...">` HTML tags for cross-referencing

**Example from 03-altalanos.md:**
```markdown
# Vívásra általánosan érvényes szabályok
<span id="GEN"></span>

## A mérkőzések menete
<span id="GEN-1"></span>

**GEN-1.1.1**  
Rule text explaining meeting structure...
```

### Content Structure
1. **Headings** (#, ##, ###) define logical sections
2. **Bold rule IDs** (e.g., `**GEN-1.1.1**`) precede rule statements
3. **Images** embedded via GitHub markdown for visual rules (target areas, positions)
4. **Cross-references** use explicit mentions or anchor IDs for lookup
5. **Lists** (numbered and bulleted) explain multi-part rules

## Q&A Solution Design Considerations

### What Makes Rules Queryable
- **Hierarchical structure**: Q&A system should preserve section/subsection relationships
- **Anchor IDs**: Use these for precise cross-references in answers
- **Hungarian terminology**: Include both Hungarian rule ID (e.g., "GEN-1.1.1") and descriptions
- **Variants**: Same base rule may differ between weapon types (longsword VOR vs COMBAT) or equipment rules

### Critical Integration Points
1. **Glossary lookup** (`fuggelek/01-szojegyzek.md`): Q&A must resolve Hungarian HEMA terms
2. **Priority rules** (`fuggelek/02-elsobbseg.md`): Explains hierarchy for ambiguous situations
3. **Penalty tables** (PDF format): Referenced for enforcement - may need OCR for full Q&A capability
4. **Equipment rules** (02-felszereles.md): Prerequisite for understanding valid vs invalid techniques

### Domain-Specific Challenges
- **Language**: All content in Hungarian; Q&A should preserve accuracy of technical terms
- **Multi-weapon context**: Rules in `03-altalanos.md` apply to all weapons, but specific chapters override/clarify
- **Variant rules**: Longsword has 3 competition variants (VOR, COMBAT, AFTERBLOW) with significant differences
- **Visual rules**: Target areas, positions, and referee signals include images—consider multimodal indexing for complete understanding

## Development Workflow

### For Building the Q&A System

1. **Parsing Phase**:
   - Extract all markdown files from root and `fuggelek/` directory
   - Parse rule IDs (e.g., `GEN-1.1.1`) and anchor IDs
   - Build hierarchical relationships: document → section → subsection → rule

2. **Indexing Phase**:
   - Index full rule text with metadata: rule ID, section, anchor, weapon type (if applicable)
   - Create glossary mappings for Hungarian terms (from `01-szojegyzek.md`)
   - Flag cross-references and variant overrides

3. **Query Phase**:
   - Accept natural language queries in Hungarian or English
   - Return relevant rules with full context (section, rule ID, anchor)
   - Rank by hierarchical relevance (specific weapon rules > general rules)
   - Suggest related rules from glossary or cross-references

### Testing Recommendations
- **Sample queries**: "What are valid target areas for longsword?" → should return relevant rules from both 03-altalanos.md and 04-hosszukard.md
- **Variant handling**: "Can you use COMBAT techniques in VOR competition?" → should return rules showing distinctions
- **Term resolution**: "What is a 'szúrás'?" → should resolve from glossary and show usage in rules

## File References for Common Tasks

| Task | Key Files |
|------|-----------|
| Add Q&A training examples | Create `docs/qa-examples.md` or extend README.md |
| Update rule structure | Modify affected chapter + update README.md TOC |
| Add new weapon type | Create new chapter following naming pattern `04.*-*.md` |
| Extend Q&A system | Add parsing logic for new file types (currently markdown + PDF) |
| Glossary expansion | Edit `fuggelek/01-szojegyzek.md` with new Hungarian terms |

## Notes for AI Agents

- **Context is distributed**: Understanding a rule often requires reading 03-altalanos.md (general), the specific weapon chapter, and sometimes the glossary
- **Preserve structure**: When extracting or summarizing rules, maintain rule IDs and anchor references for accuracy
- **Hungarian accuracy**: When translating or explaining rules, verify Hungarian terms against the glossary
- **Variant awareness**: Always note which rules apply universally vs. only to specific weapon variants
