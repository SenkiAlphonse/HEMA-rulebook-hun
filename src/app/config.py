"""Centralized configuration and path management for HEMA Rulebook app."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ruleset versioning (visible to users in footer; bump on each rule revision).
# ---------------------------------------------------------------------------
# RULESET_VERSION is a hand-curated label that bumps when the published rules
# change in a meaningful way.
#
# RULESET_LAST_UPDATED is computed at *build time* from the latest git commit
# touching `rules/` or `rules_en/` and stamped into `data/search/ruleset_meta.json`
# by `tools/build.py`. The runtime container does not have `.git`, so we read
# from that file at startup. Override priority:
#     1. HEMA_RULESET_LAST_UPDATED env var (manual override)
#     2. ruleset_meta.json (set by build)
#     3. "unknown" (build never ran or stamp file missing)
# ---------------------------------------------------------------------------
RULESET_VERSION: str = os.environ.get("HEMA_RULESET_VERSION", "2026.1")


def _resolve_ruleset_last_updated() -> str:
    env = os.environ.get("HEMA_RULESET_LAST_UPDATED")
    if env:
        return env
    # ruleset_meta.json sits beside the search indexes; its location depends on
    # PROJECT_ROOT, which is computed below. Re-derive it cheaply here.
    meta_path = _project_root_for_meta() / "data" / "search" / "ruleset_meta.json"
    try:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        value = str(meta.get("last_updated", "")).strip()
        if value:
            return value
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        logger.debug("ruleset_meta.json unavailable (%s); using fallback", e)
    return "unknown"


def _project_root_for_meta() -> Path:
    """Lightweight project-root resolver used before PROJECT_ROOT is set."""
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "rules").is_dir() and (candidate / "templates").is_dir():
            return candidate
    return here.parents[2]


RULESET_LAST_UPDATED: str = _resolve_ruleset_last_updated()


def _find_project_root(start: Path) -> Path:
    """Find repo root by walking up until expected folders exist."""
    start = start.resolve()
    for candidate in [start, *list(start.parents)]:
        # Heuristics: these directories/files are expected at repo root.
        if (
            (candidate / "rules").is_dir()
            and (candidate / "templates").is_dir()
            and (candidate / "requirements.txt").exists()
        ):
            return candidate
    # Fallback: src/app/config.py -> repo root is 2 parents up (app -> src -> root)
    try:
        return start.parents[2]
    except IndexError:
        return start.parent


# Project root directory (works with `src/` layout)
PROJECT_ROOT = _find_project_root(Path(__file__))


# Common path getters
def get_project_root() -> Path:
    """Get the project root directory"""
    return PROJECT_ROOT


def get_qa_tools_dir() -> Path:
    """Get qa_tools package directory path (developer convenience)."""
    return PROJECT_ROOT / "src" / "qa_tools"


def get_data_dir() -> Path:
    """Get top-level data directory"""
    return PROJECT_ROOT / "data"


def get_search_data_dir() -> Path:
    """Get directory containing search index + aliases"""
    return get_data_dir() / "search"


def get_templates_dir() -> Path:
    """Get templates directory path"""
    return PROJECT_ROOT / "templates"


def get_dist_dir() -> Path:
    """Get dist directory path (for pre-rendered files)"""
    return PROJECT_ROOT / "dist"


def get_rulebook_dir() -> Path:
    """Get rulebook directory (root directory with markdown files)"""
    return PROJECT_ROOT / "rules"


def get_rulebook_en_dir() -> Path:
    """Get English rulebook directory with markdown files"""
    return PROJECT_ROOT / "rules_en"


def get_rules_index_path(lang: str = "hun") -> Path:
    """Get path to language-specific rules index.

    Args:
        lang: Language code, 'hun' or 'eng'.
    """
    search_dir = get_search_data_dir()
    if lang == "eng":
        return search_dir / "rules_index_eng.json"
    return search_dir / "rules_index_hun.json"


def get_aliases_path(lang: str = "hun") -> Path:
    """Get path to aliases file for a language, with fallback to shared aliases.json."""
    search_dir = get_search_data_dir()
    lang_alias_path = search_dir / f"aliases_{lang}.json"
    if lang_alias_path.exists():
        return lang_alias_path
    return search_dir / "aliases.json"


def get_rulebook_markdown_files() -> list[Path]:
    """Get all numbered markdown rulebook files from root directory"""
    rulebook_dir = get_rulebook_dir()
    md_files = sorted(rulebook_dir.glob("[0-9][0-9]*.md"))

    # Filter out README and other non-rulebook files
    md_files = [f for f in md_files if f.name != "README.md"]

    return md_files


def get_rulebook_markdown_files_en() -> list[Path]:
    """Get all numbered English markdown rulebook files"""
    rulebook_dir = get_rulebook_en_dir()
    md_files = sorted(rulebook_dir.glob("[0-9][0-9]*.md"))
    md_files = [f for f in md_files if f.name != "README.md"]
    return md_files


def get_prerendered_rulebook_path(lang: str = "hun") -> Path:
    """Get path to pre-rendered rulebook HTML.

    Args:
        lang: Language code, 'hun' (Hungarian) or 'eng' (English). Defaults to 'hun'.
    """
    if lang == "eng":
        return get_dist_dir() / "rulebook_eng.html"
    return get_dist_dir() / "rulebook_hun.html"
