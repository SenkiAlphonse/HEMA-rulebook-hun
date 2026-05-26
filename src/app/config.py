"""Centralized configuration and path management for HEMA Rulebook app."""

from __future__ import annotations

from pathlib import Path
from typing import List


def _find_project_root(start: Path) -> Path:
    """Find repo root by walking up until expected folders exist."""
    start = start.resolve()
    for candidate in [start] + list(start.parents):
        # Heuristics: these directories/files are expected at repo root.
        if (candidate / "rules").is_dir() and (candidate / "templates").is_dir() and (candidate / "requirements.txt").exists():
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

def get_rules_index_path(lang: str = "hun", legacy_fallback: bool = False) -> Path:
    """Get path to language-specific rules index.

    Args:
        lang: Language code, 'hun' or 'eng'.
        legacy_fallback: If True and lang='hun', fall back to legacy rules_index.json.
    """
    search_dir = get_search_data_dir()
    if lang == "eng":
        return search_dir / "rules_index_eng.json"

    hun_path = search_dir / "rules_index_hun.json"
    if legacy_fallback and not hun_path.exists():
        return get_legacy_rules_index_path()
    return hun_path

def get_legacy_rules_index_path() -> Path:
    """Get legacy monolingual index path for backward compatibility."""
    return get_search_data_dir() / "rules_index.json"

def get_aliases_path(lang: str = "hun") -> Path:
    """Get path to aliases file for a language, with fallback to shared aliases.json."""
    search_dir = get_search_data_dir()
    lang_alias_path = search_dir / f"aliases_{lang}.json"
    if lang_alias_path.exists():
        return lang_alias_path
    return search_dir / "aliases.json"

def get_rulebook_markdown_files() -> List[Path]:
    """Get all numbered markdown rulebook files from root directory"""
    rulebook_dir = get_rulebook_dir()
    md_files = sorted(rulebook_dir.glob("[0-9][0-9]*.md"))
    
    # Filter out README and other non-rulebook files
    md_files = [f for f in md_files if f.name != "README.md"]
    
    return md_files

def get_rulebook_markdown_files_en() -> List[Path]:
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

