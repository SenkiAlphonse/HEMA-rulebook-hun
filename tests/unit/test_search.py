"""
Unit tests for RulebookSearch class
"""

import pytest
from search import RulebookSearch, SearchResult


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
    
    def test_formatum_filter_vor(self, search_engine):
        """Test VOR formatum filtering"""
        results = search_engine.search("longsword", formatum_filter="VOR")
        
        # Should only return VOR or general rules
        for result in results:
            assert result.formatum in ["VOR", ""], \
                f"Expected VOR or empty, got {result.formatum}"
    
    def test_formatum_filter_combat(self, search_engine):
        """Test COMBAT formatum filtering"""
        results = search_engine.search("longsword", formatum_filter="COMBAT")
        
        # Should only return COMBAT or general rules
        for result in results:
            assert result.formatum in ["COMBAT", ""], \
                f"Expected COMBAT or empty, got {result.formatum}"
    
    def test_formatum_filter_afterblow(self, search_engine):
        """Test AFTERBLOW formatum filtering"""
        results = search_engine.search("longsword", formatum_filter="AFTERBLOW")
        
        # Should only return AFTERBLOW or general rules
        for result in results:
            assert result.formatum in ["AFTERBLOW", ""], \
                f"Expected AFTERBLOW or empty, got {result.formatum}"
    
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
        
        assert rule_upper == rule_lower
    
    def test_rule_by_id_not_found(self, search_engine):
        """Test get_rule_by_id with non-existent ID"""
        rule = search_engine.get_rule_by_id("NONEXISTENT-99")
        
        assert rule is None
    
    def test_search_empty_query(self, search_engine):
        """Test search with empty query"""
        results = search_engine.search("", max_results=10)
        
        # Empty query returns all rules (no filtering)
        assert len(results) == 8
    
    def test_weapon_filter(self, search_engine):
        """Test weapon type filtering"""
        results = search_engine.search("rules", weapon_filter="longsword")
        
        # Should only return longsword or general rules
        for result in results:
            assert result.weapon_type in ["longsword", "general"], \
                f"Expected longsword or general, got {result.weapon_type}"
    
    def test_search_by_rule_id(self, search_engine):
        """Test searching by exact rule ID"""
        results = search_engine.search("GEN-1.1")
        
        # Should find the rule
        assert len(results) > 0
        # The exact match should score highest
        assert results[0].rule_id == "GEN-1.1"
    
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
                assert results[i].score >= results[i + 1].score, \
                    "Results should be ordered by score (descending)"
    
    def test_detect_formatum_in_query(self, search_engine):
        """Test formatum detection from query text"""
        # Test VOR detection
        detected = search_engine._detect_formatum_in_query("VOR rules")
        assert detected == "VOR"
        
        # Test COMBAT detection
        detected = search_engine._detect_formatum_in_query("COMBAT format")
        assert detected == "COMBAT"
        
        # Test AFTERBLOW detection
        detected = search_engine._detect_formatum_in_query("AFTERBLOW scoring")
        assert detected == "AFTERBLOW"
        
        # Test no detection
        detected = search_engine._detect_formatum_in_query("general rules")
        assert detected == ""
    
    def test_get_rules_by_section(self, search_engine):
        """Test getting rules by section name"""
        results = search_engine.get_rules_by_section("VOR Format")
        
        assert len(results) > 0
        assert all("VOR Format" in r["section"] for r in results)
    
    def test_rule_depth_calculation(self, search_engine):
        """Test rule depth calculation"""
        assert search_engine._get_rule_depth("GEN-1") == 1
        assert search_engine._get_rule_depth("GEN-1.1") == 2
        assert search_engine._get_rule_depth("LS-COMBAT-1.1.1.1") == 4
    
    def test_rule_lineage(self, search_engine):
        """Test rule lineage calculation"""
        lineage = search_engine._get_rule_lineage("GEN-1.1")
        assert "GEN" in lineage
        assert "GEN-1" in lineage
        
        lineage = search_engine._get_rule_lineage("LS-COMBAT-1.1.1.1")
        assert "LS-COMBAT" in lineage
        assert "LS-COMBAT-1" in lineage
        assert "LS-COMBAT-1.1" in lineage
        assert "LS-COMBAT-1.1.1" in lineage
