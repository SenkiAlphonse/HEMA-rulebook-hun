"""
Search blueprint - handles search, stats, and rule lookup endpoints
"""

import logging
from flask import Blueprint, request, jsonify, current_app, Response
from app.utils import (
    normalize_filter, build_document_order, filter_rules_for_extract, format_extract_text
)

# Configure logging
logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__, url_prefix='/api')


@search_bp.route('/search', methods=['POST'])
def api_search():
    """Search for rules by keyword
    
    For level 4-5 rules, returns grouped results with parent context and child rules.
    Each result includes a depth indicator and group_root for hierarchical organization.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
            
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

        # Convert results to JSON with depth and grouping info
        results_data = []
        current_group = None
        
        for r in results:
            depth = current_app.search_engine._get_rule_depth(r.rule_id)
            
            # Determine group root for hierarchy visualization
            if depth >= 4:
                # For level 4-5 rules, find the main parent (depth 2)
                lineage = current_app.search_engine._get_rule_lineage(r.rule_id)
                # Take the second element if it exists (first is the prefix like "GEN")
                current_group = lineage[1] if len(lineage) > 1 else r.rule_id
            else:
                # For levels 1-3, the rule itself is a group anchor
                current_group = r.rule_id
            
            results_data.append({
                "rule_id": r.rule_id,
                "text": r.text,
                "section": r.section,
                "subsection": r.subsection,
                "document": r.document,
                "weapon_type": r.weapon_type,
                "formatum": r.formatum or "general",
                "score": r.score,
                "depth": depth,
                "group_root": current_group
            })

        return jsonify({
            "success": True,
            "query": query,
            "count": len(results_data),
            "results": results_data,
            "note": "Results grouped by rule hierarchy. Level 4-5 rules include parent rules (up to level 3) and direct child rules."
        })

    except ValueError as e:
        logger.warning(f"Invalid search request parameters: {e}")
        return jsonify({"error": "Invalid request parameters"}), 400
    except Exception as e:
        logger.error(f"Search error: {type(e).__name__}: {e}")
        return jsonify({"error": "Search failed"}), 500


@search_bp.route('/stats', methods=['GET'])
def api_stats():
    """Get rulebook statistics"""
    try:
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
    except Exception as e:
        logger.error(f"Stats error: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to get statistics"}), 500


@search_bp.route('/extract', methods=['POST'])
def api_extract():
    """Generate rulebook extract filtered by weapon and format"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400
            
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
    except ValueError as e:
        logger.warning(f"Invalid extract request parameters: {e}")
        return jsonify({"error": "Invalid request parameters"}), 400
    except Exception as e:
        logger.error(f"Extract error: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to generate extract"}), 500


@search_bp.route('/rule/<rule_id>', methods=['GET'])
def api_rule(rule_id):
    """Get a specific rule by ID"""
    try:
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
    except Exception as e:
        logger.error(f"Get rule error: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to retrieve rule"}), 500
