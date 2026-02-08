#!/usr/bin/env python
"""
Build script for pre-rendering rulebook HTML
Converts all markdown rulebook files to HTML and saves to dist/rulebook.html
Run this at deployment time to generate static rulebook
"""

from pathlib import Path
import sys


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
        md_files = [
            "01-altalanos.md",
            "02-hosszukard.md",
            "02.a-hosszukard-VOR.md",
            "02.b-hosszukard-COMBAT.md",
            "02.c-hosszukard-AFTERBLOW.md",
            "03-etikett_fegyelem.md",
            "04-szervezes.md",
        ]
        
        # Append appendices
        appendix_dir = rulebook_dir / "fuggelek"
        if appendix_dir.exists():
            appendix_files = sorted(appendix_dir.glob("*.md"))
            md_files.extend([f.name for f in appendix_files])
        
        # Concatenate all markdown
        content = ""
        for md_file in md_files:
            file_path = rulebook_dir / md_file
            if not file_path.exists():
                file_path = rulebook_dir / "fuggelek" / md_file
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content += f.read() + "\n\n---\n\n"
        
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
    success = build_rulebook()
    sys.exit(0 if success else 1)
