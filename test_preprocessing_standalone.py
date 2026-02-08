#!/usr/bin/env python
"""
Standalone test script for markdown preprocessing
"""

import re
import mistune


def preprocess_rulebook_markdown(text):
    """
    Preprocess markdown before Mistune conversion
    """
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # Convert rule ID hard breaks to double newlines
    text = re.sub(r'(\*\*[A-Z]+-[\d\.]+\*\*)  \n', r'\1\n\n', text)
    
    return text


def get_rule_depth(rule_id):
    """Calculate indentation depth from rule ID"""
    if not rule_id:
        return 0
    parts = rule_id.split('-')
    if len(parts) < 2:
        return 0
    numeric_part = parts[1]
    return numeric_part.count('.') + 1


class RuleIDRenderer(mistune.HTMLRenderer):
    """Custom Mistune renderer"""
    
    def paragraph(self, text):
        if text.startswith('<strong>') and text.endswith('</strong>'):
            rule_id = text.replace('<strong>', '').replace('</strong>', '').strip()
            if '-' in rule_id and rule_id.split('-')[0].isalpha():
                depth = get_rule_depth(rule_id)
                indent_class = f'rule-depth-{depth}' if depth > 0 else ''
                return f'<p class="rule-id {indent_class}">{text}</p>\n'
        return f'<p>{text}</p>\n'
    
    def list(self, text, ordered, level, start=None):
        if ordered:
            tag = 'ol'
            extra = f' start="{start}"' if start is not None else ''
        else:
            tag = 'ul'
            extra = ' class="bullet-list"'
        return f'<{tag}{extra}>\n{text}</{tag}>\n'
    
    def block_html(self, text):
        if text.strip().startswith('<!--'):
            return ''
        return text


def create_mistune_markdown():
    """Create Mistune instance"""
    return mistune.create_markdown(
        renderer=RuleIDRenderer(),
        escape=False
    )


def test_preprocessing():
    """Test the preprocessing function"""
    
    # Test comment removal
    test_md_1 = """# Test Header
<!-- This is a comment -->
Some text here.
<!-- Another comment -->
More text."""
    
    print("=== Test 1: Comment Removal ===")
    print("Input:")
    print(test_md_1)
    result_1 = preprocess_rulebook_markdown(test_md_1)
    print("\nOutput:")
    print(result_1)
    print("\n✓ Comments removed:", "<!--" not in result_1)
    
    # Test rule ID hard break conversion
    test_md_2 = """**GEN-1.1.1**  
This is the rule text.

**GEN-1.1.2**  
Another rule text."""
    
    print("\n=== Test 2: Rule ID Hard Break Conversion ===")
    print("Input:")
    print(repr(test_md_2))
    result_2 = preprocess_rulebook_markdown(test_md_2)
    print("\nOutput:")
    print(repr(result_2))
    print("\n✓ Hard breaks converted to double newlines:", "**  \n" not in result_2)
    
    # Test full rendering
    print("\n=== Test 3: Full Rendering ===")
    test_md_3 = """<!-- Comment to remove -->
**GEN-6.1**  
First rule text.

**GEN-6.1.1**  
Nested rule text.

- Bullet point 1
- Bullet point 2
  - Nested bullet
"""
    
    print("Input markdown:")
    print(test_md_3)
    
    preprocessed = preprocess_rulebook_markdown(test_md_3)
    print("\nAfter preprocessing:")
    print(preprocessed)
    
    md = create_mistune_markdown()
    html = md(preprocessed)
    print("\nRendered HTML:")
    print(html)
    
    print("\n=== Validation ===")
    print(f"✓ Comments removed: {'<!--' not in html}")
    print(f"✓ Rule IDs have CSS classes: {'class=\"rule-id' in html}")
    print(f"✓ Bullet lists have CSS class: {'class=\"bullet-list\"' in html}")
    print(f"✓ Depth classes present: {'rule-depth-' in html}")


if __name__ == "__main__":
    test_preprocessing()
