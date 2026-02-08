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
    md_files = [
        "01-altalanos.md",
        "02-szojegyzek.md",
        "03-felszereles.md",
        "04-biraskodas.md",
        "05-hosszukard.md",
        "05.a-hosszukard-VOR.md",
        "05.b-hosszukard-COMBAT.md",
        "05.c-hosszukard-AFTERBLOW.md",
        "08-etikett_fegyelem.md",
        "09-szervezes.md",
    ]
    
    # Append appendices
    appendix_dir = rulebook_dir / "fuggelek"
    if appendix_dir.exists():
        appendix_files = sorted(appendix_dir.glob("*.md"))
        md_files.extend([f.name for f in appendix_files])
    
    content = ""
    for md_file in md_files:
        file_path = rulebook_dir / md_file
        if not file_path.exists():
            file_path = rulebook_dir / "fuggelek" / md_file
        
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
