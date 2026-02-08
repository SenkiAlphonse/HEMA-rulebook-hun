"""
Rulebook blueprint - handles full rulebook display and API endpoints
"""

from pathlib import Path
from flask import Blueprint, render_template, jsonify, current_app, send_file
from app.utils import create_mistune_markdown, preprocess_rulebook_markdown
from app.config import get_rulebook_markdown_files, get_prerendered_rulebook_path

rulebook_bp = Blueprint('rulebook', __name__)


def _get_rulebook_markdown_content():
    """Read and concatenate all rulebook markdown files"""
    md_files = get_rulebook_markdown_files()
    
    content = ""
    for md_file in md_files:
        if md_file.exists():
            with open(md_file, 'r', encoding='utf-8') as f:
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
