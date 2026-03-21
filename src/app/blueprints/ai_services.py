"""
AI services blueprint - handles Gemini-powered summarization
"""

import time
import logging
from flask import Blueprint, request, jsonify, current_app
from app.config import GEMINI_MODEL_CANDIDATES

# Configure logging
logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/api')
VALID_RULESET_LANGS = {"hun", "eng"}

try:
    import google.generativeai as genai
except ImportError:
    logger.warning("google-generativeai module not available - AI features disabled")
    genai = None
except Exception as e:
    logger.error(f"Unexpected error importing google-generativeai: {e}")
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
        try:
            return genai.GenerativeModel(model_name)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model '{model_name}': {e}")
            raise

    for candidate in GEMINI_MODEL_CANDIDATES:
        try:
            logger.debug(f"Attempting to initialize model: {candidate}")
            return genai.GenerativeModel(candidate)
        except Exception as e:
            logger.debug(f"Model {candidate} not available: {e}")
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


def build_rules_text_for_summary(rules, max_chars=None):
    """Convert rules to text for summarization with optional character cap.

    Returns:
        tuple[str, int, bool]: (summary_text, included_rule_count, truncated)
    """
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
    included_count = 0
    current_chars = 0
    truncated = False

    for rule in sorted_rules:
        rule_prefix = f"[{rule.get('rule_id','')}] "
        rule_text = rule.get('text', '').strip()
        line = f"{rule_prefix}{rule_text}"
        line_len = len(line) + 1

        if max_chars is not None and current_chars + line_len > max_chars:
            remaining_chars = max_chars - current_chars
            min_required = len(rule_prefix) + len("...") + 1
            if remaining_chars >= min_required:
                clipped_text_len = remaining_chars - len(rule_prefix) - len("...") - 1
                clipped_text = rule_text[:clipped_text_len].rstrip()
                parts.append(f"{rule_prefix}{clipped_text}...")
                included_count += 1
            truncated = True
            break

        parts.append(line)
        included_count += 1
        current_chars += line_len

    return "\n".join(parts), included_count, truncated


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

    chunk_size = current_app.config['SUMMARY_CHUNK_SIZE']
    chunks = split_text_for_summary(text, max_chars=chunk_size)
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
            "mode": "search",
            "format": "standard" or "handout" (default: "standard"),
            "language": "EN" or "HU",
            "query": "search query" (required if mode="search"),
            "weapon_filter": "longsword" etc (optional),
            "variant_filter": "VOR" etc (optional)
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
        from app.utils import normalize_filter
        
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

        if mode != "search":
            return jsonify({"error": 'Only mode="search" is supported'}), 400
        
        # Validate format
        if format_type not in ("standard", "handout"):
            return jsonify({"error": 'format must be "standard" or "handout"'}), 400
        
        language = normalize_filter(
            data.get("language"),
            current_app.config['SUMMARY_LANGUAGES']
        ) or "EN"

        raw_rules_lang = data.get("rules_lang", "hun")
        rules_lang = str(raw_rules_lang).strip().lower()
        if rules_lang not in VALID_RULESET_LANGS:
            return jsonify({"error": f"Invalid rules_lang '{raw_rules_lang}'. Use 'hun' or 'eng'."}), 400

        search_engine = getattr(current_app, "search_engines", {}).get(rules_lang, current_app.search_engine)

        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query cannot be empty"}), 400

        variant_filter = normalize_filter(
            data.get("variant_filter"),
            current_app.config['VARIANTS']
        )
        weapon_filter = normalize_filter(
            data.get("weapon_filter"),
            current_app.config['WEAPONS']
        )

        max_rules = current_app.config['SUMMARY_SEARCH_MAX_RULES']
        results = search_engine.search(
            query,
            max_results=max_rules,
            variant_filter=variant_filter,
            weapon_filter=weapon_filter
        )
        rules = [r.__dict__ for r in results]

        if not rules:
            return jsonify({"error": "No matching rules to summarize"}), 400

        summary_input, included_rule_count, input_truncated = build_rules_text_for_summary(
            rules,
            max_chars=current_app.config['SUMMARY_MAX_INPUT_CHARS']
        )

        if not summary_input.strip():
            return jsonify({"error": "Matching rules are too large to summarize under current limits"}), 400

        summary = summarize_with_gemini(summary_input, language, format_type=format_type)

        return jsonify({
            "success": True,
            "format": format_type,
            "language": language,
            "rules_lang": rules_lang,
            "summary": summary,
            "rule_count_total": len(rules),
            "rule_count_summarized": included_rule_count,
            "input_truncated": input_truncated
        })
    except ValueError as e:
        logger.warning(f"Invalid summary request parameters: {e}")
        return jsonify({"error": "Invalid request parameters"}), 400
    except Exception as e:
        logger.exception(f"Summary error: {type(e).__name__}")
        return jsonify({"error": "Failed to generate summary"}), 500
