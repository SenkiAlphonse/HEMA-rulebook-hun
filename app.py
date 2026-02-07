"""
HEMA Rulebook Search Web App
Flask application for searching the HEMA rulebook
"""

import json
import os
import sys
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - optional dependency
    genai = None

qa_dir = Path(__file__).parent / "qa-tools"
sys.path.insert(0, str(qa_dir))
from search_aliases import AliasAwareSearch

app = Flask(__name__)

# Load search engine
search_engine = AliasAwareSearch(
    str(qa_dir / "rules_index.json"),
    str(qa_dir / "aliases.json")
)

# Cache for format and weapon options
FORMATS = ["VOR", "COMBAT", "AFTERBLOW"]
WEAPONS = ["longsword", "rapier", "padded_weapons"]
SUMMARY_LANGUAGES = ["HU", "EN"]
SUMMARY_RATE_LIMIT_WINDOW_SEC = int(os.environ.get("SUMMARY_RATE_LIMIT_WINDOW_SEC", 3600))
SUMMARY_RATE_LIMIT_MAX = int(os.environ.get("SUMMARY_RATE_LIMIT_MAX", 10))
SUMMARY_SHARED_TOKEN = os.environ.get("SUMMARY_SHARED_TOKEN", "").strip()
_summary_requests = {}


