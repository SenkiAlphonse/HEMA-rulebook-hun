"""
DEPRECATED: app/utils.py has been refactored into app/utils/ submodules.

All utilities have been moved to:
- app/utils/markdown_utils.py: Markdown preprocessing and rendering
- app/utils/filter_utils.py: Filter validation and normalization
- app/utils/extract_utils.py: Rule extraction and formatting

For backward compatibility, all functions are re-exported below.
New code should import from app.utils directly (uses __init__.py).
"""

# Re-export all functions for backward compatibility
from app.utils import (
    preprocess_rulebook_markdown,
    RuleIDRenderer,
    create_mistune_markdown,
    normalize_filter,
    build_document_order,
    read_rulebook_markdown_content,
    filter_rules_for_extract,
    format_extract_text
)
