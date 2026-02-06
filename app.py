"""
HEMA Rulebook Search Web App
Flask application for searching the HEMA rulebook
"""

import json
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from qa_tools.search_aliases import AliasAwareSearch

app = Flask(__name__)

# Load search engine
qa_dir = Path(__file__).parent / "qa-tools"
search_engine = AliasAwareSearch(
    str(qa_dir / "rules_index.json"),
    str(qa_dir / "aliases.json")
)

# Cache for format and weapon options
FORMATS = ["VOR", "COMBAT", "AFTERBLOW"]
WEAPONS = ["longsword", "rapier", "padded_weapons"]


@app.route("/")
def index():
    """Home page"""
    return render_template("index.html", formats=FORMATS, weapons=WEAPONS)


@app.route("/api/search", methods=["POST"])
def api_search():
    """API endpoint for search"""
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        max_results = min(int(data.get("max_results", 10)), 50)  # Cap at 50
        formatum_filter = data.get("formatum_filter")
        weapon_filter = data.get("weapon_filter")

        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400

        # Validate filters
        if formatum_filter and formatum_filter not in FORMATS:
            formatum_filter = None
        if weapon_filter and weapon_filter not in WEAPONS:
            weapon_filter = None

        # Perform search
        results = search_engine.search(
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


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Get statistics about the rulebook"""
    total_rules = len(search_engine.rules)
    vor_rules = sum(1 for r in search_engine.rules if r.get("formatum") == "VOR")
    combat_rules = sum(1 for r in search_engine.rules if r.get("formatum") == "COMBAT")
    ab_rules = sum(1 for r in search_engine.rules if r.get("formatum") == "AFTERBLOW")
    longsword_rules = sum(1 for r in search_engine.rules if r.get("weapon_type") == "longsword")

    return jsonify({
        "total_rules": total_rules,
        "vor_rules": vor_rules,
        "combat_rules": combat_rules,
        "afterblow_rules": ab_rules,
        "longsword_rules": longsword_rules
    })


@app.route("/api/rule/<rule_id>", methods=["GET"])
def api_rule(rule_id):
    """Get a specific rule by ID"""
    rule = search_engine.get_rule_by_id(rule_id)
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


if __name__ == "__main__":
    # Get port from environment or use 5000 for local development
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
