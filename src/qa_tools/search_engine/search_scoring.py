"""Deterministic, bounded scoring for rule search results."""

import re
import unicodedata
from functools import lru_cache
from typing import Any

from qa_tools.search_engine import search_config

# e.g. GEN-6.2.1, LS-VOR-1.1.3; a trailing sentence period is not part of the ID.
_RULE_ID = r"(?<![\w.-])[A-Z]+(?:-[A-Z0-9]+)*-\d+(?:\.\d+)*(?!\w|-|\.\w)"
_RULE_ID_IN_TEXT = re.compile(_RULE_ID)
_RULE_ID_IN_QUERY = re.compile(_RULE_ID, re.IGNORECASE)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def split_rule_ids(query: str) -> tuple[str, list[str]]:
    """Return the query without rule IDs, and the (lowercase) IDs it contained."""
    ids = [match.group(0).lower() for match in _RULE_ID_IN_QUERY.finditer(query)]
    return _RULE_ID_IN_QUERY.sub(" ", query), ids


@lru_cache(maxsize=4096)
def mask_rule_ids(text: str) -> str:
    """Blank out cross-reference IDs so their parts (LS, VOR, AB, ...) never match as words."""
    return _RULE_ID_IN_TEXT.sub(" ", text)


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
    pattern = r"(?<![\w.-])" + re.escape(rule_id.lower()) + r"(?!\w|-|\.\w)"
    return re.search(pattern, query.lower()) is not None


def _rule_fields(rule: dict[str, Any]) -> tuple[str, str]:
    """Return the rule's own text and its heading text, without cross-reference IDs."""
    text = rule.get("text_plain", rule.get("text", ""))
    headings = " ".join((rule.get("section", ""), rule.get("subsection", "")))
    return mask_rule_ids(text), mask_rule_ids(headings)


def matches_query(
    rule: dict[str, Any],
    *,
    terms: list[str],
    alias_groups: list[list[str]] | None = None,
) -> bool:
    """Return whether every term and every alias group occurs in the rule's text or headings."""
    fields = _rule_fields(rule)
    return all(any(_matches_term(field, term) for field in fields) for term in terms) and all(
        has_alias_match(fields, group) for group in alias_groups or []
    )


def score_rule(
    rule: dict[str, Any],
    *,
    query: str,
    phrase_query: str,
    terms: list[str],
    alias_groups: list[list[str]] | None = None,
) -> float:
    """Score a rule with bounded, whole-token relevance signals; 0 means no match."""
    exact_id_match = has_exact_rule_id_match(query, rule.get("rule_id", ""))
    if not exact_id_match and not matches_query(rule, terms=terms, alias_groups=alias_groups):
        return 0.0

    text, section_text = _rule_fields(rule)
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

    for group in alias_groups or []:
        if has_alias_match((text,), group):
            score += search_config.SCORE_ALIAS_TEXT
        if has_alias_match((section_text,), group):
            score += search_config.SCORE_ALIAS_SECTION

    text_length = len(rule.get("text_plain", rule.get("text", "")))
    if text_length > search_config.LENGTH_PENALTY_THRESHOLD:
        penalty = (
            text_length / float(search_config.LENGTH_PENALTY_THRESHOLD)
        ) ** search_config.LENGTH_PENALTY_EXP
        score /= penalty

    bounded_score = min(score, search_config.MAX_NON_ID_SCORE)
    if exact_id_match:
        return search_config.SCORE_RULE_ID_MATCH + bounded_score
    return bounded_score
