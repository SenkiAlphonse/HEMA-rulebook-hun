"""
Rulebook blueprint - handles full rulebook display and API endpoints
"""

from pathlib import Path
from flask import Blueprint, render_template, jsonify, current_app, send_file
from app.utils import create_mistune_markdown, preprocess_rulebook_markdown

rulebook_bp = Blueprint('rulebook', __name__)


def _get_rulebook_markdown_content():
    """Read and concatenate all rulebook markdown files"""
    rulebook_dir = Path(__file__).parent.parent.parent
    
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
    
    content = ""
    for md_file in md_files:
        file_path = rulebook_dir / md_file
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content += f.read() + "\n\n---\n\n"
    
    return content


def _render_rulebook_html():
    """Render rulebook markdown to HTML"""
    md = create_mistune_markdown()
    content = _get_rulebook_markdown_content()
    # Preprocess markdown before conversion
    content = preprocess_rulebook_markdown(content)
    return md(content)


@rulebook_bp.route('/rulebook')
def rulebook():
    """Display the entire rulebook"""
    # Try to load pre-rendered rulebook first
    dist_path = Path(__file__).parent.parent.parent / "dist" / "rulebook.html"
    
    if dist_path.exists():
        # Pre-rendered HTML available
        with open(dist_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    else:
        # Fall back to runtime rendering
        html_content = _render_rulebook_html()
    
    return render_template("rulebook.html", markdown_content=html_content)


@rulebook_bp.route('/api/rulebook')
def api_rulebook():
    """API endpoint to get all rules as JSON"""
    rules = current_app.search_engine.rules
    return jsonify({
        "success": True,
        "rules": rules,
        "total": len(rules)
    })