def _get_gemini_model():
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    if genai is None:
        raise RuntimeError("google-generativeai is not installed")
    genai.configure(api_key=api_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash-latest")
    return genai.GenerativeModel(model_name)


def _check_rate_limit(client_key: str) -> bool:
    now = time.time()
    window_start = now - SUMMARY_RATE_LIMIT_WINDOW_SEC
    timestamps = _summary_requests.get(client_key, [])
    timestamps = [ts for ts in timestamps if ts >= window_start]
    if len(timestamps) >= SUMMARY_RATE_LIMIT_MAX:
        _summary_requests[client_key] = timestamps
        return False
    timestamps.append(now)
    _summary_requests[client_key] = timestamps
    return True


def _split_text_for_summary(text, max_chars=6000):
    chunks = []
    current = []
    current_len = 0
    for line in text.splitlines():
        line_len = len(line) + 1
        if current_len + line_len > max_chars and current:
            chunks.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks


def _build_rules_text_for_summary(rules):
    doc_order = _build_document_order(rules)
    sorted_rules = sorted(
        rules,
        key=lambda r: (
            doc_order.get(r.get("document", ""), 9999),
            int(r.get("line_number", 0)),
            r.get("rule_id", "")
        )
    )
    parts = []
    for rule in sorted_rules:
        parts.append(f"[{rule.get('rule_id','')}] {rule.get('text','').strip()}")
    return "\n".join(parts)


def _summarize_with_gemini(text, language):
    model = _get_gemini_model()
    target_language = "Hungarian" if language == "HU" else "English"
    system_prompt = (
        f"You are summarizing fencing competition rules. "
        f"Write a clean, concise, professional summary in {target_language}. "
        "Use short paragraphs or bullet points. Preserve key constraints, penalties, and exceptions. "
        "Do not invent rules."
    )

    chunks = _split_text_for_summary(text)
    summaries = []
    for chunk in chunks:
        response = model.generate_content([
            system_prompt,
            "Rules to summarize:\n" + chunk
        ])
        summaries.append(response.text.strip())

    if len(summaries) == 1:
        return summaries[0]

    merge_prompt = (
        f"Combine the summaries into a single cohesive summary in {target_language}. "
        "Avoid repetition. Keep it compact and structured."
    )
    response = model.generate_content([
        merge_prompt,
        "Summaries:\n" + "\n\n".join(summaries)
    ])
    return response.text.strip()


def _normalize_filter(value, allowed):
    if value and value in allowed:
        return value
    return None


def _build_document_order(rules):
    order = {}
    next_index = 0
    for rule in rules:
        doc = rule.get("document", "")
        if doc and doc not in order:
            order[doc] = next_index
            next_index += 1
    return order


def _filter_rules_for_extract(rules, weapon_filter, formatum_filter):
    filtered = []
    for rule in rules:
        rule_weapon = rule.get("weapon_type", "general")
        rule_formatum = rule.get("formatum") or ""

        if weapon_filter and rule_weapon not in ["general", weapon_filter]:
            continue

        if formatum_filter and rule_formatum not in ["", formatum_filter]:
            continue

        filtered.append(rule)
    return filtered


def _format_extract_text(rules, weapon_filter, formatum_filter):
    title_parts = ["Rulebook Extract"]
    if weapon_filter:
        title_parts.append(f"Weapon: {weapon_filter}")
    if formatum_filter:
        title_parts.append(f"Format: {formatum_filter}")

    doc_order = _build_document_order(rules)
    sorted_rules = sorted(
        rules,
        key=lambda r: (
            doc_order.get(r.get("document", ""), 9999),
            int(r.get("line_number", 0)),
            r.get("rule_id", "")
        )
    )

    output_lines = []
    output_lines.append("# " + " | ".join(title_parts))
    output_lines.append("")

    current_doc = None
    current_section = None
    current_subsection = None

    for rule in sorted_rules:
        doc = rule.get("document", "")
        section = rule.get("section", "")
        subsection = rule.get("subsection", "")

        if doc != current_doc:
            output_lines.append(f"\n## Document: {doc}")
            current_doc = doc
            current_section = None
            current_subsection = None

        if section and section != current_section:
            output_lines.append(f"\n### {section}")
            current_section = section
            current_subsection = None

        if subsection and subsection != current_subsection:
            output_lines.append(f"\n#### {subsection}")
            current_subsection = subsection

        output_lines.append(f"\n**{rule.get('rule_id', '')}**")
        output_lines.append(rule.get("text", "").strip())

    output_lines.append("")
    return "\n".join(output_lines)


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
        max_results = min(int(data.get("max_results", 100)), 100)  # Cap at 100
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


@app.route("/api/extract", methods=["POST"])
def api_extract():
    """Generate a rulebook extract by weapon/format filters"""
    try:
        data = request.get_json()
        weapon_filter = _normalize_filter(data.get("weapon_filter"), WEAPONS)
        formatum_filter = _normalize_filter(data.get("formatum_filter"), FORMATS)

        filtered_rules = _filter_rules_for_extract(
            search_engine.rules,
            weapon_filter,
            formatum_filter
        )

        extract_text = _format_extract_text(
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


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    """Summarize rules using Gemini (all matching rules, no cap)."""
    try:
        client_key = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        if SUMMARY_SHARED_TOKEN:
            provided = request.headers.get("X-Summary-Token", "").strip()
            if provided != SUMMARY_SHARED_TOKEN:
                return jsonify({"error": "Unauthorized"}), 401

        if not _check_rate_limit(client_key):
            return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

        data = request.get_json()
        mode = data.get("mode", "search")
        language = _normalize_filter(data.get("language"), SUMMARY_LANGUAGES) or "EN"

        if mode == "extract":
            weapon_filter = _normalize_filter(data.get("weapon_filter"), WEAPONS)
            formatum_filter = _normalize_filter(data.get("formatum_filter"), FORMATS)
            rules = _filter_rules_for_extract(
                search_engine.rules,
                weapon_filter,
                formatum_filter
            )
        else:
            query = data.get("query", "").strip()
            if not query:
                return jsonify({"error": "Query cannot be empty"}), 400
            formatum_filter = _normalize_filter(data.get("formatum_filter"), FORMATS)
            weapon_filter = _normalize_filter(data.get("weapon_filter"), WEAPONS)
            rules = search_engine.search(
                query,
                max_results=len(search_engine.rules),
                formatum_filter=formatum_filter,
                weapon_filter=weapon_filter
            )
            rules = [r.__dict__ for r in rules]

        if not rules:
            return jsonify({"error": "No matching rules to summarize"}), 400

        summary_input = _build_rules_text_for_summary(rules)
        summary = _summarize_with_gemini(summary_input, language)

        return jsonify({
            "success": True,
            "language": language,
            "summary": summary
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
