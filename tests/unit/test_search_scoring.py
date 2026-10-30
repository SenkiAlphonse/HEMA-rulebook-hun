"""Unit tests for search relevance scoring."""

from qa_tools.search_engine.search_scoring import has_exact_rule_id_match, score_rule


def _score(rule, *, query="", phrase_query="", terms=None, aliases=None, **kwargs):
    return score_rule(
        rule,
        query=query,
        phrase_query=phrase_query,
        terms=terms or [],
        aliases=aliases or {},
        **kwargs,
    )


def test_exact_rule_id_uses_dedicated_priority_tier():
    noisy_rule = {
        "rule_id": "GEN-1",
        "text": "Priority and target area rules apply to the valid target.",
        "section": "Priority and target area",
        "variant": "VOR",
    }
    id_rule = {"rule_id": "GEN-2", "text": "Unrelated wording."}
    aliases = {
        "variants": {"VOR": ["right of way", "priority", "prio"]},
        "concepts": {},
        "weapons": {},
    }

    noisy_score = _score(
        noisy_rule,
        phrase_query="priority target area",
        terms=["priority", "target", "area"],
        aliases=aliases,
        variant_query="VOR",
    )
    id_score = _score(id_rule, query="GEN-2", phrase_query="GEN-2")

    assert has_exact_rule_id_match("Rule GEN-2, please", "GEN-2")
    assert not has_exact_rule_id_match("GEN-2.1", "GEN-2")
    assert id_score > noisy_score


def test_exact_phrase_ranks_above_the_same_terms_in_different_order():
    exact = {"rule_id": "GEN-1", "text": "Valid target area."}
    reordered = {"rule_id": "GEN-2", "text": "Area for a valid target."}

    exact_score = _score(
        exact,
        phrase_query="valid target area",
        terms=["valid", "target", "area"],
    )
    reordered_score = _score(
        reordered,
        phrase_query="valid target area",
        terms=["valid", "target", "area"],
    )

    assert exact_score > reordered_score


def test_term_matches_support_long_stems_without_rewarding_repetition():
    rule = {"rule_id": "GEN-1", "text": "Part target target target."}

    assert _score(rule, terms=["art"]) == 0
    assert _score(rule, terms=["target"]) == _score(rule, terms=["target", "target"])


def test_alias_boosts_do_not_gate_text_matches():
    general_rule = {"rule_id": "GEN-1", "text": "Valid target areas are defined."}
    aliases = {"variants": {"VOR": ["right of way"]}, "concepts": {}, "weapons": {}}

    score = _score(
        general_rule,
        terms=["target"],
        aliases=aliases,
        variant_query="VOR",
    )

    assert score == 10


def test_each_alias_category_contributes_at_most_one_boost():
    rule = {
        "rule_id": "LS-VOR-1",
        "text": "Right of way, priority, and prio determine the attack.",
        "variant": "VOR",
    }
    aliases = {
        "variants": {"VOR": ["right of way", "priority", "prio"]},
        "concepts": {},
        "weapons": {},
    }

    assert _score(rule, aliases=aliases, variant_query="VOR") == 40


def test_section_matches_are_weaker_than_rule_text_matches():
    in_text = {"rule_id": "GEN-1", "text": "Priority applies."}
    in_section = {"rule_id": "GEN-2", "text": "The rule applies.", "section": "Priority"}

    assert _score(in_text, terms=["priority"]) > _score(in_section, terms=["priority"])


def test_long_text_penalty_remains_effective():
    short_rule = {"rule_id": "GEN-1", "text": "Priority applies."}
    long_rule = {"rule_id": "GEN-2", "text": "Priority applies. " + ("Other words. " * 300)}

    assert _score(short_rule, terms=["priority"]) > _score(long_rule, terms=["priority"])
