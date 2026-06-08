"""
Search blueprint - handles search, stats, and rule lookup endpoints
"""

import logging
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request

from app.query_log import log_search
from app.utils import filter_rules_for_extract, format_extract_text, normalize_filter
from app.validation import sanitize_query, validate_filter, validate_max_results, validate_query

# Configure logging
logger = logging.getLogger(__name__)

search_bp = Blueprint("search", __name__, url_prefix="/api")

VALID_RULESET_LANGS = {"hun", "eng"}


def _resolve_rules_lang(data: dict | None = None) -> str:
    """Resolve rules language from request body or query params."""
    payload = data or {}
    raw_lang = payload.get("rules_lang") or request.args.get("rules_lang") or "hun"
    lang = str(raw_lang).strip().lower()
    if lang not in VALID_RULESET_LANGS:
        raise ValueError(f"Invalid rules_lang '{raw_lang}'. Use 'hun' or 'eng'.")
    return lang


def _get_engine_for_lang(lang: str):
    """Get search engine for language with default fallback."""
    return getattr(current_app, "search_engines", {}).get(lang, current_app.search_engine)


@search_bp.route("/search", methods=["POST"])
def api_search() -> Any:
    """Search for rules by keyword

    For level 4-5 rules, returns grouped results with parent context and child rules.
    Each result includes a depth indicator and group_root for hierarchical organization.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        rules_lang = _resolve_rules_lang(data)
        search_engine = _get_engine_for_lang(rules_lang)

        query = data.get("query", "").strip()

        # Validate query
        is_valid, error_msg = validate_query(query)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Sanitize query
        query = sanitize_query(query)

        # Validate and parse max_results
        try:
            max_results_raw = data.get("max_results", 100)
            max_results = int(max_results_raw) if max_results_raw is not None else 100
        except (ValueError, TypeError):
            return jsonify({"error": f"max_results must be an integer, got {max_results_raw}"}), 400

        is_valid, error_msg = validate_max_results(max_results)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Validate filters
        variant_filter = data.get("variant_filter")
        is_valid, error_msg = validate_filter(variant_filter, current_app.config["VARIANTS"])
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        weapon_filter = data.get("weapon_filter")
        is_valid, error_msg = validate_filter(weapon_filter, current_app.config["WEAPONS"])
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        # Perform search
        results = search_engine.search(
            query,
            max_results=max_results,
            variant_filter=variant_filter,
            weapon_filter=weapon_filter,
        )

        # Convert results to JSON with depth and grouping info
        results_data = []
        current_group = None

        for r in results:
            depth = search_engine.get_rule_depth(r.rule_id)

            # Determine group root for hierarchy visualization
            if depth >= 4:
                # For level 4-5 rules, find the main parent (depth 2)
                lineage = search_engine.get_rule_lineage(r.rule_id)
                # Take the second element if it exists (first is the prefix like "GEN")
                current_group = lineage[1] if len(lineage) > 1 else r.rule_id
            else:
                # For levels 1-3, the rule itself is a group anchor
                current_group = r.rule_id

            results_data.append(
                {
                    "rule_id": r.rule_id,
                    "text": r.text,
                    "section": r.section,
                    "subsection": r.subsection,
                    "document": r.document,
                    "weapon_type": r.weapon_type,
                    "variant": r.variant or "general",
                    "score": r.score,
                    "depth": depth,
                    "group_root": current_group,
                }
            )

        # Log only successful, validated searches — keeps the dataset clean
        # for later alias-audit / curated-landing work. Validation failures and
        # exceptions are intentionally not logged. Wrapped so any logging error
        # cannot affect the response.
        try:
            log_search(
                query=query,
                rules_lang=rules_lang,
                result_count=len(results_data),
                top_rule_id=results_data[0]["rule_id"] if results_data else None,
                variant_filter=variant_filter,
                weapon_filter=weapon_filter,
            )
        except Exception:
            logger.exception("log_search failed (non-fatal)")

        return jsonify(
            {
                "success": True,
                "query": query,
                "rules_lang": rules_lang,
                "count": len(results_data),
                "results": results_data,
                "suggestions": (search_engine.suggest(query) if not results_data else []),
                "note": "Results grouped by rule hierarchy. Level 4-5 rules include parent rules (up to level 3) and direct child rules.",
            }
        )

    except ValueError as e:
        logger.warning(f"Invalid search request parameters: {e}")
        return jsonify({"error": "Invalid request parameters"}), 400
    except Exception as e:
        logger.error(f"Search error: {type(e).__name__}: {e}")
        return jsonify({"error": "Search failed"}), 500


@search_bp.route("/stats", methods=["GET"])
def api_stats() -> Any:
    """Get rulebook statistics"""
    try:
        rules_lang = _resolve_rules_lang()
        search_engine = _get_engine_for_lang(rules_lang)
        total_rules = len(search_engine.rules)
        vor_rules = sum(1 for r in search_engine.rules if r.get("variant") == "VOR")
        combat_rules = sum(1 for r in search_engine.rules if r.get("variant") == "COMBAT")
        ab_rules = sum(1 for r in search_engine.rules if r.get("variant") == "AFTERBLOW")
        longsword_rules = sum(1 for r in search_engine.rules if r.get("weapon_type") == "longsword")

        return jsonify(
            {
                "rules_lang": rules_lang,
                "total_rules": total_rules,
                "vor_rules": vor_rules,
                "combat_rules": combat_rules,
                "afterblow_rules": ab_rules,
                "longsword_rules": longsword_rules,
            }
        )
    except Exception as e:
        logger.error(f"Stats error: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to get statistics"}), 500


@search_bp.route("/extract", methods=["POST"])
def api_extract() -> Any:
    """Generate rulebook extract filtered by weapon and variant"""
    try:
        data = request.get_json() or {}
        rules_lang = _resolve_rules_lang(data)
        search_engine = _get_engine_for_lang(rules_lang)

        weapon_filter = normalize_filter(data.get("weapon_filter"), current_app.config["WEAPONS"])
        variant_filter = normalize_filter(
            data.get("variant_filter"), current_app.config["VARIANTS"]
        )

        filtered_rules = filter_rules_for_extract(
            search_engine.rules, weapon_filter, variant_filter
        )

        extract_text = format_extract_text(filtered_rules, weapon_filter, variant_filter)

        weapon_label = weapon_filter or "all-weapons"
        variant_label = variant_filter or "all-variants"
        filename = f"rulebook-extract_{rules_lang}_{weapon_label}_{variant_label}.md"

        return Response(
            extract_text,
            mimetype="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as e:
        logger.warning(f"Invalid extract request parameters: {e}")
        return jsonify({"error": "Invalid request parameters"}), 400
    except Exception as e:
        logger.error(f"Extract error: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to generate extract"}), 500


@search_bp.route("/rule/<rule_id>", methods=["GET"])
def api_rule(rule_id: str) -> Any:
    """Get a specific rule by ID"""
    try:
        rules_lang = _resolve_rules_lang()
        search_engine = _get_engine_for_lang(rules_lang)
        # Validate rule ID format
        from app.validation import validate_rule_id

        is_valid, error_msg = validate_rule_id(rule_id)
        if not is_valid:
            return jsonify({"error": error_msg}), 400

        rule = search_engine.get_rule_by_id(rule_id)
        if rule:
            return jsonify(
                {
                    "success": True,
                    "rules_lang": rules_lang,
                    "rule": {
                        "rule_id": rule["rule_id"],
                        "text": rule["text"],
                        "section": rule.get("section", ""),
                        "subsection": rule.get("subsection", ""),
                        "document": rule.get("document", ""),
                        "weapon_type": rule.get("weapon_type", ""),
                        "variant": rule.get("variant", ""),
                        "anchor_id": rule.get("anchor_id", ""),
                    },
                }
            )
        return jsonify({"error": "Rule not found"}), 404
    except Exception as e:
        logger.error(f"Get rule error: {type(e).__name__}: {e}")
        return jsonify({"error": "Failed to retrieve rule"}), 500
