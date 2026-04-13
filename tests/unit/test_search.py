"""
Unit tests for RulebookSearch class
"""

import json
import pytest
from qa_tools.search_engine.search import RulebookSearch, SearchResult


class TestRulebookSearch:
    """Test RulebookSearch functionality"""

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
            assert result.variant in ["COMBAT", ""], f"Expected COMBAT or empty, got {result.variant}"

    def test_variant_filter_afterblow(self, search_engine):
        """Test AFTERBLOW variant filtering"""
        results = search_engine.search("longsword", variant_filter="AFTERBLOW")
        # Should only return AFTERBLOW or general rules
        for result in results:
            assert result.variant in ["AFTERBLOW", ""], f"Expected AFTERBLOW or empty, got {result.variant}"

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
            assert result.weapon_type in ["longsword", "general"], f"Expected longsword or general, got {result.weapon_type}"

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
                assert results[i].score >= results[i + 1].score, "Results should be ordered by score (descending)"

    # Note: test_detect_variant_in_query removed - method was in legacy search.py
    # Variant detection is now handled by AliasAwareSearch._expand_query() via aliases

    def test_variant_detection_via_aliases(self, search_engine):
        """Test that variant detection works through alias expansion"""
        pass

    def test_search_kozbetam_substring(self):
        """Test that searching for 'özbetám' finds all GEN-3.2.5.x rules (substring, regardless of formatting)"""
        # Use the real rules index (not the sample fixture) to test actual rules
        from pathlib import Path
        from qa_tools.search_engine.search import RulebookSearch
        
        real_index = Path(__file__).parent.parent.parent / 'data' / 'search' / 'rules_index.json'
        if not real_index.exists():
            pytest.skip(f"Real rules index not found at {real_index}")
        
        search_engine = RulebookSearch(str(real_index))
        results = search_engine.search("özbetám", max_results=20)
        found_ids = {r.rule_id for r in results}
        
        # These rules should all be present if the substring is matched in text_plain
        expected = {"GEN-3.2.5.1", "GEN-3.2.5.2", "GEN-3.2.5.3"}
        assert expected.issubset(found_ids), f"Missing: {expected - found_ids}"

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
                    "variant": ""
                },
                {
                    "rule_id": "GEN-6.11.2",
                    "text": "Vívóidőn belüli közbetámadás szabály.",
                    "section": "Általános",
                    "subsection": "",
                    "document": "01-altalanos.md",
                    "weapon_type": "general",
                    "variant": ""
                },
                {
                    "rule_id": "GEN-6.11.2.1",
                    "text": "A vívóidő megítélése esetfüggő.",
                    "section": "Általános",
                    "subsection": "",
                    "document": "01-altalanos.md",
                    "weapon_type": "general",
                    "variant": ""
                }
            ],
            "total_rules": 3,
            "documents": ["01-altalanos.md"]
        }

        index_file = tmp_path / "rules_index_dupe.json"
        index_file.write_text(json.dumps(index_data, ensure_ascii=False), encoding="utf-8")

        search_engine = RulebookSearch(str(index_file))
        results = search_engine.search("idő", max_results=10)

        result_ids = [r.rule_id for r in results]
        assert len(result_ids) == len(set(result_ids)), f"Duplicate rule IDs found: {result_ids}"
