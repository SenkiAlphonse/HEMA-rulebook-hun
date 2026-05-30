"""
Markdown preprocessing and custom renderer utilities for HEMA rulebook app.
"""
import re

import mistune

from qa_tools.search_engine.search_utils import get_rule_depth


def preprocess_rulebook_markdown(text: str) -> str:
    """
    Preprocess markdown before Mistune conversion to handle:
    1. HTML comments removal
    2. Anchor spans preservation - attach to headers using special syntax
    3. Rule ID hard breaks converted to double newlines for separate paragraphs
    4. Rule ID references [RULE-ID] converted to clickable links
    """
    # Remove HTML comments (<!-- ... -->)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # Preserve anchor spans by attaching them to headers
    # Convert pattern: heading \n <span id="ID"></span> → heading {anchor:ID}
    # This format survives Mistune's inline markdown processing
    def preserve_header_anchors(text):
        lines = text.split('\n')
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Check if this is a heading
            if re.match(r'^#{1,6}\s+', line):
                # Check if next line is an anchor span
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    anchor_match = re.match(r'^<span\s+id="([^"]+)"></span>\s*$', next_line)
                    if anchor_match:
                        anchor_id = anchor_match.group(1)
                        # Append anchor notation to heading: ## Title → ## Title {anchor:ID}
                        # We append it with curly braces which are preserved through markdown
                        line = line + f' {{anchor:{anchor_id}}}'
                        i += 1  # Skip the anchor line since we've embedded it
                result.append(line)
            else:
                # Remove ALL anchor spans: both standalone AND inline
                line = re.sub(r'<span\s+id="[^"]*"></span>\s*', '', line)
                # Preserve blank lines so markdown structure remains intact,
                # especially after raw HTML blocks like <table>...</table>.
                result.append(line)
            i += 1
        return '\n'.join(result)

    text = preserve_header_anchors(text)

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


class RuleIDRenderer(mistune.HTMLRenderer):
    """Custom Mistune renderer that adds CSS classes to rule IDs for indentation"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_rule_depth = 0  # Track the depth of the last rule ID encountered

    def heading(self, text: str, level: int, **kwargs) -> str:
        """Override heading rendering to attach anchor IDs from preserved headers"""
        # Extract anchor ID from heading text using pattern {anchor:ID}
        # The pattern is appended to the heading text during preprocessing
        anchor_id = None
        cleaned_text = text

        # Match pattern: ... {anchor:SOME-ID}
        # Curly braces are preserved through Mistune's inline markdown processing
        anchor_pattern = re.compile(r'\s*\{anchor:([^}]+)\}\s*$')
        match = anchor_pattern.search(text)
        if match:
            anchor_id = match.group(1)
            # Remove the {anchor:...} pattern from the heading text
            cleaned_text = anchor_pattern.sub('', text)

        # Build heading with optional ID
        id_attr = f' id="{anchor_id}"' if anchor_id else ''
        return f'<h{level}{id_attr}>{cleaned_text}</h{level}>\n'

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
        start = kwargs.get('start')

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
