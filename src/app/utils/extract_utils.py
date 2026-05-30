"""
Rule extraction and formatting utilities for HEMA rulebook app.
"""

from typing import Any


def build_document_order(rules: list[dict[str, Any]]) -> dict[str, int]:
    """Build a mapping of document names to sequence index for sorting"""
    order = {}
    next_index = 0
    for rule in rules:
        doc = rule.get("document", "")
        if doc and doc not in order:
            order[doc] = next_index
            next_index += 1
    return order


def read_rulebook_markdown_content(lang: str = "hun") -> str:
    """
    Read and concatenate all rulebook markdown files.
    Shared utility to eliminate duplication between build.py and rulebook.py

    Args:
        lang: Language code, 'hun' (Hungarian, default) or 'eng' (English).

    Returns:
        Concatenated markdown content with separator sections
    """
    if lang == "eng":
        from app.config import get_rulebook_markdown_files_en

        md_files = get_rulebook_markdown_files_en()
    else:
        from app.config import get_rulebook_markdown_files

        md_files = get_rulebook_markdown_files()

    content = ""

    for md_file in md_files:
        if md_file.exists():
            with open(md_file, encoding="utf-8") as f:
                content += f.read() + "\n\n---\n\n"

    return content


def filter_rules_for_extract(
    rules: list[dict[str, Any]], weapon_filter: str | None, variant_filter: str | None
) -> list[dict[str, Any]]:
    """Filter rules by weapon type and variant"""
    filtered = []
    for rule in rules:
        rule_weapon = rule.get("weapon_type", "general")
        rule_variant = rule.get("variant") or ""

        if weapon_filter and rule_weapon not in ["general", weapon_filter]:
            continue

        if variant_filter and rule_variant not in ["", variant_filter]:
            continue

        filtered.append(rule)
    return filtered


def format_extract_text(
    rules: list[dict[str, Any]], weapon_filter: str | None, variant_filter: str | None
) -> str:
    """Format filtered rules into markdown extract"""
    title_parts = ["Rulebook Extract"]
    if weapon_filter:
        title_parts.append(f"Weapon: {weapon_filter}")
    if variant_filter:
        title_parts.append(f"Variant: {variant_filter}")

    doc_order = build_document_order(rules)
    sorted_rules = sorted(
        rules,
        key=lambda r: (
            doc_order.get(r.get("document", ""), 9999),
            int(r.get("line_number", 0)),
            r.get("rule_id", ""),
        ),
    )

    output_lines = []
    output_lines.append("# " + " | ".join(title_parts))
    output_lines.append("")

    current_doc = None
    current_section = None
    current_subsection = None

    for rule in sorted_rules:
        doc = rule.get("document", "")
        section = rule.get("section", "")
        subsection = rule.get("subsection", "")

        if doc != current_doc:
            output_lines.append(f"\n## Document: {doc}")
            current_doc = doc
            current_section = None
            current_subsection = None

        if section and section != current_section:
            output_lines.append(f"\n### {section}")
            current_section = section
            current_subsection = None

        if subsection and subsection != current_subsection:
            output_lines.append(f"\n#### {subsection}")
            current_subsection = subsection

        output_lines.append(f"\n**{rule.get('rule_id', '')}**")
        output_lines.append(rule.get("text", "").strip())

    output_lines.append("")
    return "\n".join(output_lines)
