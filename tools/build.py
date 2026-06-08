#!/usr/bin/env python
"""
Build script for pre-rendering rulebook HTML and regenerating search index
Converts all markdown rulebook files to HTML and saves to dist/rulebook_hun.html and dist/rulebook_eng.html
Rebuilds the rules_index_hun.json and rules_index_eng.json for search functionality
Run this at deployment time to generate static rulebook
"""

import json
import logging
import subprocess
import sys
from datetime import date
from pathlib import Path

# Allow running `python tools/build.py` without installing the package
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if SRC_DIR.is_dir():
    sys.path.insert(0, str(SRC_DIR))

from app.config import (
    get_dist_dir,
    get_prerendered_rulebook_path,
    get_project_root,
    get_rules_index_path,
    get_search_data_dir,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def _last_rules_change_date(project_root: Path) -> str:
    """Return the date (YYYY-MM-DD) of the most recent commit touching the
    rule chapters. Falls back to today if git is unavailable (e.g. running
    from a tarball) so the meta file is always written.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", "rules", "rules_en"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        out = result.stdout.strip()
        if result.returncode == 0 and out:
            return out
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as e:
        logger.warning(f"git log failed for ruleset date ({e}); using today")
    return date.today().isoformat()


def _write_ruleset_meta(project_root: Path) -> None:
    """Stamp last-updated date so the running app can show it in the footer."""
    meta = {"last_updated": _last_rules_change_date(project_root)}
    meta_path = get_search_data_dir() / "ruleset_meta.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    logger.info(f"Ruleset metadata: last_updated={meta['last_updated']}")


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
            RulebookParser(project_root, rules_subdir=rules_subdir, language=lang).save_index(
                output_path
            )

        logger.info("✓ Search index rebuilt successfully")
        _write_ruleset_meta(project_root)
        return True
    except Exception as e:
        logger.error(f"✗ Search index build error: {type(e).__name__}: {e}")
        return False


def build_rulebook():
    """Generate pre-rendered rulebook HTML for all languages (hun + eng)"""
    try:
        # Import shared utilities
        from app.utils import (
            create_mistune_markdown,
            preprocess_rulebook_markdown,
            read_rulebook_markdown_content,
        )

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
            with open(output_path, "w", encoding="utf-8") as f:
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
