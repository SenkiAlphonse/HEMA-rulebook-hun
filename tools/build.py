#!/usr/bin/env python
"""
Build script for pre-rendering rulebook HTML and regenerating search index
Converts all markdown rulebook files to HTML and saves to dist/rulebook.html
Rebuilds the rules_index.json for search functionality
Run this at deployment time to generate static rulebook
"""

import sys
import logging
import shutil
from pathlib import Path

# Allow running `python tools/build.py` without installing the package
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if SRC_DIR.is_dir():
    sys.path.insert(0, str(SRC_DIR))

from app.config import (
    get_project_root, get_dist_dir,
    get_prerendered_rulebook_path,
    get_rules_index_path,
    get_legacy_rules_index_path,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def build_search_index():
    """Regenerate language-specific search indexes from markdown files"""
    try:
        logger.info("Building search index...")
        from qa_tools.tools.parser import RulebookParser

        project_root = get_project_root()
        index_specs = (
            ("hun", "rules"),
            ("eng", "rules_en"),
        )

        for lang, rules_subdir in index_specs:
            output_path = get_rules_index_path(lang=lang)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Building {lang} index from {rules_subdir}/ ...")
            RulebookParser(project_root, rules_subdir=rules_subdir, language=lang).save_index(output_path)

        # Keep legacy monolingual file for backward compatibility (maps to Hungarian index)
        legacy_output_path = get_legacy_rules_index_path()
        shutil.copyfile(get_rules_index_path(lang="hun"), legacy_output_path)
        logger.info(f"✓ Legacy index updated at {legacy_output_path}")

        logger.info("✓ Search index rebuilt successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Search index build error: {type(e).__name__}: {e}")
        return False


def build_rulebook():
    """Generate pre-rendered rulebook HTML for all languages (hun + eng)"""
    try:
        # Import shared utilities
        from app.utils import create_mistune_markdown, preprocess_rulebook_markdown, read_rulebook_markdown_content

        # Create dist directory
        dist_dir = get_dist_dir()
        dist_dir.mkdir(exist_ok=True)

        md = create_mistune_markdown()
        all_ok = True

        for lang in ("hun", "eng"):
            content = read_rulebook_markdown_content(lang=lang)

            if not content:
                logger.warning(f"⚠ No markdown content found for lang='{lang}'")
                all_ok = False
                continue

            # Convert to HTML
            processed = preprocess_rulebook_markdown(content)
            html_content = md(processed)

            # Write to dist
            output_path = get_prerendered_rulebook_path(lang=lang)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"✓ Rulebook ({lang}) pre-rendered to {output_path}")

        return all_ok

    except Exception as e:
        logger.error(f"✗ Build failed: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    # Build search index first
    index_success = build_search_index()

    # Build rulebook HTML
    rulebook_success = build_rulebook()

    # Exit with success only if both succeed
    sys.exit(0 if (index_success and rulebook_success) else 1)

