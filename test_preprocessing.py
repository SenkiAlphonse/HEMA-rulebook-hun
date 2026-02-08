#!/usr/bin/env python
"""
Test script to verify markdown preprocessing and rendering
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils import preprocess_rulebook_markdown, create_mistune_markdown


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
    print("\nComments removed:", "<!--" not in result_1)
    
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
    print("\nHard breaks converted to double newlines:", "**  \n" not in result_2)
    
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
