"""
Shared utilities for HEMA rulebook app
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import mistune

# Add qa-tools to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'qa-tools'))
from search_utils import get_rule_depth


def preprocess_rulebook_markdown(text: str) -> str:
    """
    Preprocess markdown before Mistune conversion to handle:
    1. HTML comments removal
    2. Anchor spans removal (<span id="..."></span>)
    3. Rule ID hard breaks converted to double newlines for separate paragraphs
    4. Rule ID references [RULE-ID] converted to clickable links
    """
    # Remove HTML comments (<!-- ... -->)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # Remove anchor spans (<span id="..."></span>)
    text = re.sub(r'<span\s+id="[^"]*"></span>\s*', '', text, flags=re.IGNORECASE)
    
    # Convert rule ID references [RULE-ID] to clickable links
    # Pattern: [GEN-6.2.4] → <a href="#GEN-6.2.4" class="rule-ref" data-rule-id="GEN-6.2.4">GEN-6.2.4</a>
    # Supports multi-part prefixes like LS-VOR-1.1.3, LS-COMBAT-1.2.1.1, LS-AB-1.2.10.2
    text = re.sub(
        r'\[([A-Z]+(?:-[A-Z]+)*-[\d\.]+)\]',
        r'<a href="#\1" class="rule-ref" data-rule-id="\1">\1</a>',
        text
    )
    
    # Convert rule ID hard breaks to double newlines
    # Pattern: **RULE-ID**␠␠\n → **RULE-ID**\n\n
    # Supports multi-part prefixes
    text = re.sub(r'(\*\*[A-Z]+(?:-[A-Z]+)*-[\d\.]+\*\*)  \r?\n', r'\1\n\n', text)
    
    return text


# Note: get_rule_depth is now imported from search_utils


class RuleIDRenderer(mistune.HTMLRenderer):
    """Custom Mistune renderer that adds CSS classes to rule IDs for indentation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_rule_depth = 0  # Track the depth of the last rule ID encountered
    
    def paragraph(self, text: str) -> str:
        """Override paragraph rendering to detect and style rule IDs"""
        # Match paragraphs that start with a rule ID
        # Supports multi-part prefixes like LS-VOR-1.1.3, LS-COMBAT-1.2.1.1
        match = re.match(r'^<strong>([A-Z]+(?:-[A-Z]+)*-[\d\.]+)</strong>', text)
        if match:
            rule_id = match.group(1)
            if '-' in rule_id and rule_id.split('-')[0].isalpha():
                depth = get_rule_depth(rule_id)
                self.last_rule_depth = depth  # Remember this depth for following paragraphs
                
                # Apply indent class for depth 4 and 5
                indent_class = f'rule-depth-{depth}' if depth >= 4 else ''
                class_attr = f'rule-id {indent_class}' if indent_class else 'rule-id'
                
                # Reset tracking if we encounter a shallower rule (parent/sibling level)
                if depth < 4:
                    self.last_rule_depth = 0
                
                # Add an anchor ID for navigation
                return f'<p class="{class_attr}" id="{rule_id}">{text}</p>\n'

        # Regular paragraph following a rule ID should inherit its indentation if depth >= 4
        if self.last_rule_depth >= 4:
            indent_class = f'rule-depth-{self.last_rule_depth}'
            return f'<p class="{indent_class}">{text}</p>\n'
        
        # Regular paragraph without indentation
        return f'<p>{text}</p>\n'
    
    def list(self, text: str, ordered: bool, **kwargs) -> str:
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
    
    def block_html(self, text: str) -> str:
        """Override block HTML to filter out comments and anchor spans"""
        stripped = text.strip()
        if stripped.startswith('<!--'):
            return ''
        if stripped.startswith('<span') and 'id=' in stripped:
            return ''
        return text
    
    def inline_html(self, html: str) -> str:
        """Override inline HTML to preserve rule reference links but filter comments and spans"""
        # Filter out HTML comments
        if html.strip().startswith('<!--'):
            return ''
        # Filter out anchor spans
        if html.strip().startswith('<span') and 'id=' in html:
            return ''
        # Allow other inline HTML (like rule reference <a> tags) to pass through
        return html


def create_mistune_markdown() -> mistune.Markdown:
    """Create a Mistune markdown instance with HTML preservation and custom renderer"""
    return mistune.create_markdown(
        renderer=RuleIDRenderer(),
        escape=False,  # Preserve HTML blocks like <table>, <div>, <span id=...>
        plugins=['url', 'strikethrough', 'table']  # Enable plugins including HTML rendering
    )


def normalize_filter(value: Optional[str], allowed: List[str]) -> Optional[str]:
    """Validate and normalize filter values"""
    if value and value in allowed:
        return value
    return None


def build_document_order(rules: List[Dict[str, Any]]) -> Dict[str, int]:
    """Build a mapping of document names to sequence index for sorting"""
    order = {}
    next_index = 0
    for rule in rules:
        doc = rule.get("document", "")
        if doc and doc not in order:
            order[doc] = next_index
            next_index += 1
    return order


def get_rulebook_markdown_files_util() -> List[Path]:
    """
    Get all numbered markdown rulebook files from root directory.
    Shared utility to avoid duplication between build.py and rulebook.py
    
    Returns:
        List of Path objects for markdown files in order
    """
    from app.config import get_rulebook_markdown_files
    return get_rulebook_markdown_files()


def read_rulebook_markdown_content() -> str:
    """
    Read and concatenate all rulebook markdown files.
    Shared utility to eliminate duplication between build.py and rulebook.py
    
    Returns:
        Concatenated markdown content with separator sections
    """
    from app.config import get_rulebook_markdown_files
    
    md_files = get_rulebook_markdown_files()
    content = ""
    
    for md_file in md_files:
        if md_file.exists():
            with open(md_file, 'r', encoding='utf-8') as f:
                content += f.read() + "\n\n---\n\n"
    
    return content


def filter_rules_for_extract(
    rules: List[Dict[str, Any]],
    weapon_filter: Optional[str],
    formatum_filter: Optional[str]
) -> List[Dict[str, Any]]:
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


def format_extract_text(
    rules: List[Dict[str, Any]],
    weapon_filter: Optional[str],
    formatum_filter: Optional[str]
) -> str:
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
