"""
AI services blueprint - handles Gemini-powered summarization
"""

import time
from flask import Blueprint, request, jsonify, current_app

ai_bp = Blueprint('ai', __name__, url_prefix='/api')

try:
    import google.generativeai as genai
except Exception:
    genai = None


def get_gemini_model():
    """Initialize and return Gemini model"""
    api_key = current_app.config['GEMINI_API_KEY']
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    if genai is None:
        raise RuntimeError("google-generativeai is not installed")
    
    genai.configure(api_key=api_key)
    model_name = current_app.config['GEMINI_MODEL']
    
    if model_name:
        return genai.GenerativeModel(model_name)

    for candidate in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]:
        try:
            return genai.GenerativeModel(candidate)
        except Exception:
            continue

    raise RuntimeError("No available Gemini model found. Set GEMINI_MODEL explicitly.")


def check_rate_limit(client_key: str) -> bool:
    """Check if client is within rate limit"""
    now = time.time()
    window_start = now - current_app.config['SUMMARY_RATE_LIMIT_WINDOW_SEC']
    timestamps = current_app.summary_requests.get(client_key, [])
    timestamps = [ts for ts in timestamps if ts >= window_start]
    
    if len(timestamps) >= current_app.config['SUMMARY_RATE_LIMIT_MAX']:
        current_app.summary_requests[client_key] = timestamps
        return False
    
    timestamps.append(now)
    current_app.summary_requests[client_key] = timestamps
    return True


def split_text_for_summary(text, max_chars=6000):
    """Split text into chunks for summarization"""
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


def build_rules_text_for_summary(rules):
    """Convert rules to text for summarization"""
    from app.utils import build_document_order
    
    doc_order = build_document_order(rules)
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


def summarize_with_gemini(text, language, format_type="standard"):
    """Generate summary using Gemini
    
    Args:
        text: Rules text to summarize
        language: "EN" or "HU"
        format_type: "standard" (paragraph) or "handout" (1-page bullet format)
    """
    model = get_gemini_model()
    target_language = "Hungarian" if language == "HU" else "English"
    
    if format_type == "handout":
        system_prompt = (
            f"You are creating a compact 1-page rule handout in {target_language}. "
            f"Format this as a clean, scannable reference sheet:\n"
            f"- Use bullet points (•) for key rules and exceptions\n"
            f"- Group related rules under clear section headers (e.g., '## Valid Targets', '## Penalties')\n"
            f"- Keep each bullet to 1-2 lines maximum\n"
            f"- Prioritize: valid actions, penalties, restrictions, special cases\n"
            f"- Use concise language (no fluff)\n"
            f"- Maximum 1 page when printed (keep it tight!)\n"
            f"- Do not invent rules or add explanations beyond what's provided"
        )
    else:
        system_prompt = (
            f"You are summarizing fencing competition rules. "
            f"Write a clean, concise, professional summary in {target_language}. "
            "Use short paragraphs or bullet points. Preserve key constraints, penalties, and exceptions. "
            "Do not invent rules."
        )

    chunks = split_text_for_summary(text)
    summaries = []
    for chunk in chunks:
        response = model.generate_content([
            system_prompt,
            "Rules to summarize:\n" + chunk
        ])
        summaries.append(response.text.strip())

    if len(summaries) == 1:
        return summaries[0]

    if format_type == "handout":
        merge_prompt = (
            f"Merge these rule summaries into a single 1-page handout in {target_language}:\n"
            f"- Combine related bullets under headers\n"
            f"- Remove any duplicates\n"
            f"- Keep it scannable and concise\n"
            f"- Maximum 1 printed page"
        )
    else:
        merge_prompt = (
            f"Combine the summaries into a single cohesive summary in {target_language}. "
            "Avoid repetition. Keep it compact and structured."
        )
    
    response = model.generate_content([
        merge_prompt,
        "Summaries:\n" + "\n\n".join(summaries)
    ])
    return response.text.strip()


@ai_bp.route('/summarize', methods=['POST'])
def api_summarize():
    """Summarize rules using Gemini
    
    Request body:
        {
            "mode": "extract" or "search",
            "format": "standard" or "handout" (default: "standard"),
            "language": "EN" or "HU",
            "query": "search query" (required if mode="search"),
            "weapon_filter": "longsword" etc (optional),
            "formatum_filter": "VOR" etc (optional)
        }
    
    Response:
        {
            "success": true,
            "format": "handout",
            "language": "EN",
            "summary": "..."
        }
    """
    try:
        from app.utils import normalize_filter, filter_rules_for_extract
        
        client_key = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        
        # Check shared token if configured
        if current_app.config['SUMMARY_SHARED_TOKEN']:
            provided = request.headers.get("X-Summary-Token", "").strip()
            if provided != current_app.config['SUMMARY_SHARED_TOKEN']:
                return jsonify({"error": "Unauthorized"}), 401

        if not check_rate_limit(client_key):
            return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

        data = request.get_json()
        mode = data.get("mode", "search")
        format_type = data.get("format", "standard")
        
        # Validate format
        if format_type not in ("standard", "handout"):
            return jsonify({"error": 'format must be "standard" or "handout"'}), 400
        
        language = normalize_filter(
            data.get("language"),
            current_app.config['SUMMARY_LANGUAGES']
        ) or "EN"

        if mode == "extract":
            weapon_filter = normalize_filter(
                data.get("weapon_filter"),
                current_app.config['WEAPONS']
            )
            formatum_filter = normalize_filter(
                data.get("formatum_filter"),
                current_app.config['FORMATS']
            )
            rules = filter_rules_for_extract(
                current_app.search_engine.rules,
                weapon_filter,
                formatum_filter
            )
        else:
            query = data.get("query", "").strip()
            if not query:
                return jsonify({"error": "Query cannot be empty"}), 400
            
            formatum_filter = normalize_filter(
                data.get("formatum_filter"),
                current_app.config['FORMATS']
            )
            weapon_filter = normalize_filter(
                data.get("weapon_filter"),
                current_app.config['WEAPONS']
            )
            results = current_app.search_engine.search(
                query,
                max_results=len(current_app.search_engine.rules),
                formatum_filter=formatum_filter,
                weapon_filter=weapon_filter
            )
            rules = [r.__dict__ for r in results]

        if not rules:
            return jsonify({"error": "No matching rules to summarize"}), 400

        summary_input = build_rules_text_for_summary(rules)
        summary = summarize_with_gemini(summary_input, language, format_type=format_type)

        return jsonify({
            "success": True,
            "format": format_type,
            "language": language,
            "summary": summary
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
