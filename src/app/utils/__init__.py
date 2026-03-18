"""
app.utils - Re-export public API for backward compatibility.

All utilities have been moved to submodules:
- markdown_utils: Markdown preprocessing and rendering
- filter_utils: Filter validation and normalization
- extract_utils: Rule extraction and formatting
"""

from .markdown_utils import preprocess_rulebook_markdown, RuleIDRenderer, create_mistune_markdown
from .filter_utils import normalize_filter
from .extract_utils import (
    build_document_order,
    read_rulebook_markdown_content,
    filter_rules_for_extract,
    format_extract_text
)

__all__ = [
    'preprocess_rulebook_markdown',
    'RuleIDRenderer',
    'create_mistune_markdown',
    'normalize_filter',
    'build_document_order',
    'read_rulebook_markdown_content',
    'filter_rules_for_extract',
    'format_extract_text'
]
