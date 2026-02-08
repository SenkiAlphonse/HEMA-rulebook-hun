#!/usr/bin/env python
"""
Build script for pre-rendering rulebook HTML and regenerating search index
Converts all markdown rulebook files to HTML and saves to dist/rulebook.html
Rebuilds the rules_index.json for search functionality
Run this at deployment time to generate static rulebook
"""

import sys
import subprocess
import logging
from app.config import (
    get_project_root, get_qa_tools_dir, get_dist_dir, 
    get_rulebook_markdown_files, get_prerendered_rulebook_path
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def build_search_index():
    """Regenerate the search index from markdown files"""
    try:
        logger.info("Building search index...")
        result = subprocess.run(
            [sys.executable, "qa-tools/parser.py"],
            cwd=get_project_root(),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✓ Search index rebuilt successfully")
            return True
        else:
            logger.error(f"✗ Search index build failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("✗ Search index build timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Search index build error: {type(e).__name__}: {e}")
        return False


def build_rulebook():
    """Generate pre-rendered rulebook HTML"""
    try:
        # Import Mistune (will be available after pip install)
        from app.utils import create_mistune_markdown, preprocess_rulebook_markdown
        
        # Create dist directory
        dist_dir = get_dist_dir()
        dist_dir.mkdir(exist_ok=True)
        
        # Get markdown files
        md_files = get_rulebook_markdown_files()
        
        if not md_files:
            logger.warning("⚠ No markdown files found for rulebook")
            return False
        
        # Concatenate all markdown
        content = ""
        for md_file in md_files:
            if md_file.exists():
                with open(md_file, 'r', encoding='utf-8') as f:
                    content += f.read() + "\n\n---\n\n"
                logger.info(f"  ✓ Loaded {md_file.name}")
        
        # Convert to HTML
        md = create_mistune_markdown()
        # Preprocess markdown before conversion
        content = preprocess_rulebook_markdown(content)
        html_content = md(content)
        
        # Write to dist
        output_path = get_prerendered_rulebook_path()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✓ Rulebook pre-rendered to {output_path}")
        return True
        
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

