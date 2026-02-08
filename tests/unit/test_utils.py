"""
Unit tests for app/utils.py functions
"""

import pytest
from app.utils import (
    normalize_filter, 
    preprocess_rulebook_markdown,
    build_document_order
)
from search_utils import get_rule_depth


class TestNormalizeFilter:
    """Test normalize_filter function"""
    
    def test_normalize_filter_valid(self):
        """Test with valid filter value"""
        result = normalize_filter("VOR", ["VOR", "COMBAT", "AFTERBLOW"])
        assert result == "VOR"
    
    def test_normalize_filter_lowercase(self):
        """Test with lowercase input"""
        result = normalize_filter("vor", ["VOR", "COMBAT", "AFTERBLOW"])
        assert result == "VOR"
    
    def test_normalize_filter_invalid(self):
        """Test with invalid filter value"""
        result = normalize_filter("INVALID", ["VOR", "COMBAT", "AFTERBLOW"])
        assert result is None
    
    def test_normalize_filter_none(self):
        """Test with None value"""
        result = normalize_filter(None, ["VOR", "COMBAT", "AFTERBLOW"])
        assert result is None
    
    def test_normalize_filter_empty_list(self):
        """Test with empty allowed list"""
        result = normalize_filter("VOR", [])
        assert result is None


class TestPreprocessMarkdown:
    """Test preprocess_rulebook_markdown function"""
    
    def test_preprocess_markdown_comment_removal(self):
        """Test HTML comment removal"""
        text = "Some text <!-- This is a comment --> more text"
        result = preprocess_rulebook_markdown(text)
        
        assert "<!--" not in result
        assert "comment" not in result
        assert "Some text" in result
        assert "more text" in result
    
    def test_preprocess_markdown_anchor_removal(self):
        """Test anchor span removal"""
        text = 'Some text <span id="GEN-1"></span> more text'
        result = preprocess_rulebook_markdown(text)
        
        assert '<span id="GEN-1"></span>' not in result
        assert "Some text" in result
        assert "more text" in result
    
    def test_preprocess_markdown_hard_breaks(self):
        """Test rule ID hard break conversion"""
        text = "**GEN-1.1.1**  \nSome rule text"
        result = preprocess_rulebook_markdown(text)
        
        # Should convert double-space newline to double newline
        assert "**GEN-1.1.1**\n\n" in result
    
    def test_preprocess_markdown_rule_references(self):
        """Test rule reference conversion to links"""
        text = "See rule [GEN-1.1] for details"
        result = preprocess_rulebook_markdown(text)
        
        # Should convert [GEN-1.1] to <a> tag
        assert '<a href="#GEN-1.1"' in result
        assert 'class="rule-ref"' in result
        assert 'data-rule-id="GEN-1.1"' in result
    
    def test_preprocess_markdown_multiline_comment(self):
        """Test multiline HTML comment removal"""
        text = """Some text
<!-- This is a
multiline comment -->
more text"""
        result = preprocess_rulebook_markdown(text)
        
        assert "<!--" not in result
        assert "multiline comment" not in result
        assert "Some text" in result
        assert "more text" in result


class TestBuildDocumentOrder:
    """Test build_document_order function"""
    
    def test_build_document_order(self, sample_rules):
        """Test building document order mapping"""
        order = build_document_order(sample_rules)
        
        # Should have entries for each unique document
        assert "01-altalanos.md" in order
        assert "02.a-hosszukard-VOR.md" in order
        assert "02.b-hosszukard-COMBAT.md" in order
        
        # Order should be consistent
        assert isinstance(order["01-altalanos.md"], int)
        assert order["01-altalanos.md"] >= 0
    
    def test_build_document_order_empty(self):
        """Test with empty rules list"""
        order = build_document_order([])
        assert order == {}


class TestGetRuleDepth:
    """Test get_rule_depth utility function"""
    
    def test_get_rule_depth_level_1(self):
        """Test depth calculation for level 1 rules"""
        assert get_rule_depth("GEN-1") == 1
        assert get_rule_depth("LS-VOR-1") == 1
    
    def test_get_rule_depth_level_2(self):
        """Test depth calculation for level 2 rules"""
        assert get_rule_depth("GEN-1.1") == 2
        assert get_rule_depth("LS-COMBAT-2.3") == 2
    
    def test_get_rule_depth_level_3(self):
        """Test depth calculation for level 3 rules"""
        assert get_rule_depth("GEN-1.1.1") == 3
    
    def test_get_rule_depth_level_4(self):
        """Test depth calculation for level 4 rules"""
        assert get_rule_depth("GEN-6.7.4.2") == 4
        assert get_rule_depth("LS-AB-1.2.10.2") == 4
    
    def test_get_rule_depth_level_5(self):
        """Test depth calculation for level 5 rules"""
        assert get_rule_depth("GEN-1.2.3.4.5") == 5
    
    def test_get_rule_depth_invalid(self):
        """Test with invalid rule ID"""
        assert get_rule_depth("") == 0
        assert get_rule_depth("INVALID") == 0
