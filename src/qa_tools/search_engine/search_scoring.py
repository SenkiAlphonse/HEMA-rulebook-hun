"""Deterministic, bounded scoring for rule search results."""

import re
import unicodedata
from typing import Any

from qa_tools.search_engine import search_config


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _matches_phrase(text: str, phrase: str) -> bool:
    tokens = re.findall(r"\w+", normalize_text(phrase))
    if not tokens:
        return False
    pattern = r"(?<!\w)" + r"\W+".join(re.escape(token) for token in tokens) + r"(?!\w)"
    return re.search(pattern, normalize_text(text)) is not None


def _matches_term(text: str, term: str) -> bool:
    normalized_term = normalize_text(term)
    if len(normalized_term) < 4:
        return _matches_phrase(text, normalized_term)
    return any(normalized_term in token for token in re.findall(r"\w+", normalize_text(text)))


def has_alias_match(fields: tuple[str, ...], aliases: list[str] | None) -> bool:
    """Return whether any alias matches any searchable field."""
    return any(_matches_phrase(field, alias) for field in fields for alias in aliases or [])


def has_exact_rule_id_match(query: str, rule_id: str) -> bool:
    """Return whether the query contains this complete rule ID, not a prefix."""
    if not query or not rule_id:
        return False
    pattern = r"(?<![\w.-])" + re.escape(rule_id.lower()) + r"(?![\w.-])"
    return re.search(pattern, query.lower()) is not None


def score_rule(
    rule: dict[str, Any],
    *,
    query: str,
    phrase_query: str,
    terms: list[str],
    aliases: dict[str, Any],
    concept_terms: list[str] | None = None,
    variant_query: str | None = None,
    weapon_query: str | None = None,
) -> float:
    """Score one eligible rule using bounded, whole-token relevance signals."""
    text = rule.get("text_plain", rule.get("text", ""))
    section = rule.get("section", "")
    subsection = rule.get("subsection", "")
    section_text = " ".join((section, subsection))
    exact_id_match = has_exact_rule_id_match(query, rule.get("rule_id", ""))
    score = 0.0

    if phrase_query and _matches_phrase(text, phrase_query):
        score += search_config.SCORE_EXACT_PHRASE_TEXT
    if phrase_query and _matches_phrase(section_text, phrase_query):
        score += search_config.SCORE_EXACT_PHRASE_SECTION

    for term in dict.fromkeys(terms):
        if _matches_term(text, term):
            score += search_config.SCORE_TERM_MATCH
        if _matches_term(section_text, term):
            score += search_config.SCORE_TERM_SECTION

    searchable_fields = (text, section, subsection)
    categories = (
        (
            concept_terms,
            None,
            None,
            search_config.SCORE_CONCEPT_TERM,
        ),
        (
            aliases.get("variants", {}).get(variant_query, []),
            variant_query,
            "variant",
            search_config.SCORE_VARIANT_ALIAS,
        ),
        (
            aliases.get("weapons", {}).get(weapon_query, []),
            weapon_query,
            "weapon_type",
            search_config.SCORE_WEAPON_ALIAS,
        ),
    )

    for category_aliases, key, metadata_field, weight in categories:
        if not category_aliases:
            continue
        metadata_matches = metadata_field is not None and rule.get(metadata_field) == key
        alias_matches = has_alias_match(searchable_fields, list(dict.fromkeys(category_aliases)))
        if metadata_matches or alias_matches:
            score += weight

    text_length = len(text)
    if text_length > search_config.LENGTH_PENALTY_THRESHOLD:
        penalty = (
            text_length / float(search_config.LENGTH_PENALTY_THRESHOLD)
        ) ** search_config.LENGTH_PENALTY_EXP
        score /= penalty

    bounded_score = min(score, search_config.MAX_NON_ID_SCORE)
    if exact_id_match:
        return search_config.SCORE_RULE_ID_MATCH + bounded_score
    return bounded_score
