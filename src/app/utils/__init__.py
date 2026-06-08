"""
app.utils - Re-export public API.

Submodules:
- markdown_utils: Markdown preprocessing, rendering, and plain-text stripping
- extract_utils: Rule extraction and formatting helpers

Note: ``normalize_filter`` lives in ``app.validation`` (it is input validation,
not a generic utility). It is re-exported here for backward compatibility.
"""

from app.validation import normalize_filter

from .extract_utils import (
    build_document_order,
    filter_rules_for_extract,
    format_extract_text,
    read_rulebook_markdown_content,
)
from .markdown_utils import (
    RuleIDRenderer,
    create_mistune_markdown,
    preprocess_rulebook_markdown,
    strip_markdown,
)

__all__ = [
    "RuleIDRenderer",
    "build_document_order",
    "create_mistune_markdown",
    "filter_rules_for_extract",
    "format_extract_text",
    "normalize_filter",
    "preprocess_rulebook_markdown",
    "read_rulebook_markdown_content",
    "strip_markdown",
]
