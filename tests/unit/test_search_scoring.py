"""Unit tests for search relevance scoring."""

from qa_tools.search_engine.search_scoring import (
    has_exact_rule_id_match,
    mask_rule_ids,
    matches_query,
    score_rule,
    split_rule_ids,
)

VOR = ["right of way", "priority", "prio"]


def _score(rule, *, query="", phrase_query="", terms=None, alias_groups=None):
    return score_rule(
        rule,
        query=query,
        phrase_query=phrase_query,
        terms=terms or [],
        alias_groups=alias_groups,
    )


def test_exact_rule_id_uses_dedicated_priority_tier():
    noisy_rule = {
        "rule_id": "GEN-1",
        "text": "Priority and target area rules apply to the valid target.",
        "section": "Priority and target area",
    }
    id_rule = {"rule_id": "GEN-2", "text": "Unrelated wording."}

    noisy_score = _score(
        noisy_rule,
        phrase_query="priority target area",
        terms=["priority", "target", "area"],
        alias_groups=[VOR],
    )
    id_score = _score(id_rule, query="GEN-2", phrase_query="GEN-2", terms=["gen"])

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


def test_alias_group_must_match_for_a_rule_to_score():
    matching = {"rule_id": "GEN-1", "text": "Priority applies to the target."}
    unrelated = {"rule_id": "GEN-2", "text": "Valid target areas are defined.", "variant": "VOR"}

    assert _score(matching, terms=["target"], alias_groups=[VOR]) > 0
    assert _score(unrelated, terms=["target"], alias_groups=[VOR]) == 0


def test_rule_metadata_alone_does_not_match():
    rule = {"rule_id": "LS-VOR-1", "text": "The attacker scores.", "variant": "VOR"}

    assert not matches_query(rule, terms=[], alias_groups=[VOR])
    assert _score(rule, alias_groups=[VOR]) == 0


def test_heading_alone_matches_but_ranks_below_rule_text():
    in_text = {"rule_id": "GEN-1", "text": "Priority applies."}
    in_heading = {
        "rule_id": "GEN-2",
        "text": "The rule applies.",
        "subsection": "Validity or priority of hits",
    }

    heading_score = _score(in_heading, alias_groups=[VOR])
    assert matches_query(in_heading, terms=[], alias_groups=[VOR])
    assert _score(in_text, alias_groups=[VOR]) > heading_score > 0


def test_each_alias_group_contributes_at_most_one_boost():
    rule = {
        "rule_id": "LS-VOR-1",
        "text": "Right of way, priority, and prio determine the attack.",
    }

    assert _score(rule, alias_groups=[VOR]) == 40


def test_every_term_and_alias_group_must_match():
    rule = {"rule_id": "GEN-1", "text": "Priority applies to the target."}

    assert matches_query(rule, terms=["target"], alias_groups=[VOR])
    assert not matches_query(rule, terms=["target", "missing"], alias_groups=[VOR])
    assert not matches_query(rule, terms=["target"], alias_groups=[VOR, ["penalty"]])


def test_section_matches_are_weaker_than_rule_text_matches():
    in_text = {"rule_id": "GEN-1", "text": "Priority applies."}
    in_section = {"rule_id": "GEN-2", "text": "The rule applies.", "section": "Priority"}

    assert _score(in_text, terms=["priority"]) > _score(in_section, terms=["priority"])


def test_long_text_penalty_remains_effective():
    short_rule = {"rule_id": "GEN-1", "text": "Priority applies."}
    long_rule = {"rule_id": "GEN-2", "text": "Priority applies. " + ("Other words. " * 300)}

    assert _score(short_rule, terms=["priority"]) > _score(long_rule, terms=["priority"])


def test_split_rule_ids_separates_ids_from_keywords():
    remaining, ids = split_rule_ids("see LS-VOR-1.1.3 and gen-6.2.1. referee")

    assert ids == ["ls-vor-1.1.3", "gen-6.2.1"]
    assert "ls" not in remaining.lower()
    assert "referee" in remaining


def test_split_rule_ids_leaves_ordinary_hyphenated_words_alone():
    remaining, ids = split_rule_ids("right-of-way after-blow")

    assert ids == []
    assert remaining == "right-of-way after-blow"


def test_exact_rule_id_match_ignores_trailing_punctuation_but_not_longer_ids():
    assert has_exact_rule_id_match("GEN-6.2.1.", "GEN-6.2.1")
    assert has_exact_rule_id_match("(GEN-6.2.1)", "GEN-6.2.1")
    assert not has_exact_rule_id_match("GEN-6.2.1.1", "GEN-6.2.1")


def test_cross_reference_ids_are_masked_in_rule_text():
    assert "vor" not in mask_rule_ids("See [LS-VOR-1.3.4], [LS-AB-1.2.5].").lower()
    assert (
        mask_rule_ids("In Longsword-VOR, a started attack") == "In Longsword-VOR, a started attack"
    )


def test_cross_reference_ids_do_not_match_alias_or_keyword_words():
    citing = {"rule_id": "DIS-3.2.1", "text": "See [LS-VOR-1.3.4] and [GEN-6.2.1]."}
    plain_vor = {"rule_id": "GEN-1", "text": "In Longsword-VOR, a started attack has priority."}

    assert not matches_query(citing, terms=[], alias_groups=[["vor"]])
    assert not matches_query(citing, terms=["gen"], alias_groups=[])
    assert matches_query(plain_vor, terms=[], alias_groups=[["vor"]])
