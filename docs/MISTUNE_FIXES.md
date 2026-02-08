# Mistune Rendering Fixes - Implementation Summary

## Date: February 8, 2026

## Problem Statement
After refactoring the HEMA rulebook app to use Mistune for markdown conversion, several rendering issues were discovered:
1. HTML comments (`<!-- -->`) were appearing in the rendered output
2. Rule IDs were inconsistently formatted - some merged with text, others not on separate lines
3. Bullet lists lacked proper CSS styling classes
4. Some newlines were disappearing during conversion

## Root Cause Analysis
- Mistune treats markdown hard line breaks (`  \n` - two trailing spaces) as `<br>` tags within a single `<p>` element
- The pattern `**RULE-ID**  \n` followed by rule text was being rendered as a single paragraph
- HTML comments were not being filtered by default
- Unordered lists (`<ul>`) needed custom CSS class for consistent styling

## Solution Implemented

### 1. Preprocessing Function (`app/utils.py`)
Added `preprocess_rulebook_markdown()` function that:
- **Removes HTML comments**: Uses regex `r'<!--.*?-->'` with DOTALL flag to strip all comments
- **Converts hard breaks to paragraph breaks**: Transforms `**RULE-ID**  \n` to `**RULE-ID**\n\n` (double newline)
  - This ensures rule IDs render as separate `<p>` elements from their text
  - Regex pattern: `r'(\*\*[A-Z]+-[\d\.]+\*\*)  \n'` → `r'\1\n\n'`

### 2. Enhanced Custom Renderer (`app/utils.py`)
Extended `RuleIDRenderer` class with two new method overrides:

#### `list()` Override
```python
def list(self, text, ordered, level, start=None):
    if ordered:
        tag = 'ol'
        extra = f' start="{start}"' if start is not None else ''
    else:
        tag = 'ul'
        extra = ' class="bullet-list"'
    return f'<{tag}{extra}>\n{text}</{tag}>\n'
```
- Adds `class="bullet-list"` to all `<ul>` elements
- Preserves `<ol>` start attribute when present

#### `block_html()` Override
```python
def block_html(self, text):
    if text.strip().startswith('<!--'):
        return ''
    return text
```
- Filters out HTML comments at the block level
- Preserves other HTML blocks (e.g., `<span id="...">` anchors)

### 3. Integration Updates

#### `app/blueprints/rulebook.py`
- Added import: `from app.utils import preprocess_rulebook_markdown`
- Modified `_render_rulebook_html()`:
  ```python
  content = _get_rulebook_markdown_content()
  content = preprocess_rulebook_markdown(content)  # NEW LINE
  return md(content)
  ```

#### `build.py`
- Added import: `from app.utils import preprocess_rulebook_markdown`
- Modified build process:
  ```python
  content = preprocess_rulebook_markdown(content)  # NEW LINE
  html_content = md(content)
  ```

### 4. CSS Enhancement (`templates/rulebook.html`)
Added dedicated styling for bullet lists:
```css
ul.bullet-list {
    margin-left: 2rem;
    margin-bottom: 0.8rem;
}
```

## Files Modified

| File | Changes | Lines Changed |
|------|---------|---------------|
| `app/utils.py` | Added preprocessing function, list() and block_html() overrides | ~30 new lines |
| `app/blueprints/rulebook.py` | Added preprocessing import and call | 2 lines |
| `build.py` | Added preprocessing import and call | 2 lines |
| `templates/rulebook.html` | Added bullet-list CSS class | 5 lines |

## Testing Strategy

Created `test_preprocessing_standalone.py` to validate:
1. ✓ HTML comments are completely removed
2. ✓ Rule ID hard breaks convert to double newlines
3. ✓ Rule IDs render with `class="rule-id"` and depth classes
4. ✓ Bullet lists render with `class="bullet-list"`
5. ✓ Nested rules maintain proper depth-based indentation

## Expected Outcomes

### Before Fix
```html
<p><strong>GEN-1.1.1</strong><br>
Rule text here.</p>
<!-- This comment appears -->
<ul>
  <li>Bullet point</li>
</ul>
```

### After Fix
```html
<p class="rule-id rule-depth-3"><strong>GEN-1.1.1</strong></p>
<p>Rule text here.</p>

<ul class="bullet-list">
  <li>Bullet point</li>
</ul>
```

## Deployment Considerations

1. **No markdown file changes required** - All fixes are in the rendering layer
2. **Pre-rendering preserved** - `build.py` will generate correct HTML at deploy time
3. **Runtime fallback works** - If pre-rendered HTML unavailable, runtime rendering uses same logic
4. **Backward compatible** - Existing CSS classes and structure maintained
5. **No new dependencies** - Uses only regex (stdlib) and existing Mistune

## Next Steps

1. Deploy changes to Render.com
2. Verify pre-rendered `dist/rulebook.html` contains correct HTML structure
3. Validate bullet list indentation and rule ID separation in browser
4. Monitor for any edge cases in the 10+ markdown files

## Code Quality

- ✓ Syntax validated with `python -m py_compile`
- ✓ All imports properly structured
- ✓ Docstrings added for new functions
- ✓ Regex patterns tested with sample markdown
- ✓ CSS classes follow existing naming conventions
