"""
Centralized configuration and path management for HEMA Rulebook app
"""

from pathlib import Path
from typing import List

# Project root directory - one level above app/ directory
PROJECT_ROOT = Path(__file__).parent.parent

# Common path getters
def get_project_root() -> Path:
    """Get the project root directory"""
    return PROJECT_ROOT

def get_qa_tools_dir() -> Path:
    """Get qa-tools directory path"""
    return PROJECT_ROOT / "qa-tools"

def get_templates_dir() -> Path:
    """Get templates directory path"""
    return PROJECT_ROOT / "templates"

def get_dist_dir() -> Path:
    """Get dist directory path (for pre-rendered files)"""
    return PROJECT_ROOT / "dist"

def get_rulebook_dir() -> Path:
    """Get rulebook directory (root directory with markdown files)"""
    return PROJECT_ROOT

def get_rules_index_path() -> Path:
    """Get path to rules_index.json"""
    return get_qa_tools_dir() / "rules_index.json"

def get_aliases_path() -> Path:
    """Get path to aliases.json"""
    return get_qa_tools_dir() / "aliases.json"

def get_rulebook_markdown_files() -> List[Path]:
    """Get all numbered markdown rulebook files from root directory"""
    rulebook_dir = get_rulebook_dir()
    md_files = sorted(rulebook_dir.glob("[0-9][0-9]*.md"))
    
    # Filter out README and other non-rulebook files
    md_files = [f for f in md_files if f.name != "README.md"]
    
    return md_files

def get_prerendered_rulebook_path() -> Path:
    """Get path to pre-rendered rulebook HTML"""
    return get_dist_dir() / "rulebook.html"
