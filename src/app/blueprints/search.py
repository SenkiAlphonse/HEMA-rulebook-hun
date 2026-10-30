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


def _read_json_object(*, optional: bool = False) -> tuple[dict[str, Any] | None, Any]:
    """Read the request body as a JSON object; return (payload, error_response).

    A missing body counts as an empty object when optional; any other unusable body is a 400.
    """
    data = request.get_json(silent=True)
    if data is None and optional and not request.get_data():
        return {}, None
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Request body must be a JSON object"}), 400)
    return data, None


def _extract_filter(
    data: dict[str, Any], key: str, allowed: list[str]
) -> tuple[str | None, str | None]:
    """Return (canonical filter value or None, error message or None) for an optional filter."""
    raw = data.get(key)
    value = normalize_filter(raw, allowed)
    if value is None:
        is_valid, error_msg = validate_filter(raw, allowed)
        return None, (None if is_valid else error_msg)
    return value, None


@search_bp.route("/search", methods=["POST"])
def api_search() -> Any:
    """Search for rules by keyword

    Returns ranked flat results for compatibility and hierarchy-aware groups for display.
    """
    try:
        data, error_response = _read_json_object()
        if error_response:
            return error_response

        rules_lang = _resolve_rules_lang(data)
        search_engine = _get_engine_for_lang(rules_lang)

        query = data.get("query", "")

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
        result_groups = search_engine.search_grouped(
            query,
            max_results=max_results,
            variant_filter=variant_filter,
            weapon_filter=weapon_filter,
        )

        def serialize_result(result, group_root, is_match, score):
            return {
                "rule_id": result.rule_id,
                "text": result.text,
                "section": result.section,
                "subsection": result.subsection,
                "document": result.document,
                "weapon_type": result.weapon_type,
                "variant": result.variant or "general",
                "score": score,
                "depth": search_engine.get_rule_depth(result.rule_id),
                "group_root": group_root,
                "is_match": is_match,
            }

        results_data = []
        groups_data = []
        match_count = 0

        for group in result_groups:
            context_data = [
                serialize_result(context, group.group_root, False, score=None)
                for context in group.context
            ]
            matches_data = [
                serialize_result(match, group.group_root, True, score=match.score)
                for match in group.matches
            ]
            cited_by_data = [
                serialize_result(citing, group.group_root, False, score=None)
                for citing in group.cited_by
            ]
            match_count += len(matches_data)
            context_score = max((match.score for match in group.matches), default=0.0)
            results_data.extend(
                [
                    *[
                        serialize_result(context, group.group_root, False, score=context_score)
                        for context in group.context
                    ],
                    *matches_data,
                ]
            )
            groups_data.append(
                {
                    "group_root": group.group_root,
                    "context": context_data,
                    "matches": matches_data,
                    "cited_by": cited_by_data,
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
                result_count=match_count,
                top_rule_id=(result_groups[0].matches[0].rule_id if result_groups else None),
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
                "match_count": match_count,
                "group_count": len(groups_data),
                "groups": groups_data,
                "suggestions": (search_engine.suggest(query) if not match_count else []),
                "note": "Flat results are retained for compatibility; groups separate matched rules from hierarchy context and from rules citing a rule named by ID.",
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
        data, error_response = _read_json_object(optional=True)
        if error_response:
            return error_response

        rules_lang = _resolve_rules_lang(data)
        search_engine = _get_engine_for_lang(rules_lang)

        weapon_filter, error_msg = _extract_filter(
            data, "weapon_filter", current_app.config["WEAPONS"]
        )
        if error_msg:
            return jsonify({"error": error_msg}), 400

        variant_filter, error_msg = _extract_filter(
            data, "variant_filter", current_app.config["VARIANTS"]
        )
        if error_msg:
            return jsonify({"error": error_msg}), 400

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
