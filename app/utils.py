"""
Shared utilities for HEMA rulebook app
"""

import re
import mistune


def preprocess_rulebook_markdown(text):
    """
    Preprocess markdown before Mistune conversion to handle:
    1. HTML comments removal
    2. Rule ID hard breaks converted to double newlines for separate paragraphs
    """
    # Remove HTML comments (<!-- ... -->)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # Convert rule ID hard breaks to double newlines
    # Pattern: **RULE-ID**  \n (two trailing spaces + newline) → **RULE-ID**\n\n
    text = re.sub(r'(\*\*[A-Z]+-[\d\.]+\*\*)  \n', r'\1\n\n', text)
    
    return text


def get_rule_depth(rule_id):
    """Calculate indentation depth from rule ID (e.g., GEN-6.10.4.1 = depth 4)"""
    if not rule_id:
        return 0
    parts = rule_id.split('-')
    if len(parts) < 2:
        return 0
    numeric_part = parts[1]
    return numeric_part.count('.') + 1


class RuleIDRenderer(mistune.HTMLRenderer):
    """Custom Mistune renderer that adds CSS classes to rule IDs for indentation"""
    
    def paragraph(self, text):
        """Override paragraph rendering to detect and style rule IDs"""
        # Check if this is a rule ID line: <strong>GEN-X.X.X</strong>
        if text.startswith('<strong>') and text.endswith('</strong>'):
            # Extract rule ID from <strong> tags
            rule_id = text.replace('<strong>', '').replace('</strong>', '').strip()
            
            # Validate it looks like a rule ID (PREFIX-numeric.numeric.numeric...)
            if '-' in rule_id and rule_id.split('-')[0].isalpha():
                depth = get_rule_depth(rule_id)
                indent_class = f'rule-depth-{depth}' if depth > 0 else ''
                return f'<p class="rule-id {indent_class}">{text}</p>\n'
        
        # Regular paragraph
        return f'<p>{text}</p>\n'
    
    def list(self, text, ordered, **kwargs):
        """Override list rendering to add bullet-list CSS class"""
        # Extract known parameters, ignore others
        start = kwargs.get('start', None)
        
        if ordered:
            tag = 'ol'
            extra = f' start="{start}"' if start is not None else ''
        else:
            tag = 'ul'
            extra = ' class="bullet-list"'
        return f'<{tag}{extra}>\n{text}</{tag}>\n'
    
    def block_html(self, text):
        """Override block HTML to filter out comments while preserving other HTML"""
        # Filter HTML comments but keep other HTML blocks like <span id="...">
        if text.strip().startswith('<!--'):
            return ''
        return text


def create_mistune_markdown():
    """Create a Mistune markdown instance with HTML preservation and custom renderer"""
    return mistune.create_markdown(
        renderer=RuleIDRenderer(),
        escape=False  # Preserve HTML blocks like <table>, <div>, <span id=...>
    )


def normalize_filter(value, allowed):
    """Validate and normalize filter values"""
    if value and value in allowed:
        return value
    return None


def build_document_order(rules):
    """Build a mapping of document names to sequence index for sorting"""
    order = {}
    next_index = 0
    for rule in rules:
        doc = rule.get("document", "")
        if doc and doc not in order:
            order[doc] = next_index
            next_index += 1
    return order


def filter_rules_for_extract(rules, weapon_filter, formatum_filter):
    """Filter rules by weapon type and format"""
    filtered = []
    for rule in rules:
        rule_weapon = rule.get("weapon_type", "general")
        rule_formatum = rule.get("formatum") or ""

        if weapon_filter and rule_weapon not in ["general", weapon_filter]:
            continue

        if formatum_filter and rule_formatum not in ["", formatum_filter]:
            continue

        filtered.append(rule)
    return filtered


def format_extract_text(rules, weapon_filter, formatum_filter):
    """Format filtered rules into markdown extract"""
    title_parts = ["Rulebook Extract"]
    if weapon_filter:
        title_parts.append(f"Weapon: {weapon_filter}")
    if formatum_filter:
        title_parts.append(f"Format: {formatum_filter}")

    doc_order = build_document_order(rules)
    sorted_rules = sorted(
        rules,
        key=lambda r: (
            doc_order.get(r.get("document", ""), 9999),
            int(r.get("line_number", 0)),
            r.get("rule_id", "")
        )
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
