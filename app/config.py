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
    """Get qa_tools directory path"""
    return PROJECT_ROOT / "qa_tools"

def get_templates_dir() -> Path:
    """Get templates directory path"""
    return PROJECT_ROOT / "templates"

def get_dist_dir() -> Path:
    """Get dist directory path (for pre-rendered files)"""
    return PROJECT_ROOT / "dist"

def get_rulebook_dir() -> Path:
    """Get rulebook directory (root directory with markdown files)"""
    return PROJECT_ROOT / "rules"

def get_rules_index_path() -> Path:
    """Get path to rules_index.json"""
    return get_qa_tools_dir() / "data" / "rules_index.json"

def get_aliases_path() -> Path:
    """Get path to aliases.json"""
    return get_qa_tools_dir() / "data" / "aliases.json"

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


# AI/Gemini Configuration Constants
GEMINI_MODEL_CANDIDATES = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
SUMMARY_CHUNK_SIZE = 6000  # Character limit for content chunks
SUMMARY_MAX_RETRIES = 2  # Maximum retry attempts for API calls
SUMMARY_SEARCH_MAX_RULES = 20  # Max number of search matches sent for summary
SUMMARY_MAX_INPUT_CHARS = 15000  # Max total input chars sent to Gemini for one summary

