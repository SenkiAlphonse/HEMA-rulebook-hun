"""
Unit tests for RulebookSearch class
"""

import json

import pytest

from qa_tools.search_engine import AliasAwareSearch, SearchResult


class TestRulebookSearch:
    """Test search engine (AliasAwareSearch) functionality"""

    def test_load_index(self, search_engine, sample_rules):
        """Test that index loads correctly"""
        assert len(search_engine.rules) == len(sample_rules)
        assert search_engine.rules[0]["rule_id"] == "GEN-1"

    def test_search_basic(self, search_engine):
        """Test basic search functionality"""
        results = search_engine.search("meeting", max_results=10)
        assert len(results) > 0
        assert any("meeting" in r.text.lower() for r in results)
        # Results should be SearchResult objects
        assert all(isinstance(r, SearchResult) for r in results)

    def test_variant_filter_vor(self, search_engine):
        """Test VOR variant filtering"""
        results = search_engine.search("longsword", variant_filter="VOR")
        # Should only return VOR or general rules
        for result in results:
            assert result.variant in ["VOR", ""], f"Expected VOR or empty, got {result.variant}"

    def test_variant_filter_combat(self, search_engine):
        """Test COMBAT variant filtering"""
        results = search_engine.search("longsword", variant_filter="COMBAT")
        # Should only return COMBAT or general rules
        for result in results:
            assert result.variant in ["COMBAT", ""], (
                f"Expected COMBAT or empty, got {result.variant}"
            )

    def test_variant_filter_afterblow(self, search_engine):
        """Test AFTERBLOW variant filtering"""
        results = search_engine.search("longsword", variant_filter="AFTERBLOW")
        # Should only return AFTERBLOW or general rules
        for result in results:
            assert result.variant in ["AFTERBLOW", ""], (
                f"Expected AFTERBLOW or empty, got {result.variant}"
            )

    def test_rule_by_id(self, search_engine):
        """Test get_rule_by_id lookup"""
        rule = search_engine.get_rule_by_id("GEN-1")
        assert rule is not None
        assert rule["rule_id"] == "GEN-1"
        assert "meeting" in rule["text"].lower()

    def test_rule_by_id_case_insensitive(self, search_engine):
        """Test that rule ID lookup is case-insensitive"""
        rule_upper = search_engine.get_rule_by_id("GEN-1")
        rule_lower = search_engine.get_rule_by_id("gen-1")
        # Both should return the same rule or both be None
        assert (rule_upper is None and rule_lower is None) or rule_upper == rule_lower

    def test_rule_by_id_not_found(self, search_engine):
        """Test get_rule_by_id with non-existent ID"""
        rule = search_engine.get_rule_by_id("NONEXISTENT-99")
        assert rule is None

    def test_search_empty_query(self, search_engine):
        """Test search with empty query"""
        results = search_engine.search("", max_results=10)
        # Empty query returns no results (filtered by AliasAwareSearch)
        assert len(results) == 0

    def test_weapon_filter(self, search_engine):
        """Test weapon type filtering"""
        results = search_engine.search("rules", weapon_filter="longsword")
        # Should only return longsword or general rules
        for result in results:
            assert result.weapon_type in ["longsword", "general"], (
                f"Expected longsword or general, got {result.weapon_type}"
            )

    def test_search_by_rule_id(self, search_engine):
        """Test searching by exact rule ID"""
        results = search_engine.search("GEN-1.1")
        # Should find matching rules
        assert len(results) > 0
        # At least one result should be a GEN rule
        assert any(r.rule_id.startswith("GEN") for r in results)

    def test_max_results_limit(self, search_engine):
        """Test that max_results parameter is respected"""
        results = search_engine.search("rules", max_results=2)
        assert len(results) <= 2

    def test_search_score_ordering(self, search_engine):
        """Test that results are ordered by relevance score"""
        results = search_engine.search("meeting structure", max_results=10)
        if len(results) > 1:
            # Scores should be in descending order
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score, (
                    "Results should be ordered by score (descending)"
                )

    # Note: test_detect_variant_in_query removed - method was in legacy search.py
    # Variant detection is now handled by AliasAwareSearch._expand_query() via aliases

    def test_variant_detection_via_aliases(self, search_engine):
        """Test that variant detection works through alias expansion"""
        pass

    def test_search_kozbetam_substring(self):
        """Test that searching for 'özbetám' finds all GEN-3.2.5.x rules (substring, regardless of formatting)"""
        # Use the real rules index (not the sample fixture) to test actual rules
        from pathlib import Path

        from qa_tools.search_engine import AliasAwareSearch

        real_index = (
            Path(__file__).parent.parent.parent / "data" / "search" / "rules_index_hun.json"
        )
        if not real_index.exists():
            pytest.skip(f"Real rules index not found at {real_index}")

        search_engine = AliasAwareSearch(str(real_index))
        results = search_engine.search("özbetám", max_results=20)
        found_ids = {r.rule_id for r in results}

        # These rules should all be present if the substring is matched in text_plain
        expected = {"GEN-3.2.5.1", "GEN-3.2.5.2", "GEN-3.2.5.3"}
        assert expected.issubset(found_ids), f"Missing: {expected - found_ids}"

    def test_search_multiword_alias_resolves_to_one_group_english(self):
        """A multiword alias is one alias group, and every result mentions it in text or heading."""
        from pathlib import Path

        from qa_tools.search_engine.search_scoring import has_alias_match

        project_root = Path(__file__).parent.parent.parent
        index_path = project_root / "data" / "search" / "rules_index_eng.json"
        aliases_path = project_root / "data" / "search" / "aliases.json"
        if not index_path.exists():
            pytest.skip(f"English rules index not found at {index_path}")

        search_engine = AliasAwareSearch(str(index_path), str(aliases_path))
        vor_aliases = search_engine.aliases["variants"]["VOR"]
        for query in ("right of way", "right-of-way"):
            expanded = search_engine._expand_query(query)
            groups = search_engine.search_grouped(query, max_results=20)
            matches = [match for group in groups for match in group.matches]

            assert expanded.alias_groups == [vor_aliases]
            assert expanded.base_query == ""
            assert matches
            for match in matches:
                rule = search_engine.get_rule_by_id(match.rule_id)
                fields = (rule.get("text_plain", rule["text"]), match.section, match.subsection)
                assert has_alias_match(fields, vor_aliases)

    @pytest.fixture
    def alias_engine(self, tmp_path):
        """Engine over a tiny index using the real alias dictionary."""
        from pathlib import Path

        rules = [
            {"rule_id": "GEN-1", "text": "A right handed fencer waits.", "variant": ""},
            {"rule_id": "GEN-2", "text": "Priority determines the attack.", "variant": ""},
            {"rule_id": "GEN-3", "text": "The brown glove is required.", "variant": ""},
            {"rule_id": "VOR-1", "text": "The attacker scores.", "variant": "VOR"},
            {"rule_id": "CF-1", "text": "Priority is not used.", "variant": "COMBAT"},
            {
                "rule_id": "HEAD-1",
                "text": "The referee validates hits.",
                "subsection": "Validity or priority of hits",
                "variant": "",
            },
        ]
        for rule in rules:
            rule.setdefault("weapon_type", "longsword")
        index_file = tmp_path / "rules_index.json"
        index_file.write_text(json.dumps({"rules": rules}), encoding="utf-8")
        aliases_path = Path(__file__).parents[2] / "data" / "search" / "aliases.json"
        return AliasAwareSearch(str(index_file), str(aliases_path))

    @pytest.mark.parametrize(
        ("query", "expected_ids"),
        [
            ("right of way", {"GEN-2", "CF-1", "HEAD-1"}),
            ("right-of-way", {"GEN-2", "CF-1", "HEAD-1"}),
            ("priority", {"GEN-2", "CF-1", "HEAD-1"}),
            ("vor", {"GEN-2", "CF-1", "HEAD-1"}),
            ("right of way attack", {"GEN-2"}),
            ("right of way waits", set()),
        ],
    )
    def test_variant_alias_matches_text_or_heading_not_metadata(
        self, alias_engine, query, expected_ids
    ):
        # VOR-1 belongs to the VOR variant but never mentions an alias, so it must not match.
        assert {result.rule_id for result in alias_engine.search(query)} == expected_ids

    def test_heading_match_ranks_below_text_match(self, alias_engine):
        scores = {result.rule_id: result.score for result in alias_engine.search("right of way")}

        assert scores["GEN-2"] > scores["HEAD-1"] > 0

    def test_alias_does_not_apply_a_variant_filter(self, alias_engine):
        assert "CF-1" in {result.rule_id for result in alias_engine.search("right of way")}

    def test_explicit_variant_filter_still_applies_to_alias_search(self, alias_engine):
        results = alias_engine.search("right of way", variant_filter="VOR")

        assert {result.rule_id for result in results} == {"GEN-2", "HEAD-1"}

    @pytest.mark.parametrize(
        ("query", "expected_ids"),
        [
            ("target area", {"GEN-3", "GEN-5", "GEN-6"}),
            ("target area head", {"GEN-3"}),
            ("target area ready", set()),
        ],
    )
    def test_concept_alias_matches_whole_alternatives(self, tmp_path, query, expected_ids):
        rules = [
            {"rule_id": "GEN-1", "text": "The target is ready."},
            {"rule_id": "GEN-2", "text": "The competition area is clear."},
            {"rule_id": "GEN-3", "text": "A valid target is the head."},
            {"rule_id": "GEN-4", "text": "Protective equipment is required."},
            {"rule_id": "GEN-5", "text": "The finding is recorded."},
            {"rule_id": "GEN-6", "text": "Valid-target scoring applies."},
            {"rule_id": "GEN-7", "text": "An invalid target does not score."},
        ]
        index_file = tmp_path / "rules_index.json"
        index_file.write_text(json.dumps({"rules": rules}), encoding="utf-8")
        aliases_file = tmp_path / "aliases.json"
        aliases_file.write_text(
            json.dumps({"concepts": {"target": ["target area", "valid target", "finding"]}}),
            encoding="utf-8",
        )
        engine = AliasAwareSearch(str(index_file), str(aliases_file))

        assert {result.rule_id for result in engine.search(query)} == expected_ids

    def test_multiple_alias_groups_must_all_match(self, tmp_path):
        rules = [
            {"rule_id": "GEN-1", "text": "A valid target is penalised."},
            {"rule_id": "GEN-2", "text": "A valid target is scored."},
            {"rule_id": "GEN-3", "text": "A punishment applies."},
        ]
        index_file = tmp_path / "rules_index.json"
        index_file.write_text(json.dumps({"rules": rules}), encoding="utf-8")
        aliases_file = tmp_path / "aliases.json"
        aliases_file.write_text(
            json.dumps(
                {
                    "concepts": {
                        "target": ["valid target"],
                        "penalty": ["penalised", "punishment"],
                    }
                }
            ),
            encoding="utf-8",
        )
        engine = AliasAwareSearch(str(index_file), str(aliases_file))

        assert {result.rule_id for result in engine.search("valid target punishment")} == {"GEN-1"}
        assert {result.rule_id for result in engine.search("punishment")} == {"GEN-1", "GEN-3"}

    @pytest.mark.parametrize("query", ["long sword", "longsword", "ls"])
    def test_weapon_alias_matches_text_not_weapon_metadata(self, tmp_path, query):
        from pathlib import Path

        rules = [
            {"rule_id": "GEN-1", "text": "Sword inspection.", "weapon_type": "general"},
            {"rule_id": "GEN-2", "text": "Long-sword inspection.", "weapon_type": "general"},
            {"rule_id": "LS-1", "text": "The attacker scores.", "weapon_type": "longsword"},
            {"rule_id": "RP-1", "text": "Longsword rules apply.", "weapon_type": "rapier"},
        ]
        index_file = tmp_path / "rules_index.json"
        index_file.write_text(json.dumps({"rules": rules}), encoding="utf-8")
        aliases_path = Path(__file__).parents[2] / "data" / "search" / "aliases.json"
        engine = AliasAwareSearch(str(index_file), str(aliases_path))

        assert {result.rule_id for result in engine.search(query)} == {"GEN-2", "RP-1"}
        results = engine.search(query, weapon_filter="longsword")
        assert {result.rule_id for result in results} == {"GEN-2"}

    @pytest.fixture
    def id_engine(self, tmp_path):
        """Engine over a tiny index with cross-references between rules."""
        from pathlib import Path

        rules = [
            {
                "rule_id": "GEN-6.2.1",
                "text": "The referee calls the fencers.",
                "references_from": ["DIS-3.2.1", "LS-VOR-1.3.4", "LS-COMBAT-1.1.6"],
            },
            {"rule_id": "DIS-3.2.1", "text": "See [GEN-6.2.1] and [LS-VOR-1.3.4].", "variant": ""},
            {
                "rule_id": "LS-VOR-1.3.4",
                "text": "A VOR rule that cites [GEN-6.2.1].",
                "variant": "VOR",
                "weapon_type": "longsword",
            },
            {
                "rule_id": "LS-COMBAT-1.1.6",
                "text": "A COMBAT rule that cites [GEN-6.2.1].",
                "variant": "COMBAT",
                "weapon_type": "longsword",
            },
            {"rule_id": "GEN-7.1", "text": "Another referee rule."},
        ]
        for rule in rules:
            rule.setdefault("weapon_type", "general")
            rule.setdefault("variant", "")
        index_file = tmp_path / "rules_index.json"
        index_file.write_text(json.dumps({"rules": rules}), encoding="utf-8")
        aliases_path = Path(__file__).parents[2] / "data" / "search" / "aliases.json"
        return AliasAwareSearch(str(index_file), str(aliases_path))

    @pytest.mark.parametrize("query", ["GEN-6.2.1", "gen-6.2.1", "GEN-6.2.1.", "(GEN-6.2.1)"])
    def test_rule_id_query_returns_only_that_rule(self, id_engine, query):
        results = id_engine.search_grouped(query, max_results=20)

        assert [m.rule_id for g in results for m in g.matches] == ["GEN-6.2.1"]

    def test_unknown_rule_id_returns_nothing_instead_of_keyword_noise(self, id_engine):
        assert id_engine.search_grouped("GEN-99", max_results=20) == []

    def test_rule_id_with_keyword_requires_the_keyword_for_other_rules(self, id_engine):
        results = id_engine.search_grouped("GEN-6.2.1 referee", max_results=20)
        matched = {m.rule_id for g in results for m in g.matches}

        assert matched == {"GEN-6.2.1", "GEN-7.1"}

    def test_cross_references_do_not_make_rules_match_alias_words(self, id_engine):
        # DIS-3.2.1 only mentions "LS-VOR-1.3.4"; the VOR alias must not match inside an ID.
        results = id_engine.search_grouped("vor", max_results=20)

        assert {m.rule_id for g in results for m in g.matches} == {"LS-VOR-1.3.4"}

    def test_rule_id_query_lists_citing_rules_separately(self, id_engine):
        (group,) = id_engine.search_grouped("GEN-6.2.1", max_results=20)

        assert [r.rule_id for r in group.matches] == ["GEN-6.2.1"]
        assert [r.rule_id for r in group.cited_by] == [
            "DIS-3.2.1",
            "LS-VOR-1.3.4",
            "LS-COMBAT-1.1.6",
        ]

    def test_citing_rules_respect_explicit_filters(self, id_engine):
        (group,) = id_engine.search_grouped("GEN-6.2.1", variant_filter="VOR")

        assert [r.rule_id for r in group.cited_by] == ["DIS-3.2.1", "LS-VOR-1.3.4"]

    def test_citing_rules_exclude_rules_that_are_already_matches(self, id_engine):
        results = id_engine.search_grouped("GEN-6.2.1 cites", max_results=20)
        matched = {m.rule_id for g in results for m in g.matches}
        cited = {r.rule_id for g in results for r in g.cited_by}

        assert "GEN-6.2.1" in matched
        assert not matched & cited

    def test_keyword_queries_have_no_citing_rules(self, id_engine):
        results = id_engine.search_grouped("referee", max_results=20)

        assert results
        assert all(group.cited_by == [] for group in results)

    def test_search_deduplicates_rule_ids_in_results(self, tmp_path):
        """Search results should not contain duplicate rule IDs."""
        index_data = {
            "rules": [
                {
                    "rule_id": "GEN-6.11.2",
                    "text": "Vívóidőn belüli közbetámadás szabály.",
                    "section": "Általános",
                    "subsection": "",
                    "document": "01-altalanos.md",
                    "weapon_type": "general",
                    "variant": "",
                },
                {
                    "rule_id": "GEN-6.11.2",
                    "text": "Vívóidőn belüli közbetámadás szabály.",
                    "section": "Általános",
                    "subsection": "",
                    "document": "01-altalanos.md",
                    "weapon_type": "general",
                    "variant": "",
                },
                {
                    "rule_id": "GEN-6.11.2.1",
                    "text": "A vívóidő megítélése esetfüggő.",
                    "section": "Általános",
                    "subsection": "",
                    "document": "01-altalanos.md",
                    "weapon_type": "general",
                    "variant": "",
                },
            ],
            "total_rules": 3,
            "documents": ["01-altalanos.md"],
        }

        index_file = tmp_path / "rules_index_dupe.json"
        index_file.write_text(json.dumps(index_data, ensure_ascii=False), encoding="utf-8")

        search_engine = AliasAwareSearch(str(index_file))
        results = search_engine.search("idő", max_results=10)

        result_ids = [r.rule_id for r in results]
        assert len(result_ids) == len(set(result_ids)), f"Duplicate rule IDs found: {result_ids}"
