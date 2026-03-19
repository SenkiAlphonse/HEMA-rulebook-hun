"""
Rulebook blueprint - handles full rulebook display and API endpoints
"""

from flask import Blueprint, render_template, jsonify, current_app
from app.config import get_prerendered_rulebook_path

rulebook_bp = Blueprint('rulebook', __name__)


@rulebook_bp.route('/rulebook')
def rulebook():
    """Display the entire rulebook"""
    dist_path = get_prerendered_rulebook_path()
    with open(dist_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

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
