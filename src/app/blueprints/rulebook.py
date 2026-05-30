"""
Rulebook blueprint - handles full rulebook display and API endpoints
"""

from flask import Blueprint, abort, current_app, jsonify, render_template, request

from app.config import get_prerendered_rulebook_path

rulebook_bp = Blueprint("rulebook", __name__)

VALID_LANGS = {"hun", "eng"}


@rulebook_bp.route("/rulebook")
def rulebook():
    """Display the entire rulebook. Accepts ?lang=hun (default) or ?lang=eng."""
    lang = request.args.get("lang", "hun").lower()
    if lang not in VALID_LANGS:
        abort(400, description=f"Invalid lang '{lang}'. Use 'hun' or 'eng'.")

    dist_path = get_prerendered_rulebook_path(lang=lang)
    with open(dist_path, encoding="utf-8") as f:
        html_content = f.read()

    return render_template("rulebook.html", markdown_content=html_content)


@rulebook_bp.route("/api/rulebook")
def api_rulebook():
    """API endpoint to get all rules as JSON"""
    lang = request.args.get("lang", "hun").lower()
    if lang not in VALID_LANGS:
        abort(400, description=f"Invalid lang '{lang}'. Use 'hun' or 'eng'.")

    search_engine = getattr(current_app, "search_engines", {}).get(lang, current_app.search_engine)
    rules = search_engine.rules
    return jsonify({"success": True, "lang": lang, "rules": rules, "total": len(rules)})
