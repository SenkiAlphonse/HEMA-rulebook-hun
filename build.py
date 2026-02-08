#!/usr/bin/env python
"""
Build script for pre-rendering rulebook HTML and regenerating search index
Converts all markdown rulebook files to HTML and saves to dist/rulebook.html
Rebuilds the rules_index.json for search functionality
Run this at deployment time to generate static rulebook
"""

from pathlib import Path
import sys
import subprocess


def build_search_index():
    """Regenerate the search index from markdown files"""
    try:
        print("Building search index...")
        result = subprocess.run(
            [sys.executable, "qa-tools/parser.py"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Search index rebuilt successfully")
            return True
        else:
            print(f"✗ Search index build failed: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"✗ Search index build error: {e}", file=sys.stderr)
        return False


def build_rulebook():
    """Generate pre-rendered rulebook HTML"""
    try:
        # Import Mistune (will be available after pip install)
        from app.utils import create_mistune_markdown, preprocess_rulebook_markdown
        
        # Get project root
        project_root = Path(__file__).parent
        
        # Create dist directory
        dist_dir = project_root / "dist"
        dist_dir.mkdir(exist_ok=True)
        
        # Read all markdown files
        rulebook_dir = project_root
        
        # Automatically detect all numbered markdown files in the root directory
        # Pattern: NN-*.md or NN.x-*.md (where NN is 01-99)
        md_files = []
        for md_file in sorted(rulebook_dir.glob("[0-9][0-9]*.md")):
            # Exclude non-rulebook files
            if md_file.name not in ["README.md"]:
                md_files.append(md_file.name)
        
        # Append appendices from fuggelek directory
        appendix_dir = rulebook_dir / "fuggelek"
        if appendix_dir.exists():
            appendix_files = sorted(appendix_dir.glob("*.md"))
            # Skip README files in appendix too
            md_files.extend([f"fuggelek/{f.name}" for f in appendix_files if f.name != "README.md"])
        
        # Concatenate all markdown
        content = ""
        for md_file in md_files:
            file_path = rulebook_dir / md_file
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content += f.read() + "\n\n---\n\n"
                print(f"  ✓ Loaded {md_file}")
        
        # Convert to HTML
        md = create_mistune_markdown()
        # Preprocess markdown before conversion
        content = preprocess_rulebook_markdown(content)
        html_content = md(content)
        
        # Write to dist
        output_path = dist_dir / "rulebook.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Rulebook pre-rendered to {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ Build failed: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    # Build search index first
    index_success = build_search_index()
    
    # Build rulebook HTML
    rulebook_success = build_rulebook()
    
    # Exit with success only if both succeed
    sys.exit(0 if (index_success and rulebook_success) else 1)
