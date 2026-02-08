"""
Search blueprint - handles search, stats, and rule lookup endpoints
"""

from flask import Blueprint, request, jsonify, current_app, Response
from app.utils import (
    normalize_filter, build_document_order, filter_rules_for_extract, format_extract_text
)

search_bp = Blueprint('search', __name__, url_prefix='/api')


@search_bp.route('/search', methods=['POST'])
def api_search():
    """Search for rules by keyword"""
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        max_results = min(int(data.get("max_results", 100)), 100)
        formatum_filter = data.get("formatum_filter")
        weapon_filter = data.get("weapon_filter")

        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400

        # Validate filters
        if formatum_filter and formatum_filter not in current_app.config['FORMATS']:
            formatum_filter = None
        if weapon_filter and weapon_filter not in current_app.config['WEAPONS']:
            weapon_filter = None

        # Perform search
        results = current_app.search_engine.search(
            query,
            max_results=max_results,
            formatum_filter=formatum_filter,
            weapon_filter=weapon_filter
        )

        # Convert results to JSON
        results_data = [
            {
                "rule_id": r.rule_id,
                "text": r.text,
                "section": r.section,
                "subsection": r.subsection,
                "document": r.document,
                "weapon_type": r.weapon_type,
                "formatum": r.formatum or "general",
                "score": r.score
            }
            for r in results
        ]

        return jsonify({
            "success": True,
            "query": query,
            "count": len(results_data),
            "results": results_data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@search_bp.route('/stats', methods=['GET'])
def api_stats():
    """Get rulebook statistics"""
    total_rules = len(current_app.search_engine.rules)
    vor_rules = sum(1 for r in current_app.search_engine.rules if r.get("formatum") == "VOR")
    combat_rules = sum(1 for r in current_app.search_engine.rules if r.get("formatum") == "COMBAT")
    ab_rules = sum(1 for r in current_app.search_engine.rules if r.get("formatum") == "AFTERBLOW")
    longsword_rules = sum(1 for r in current_app.search_engine.rules if r.get("weapon_type") == "longsword")

    return jsonify({
        "total_rules": total_rules,
        "vor_rules": vor_rules,
        "combat_rules": combat_rules,
        "afterblow_rules": ab_rules,
        "longsword_rules": longsword_rules
    })


@search_bp.route('/extract', methods=['POST'])
def api_extract():
    """Generate rulebook extract filtered by weapon and format"""
    try:
        data = request.get_json()
        weapon_filter = normalize_filter(data.get("weapon_filter"), current_app.config['WEAPONS'])
        formatum_filter = normalize_filter(data.get("formatum_filter"), current_app.config['FORMATS'])

        filtered_rules = filter_rules_for_extract(
            current_app.search_engine.rules,
            weapon_filter,
            formatum_filter
        )

        extract_text = format_extract_text(
            filtered_rules,
            weapon_filter,
            formatum_filter
        )

        weapon_label = weapon_filter or "all-weapons"
        format_label = formatum_filter or "all-formats"
        filename = f"rulebook-extract_{weapon_label}_{format_label}.md"

        return Response(
            extract_text,
            mimetype="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@search_bp.route('/rule/<rule_id>', methods=['GET'])
def api_rule(rule_id):
    """Get a specific rule by ID"""
    rule = current_app.search_engine.get_rule_by_id(rule_id)
    if rule:
        return jsonify({
            "success": True,
            "rule": {
                "rule_id": rule["rule_id"],
                "text": rule["text"],
                "section": rule.get("section", ""),
                "subsection": rule.get("subsection", ""),
                "document": rule.get("document", ""),
                "weapon_type": rule.get("weapon_type", ""),
                "formatum": rule.get("formatum", ""),
                "anchor_id": rule.get("anchor_id", "")
            }
        })
    return jsonify({"error": "Rule not found"}), 404
