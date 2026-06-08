"""
Unit tests for RulebookParser class
"""

import tempfile
from pathlib import Path

import pytest

from qa_tools.tools.parser import RulebookParser


class TestRulebookParser:
    """Test RulebookParser functionality"""

    def test_extract_weapon_info_longsword_vor(self):
        """Test weapon extraction for longsword VOR files"""
        parser = RulebookParser(".")
        weapon, variant = parser._extract_weapon_info("05.a-hosszukard-VOR.md")

        assert weapon == "longsword"
        assert variant == "VOR"

    def test_extract_weapon_info_longsword_combat(self):
        """Test weapon extraction for longsword COMBAT files"""
        parser = RulebookParser(".")
        weapon, variant = parser._extract_weapon_info("05.b-hosszukard-COMBAT.md")

        assert weapon == "longsword"
        assert variant == "COMBAT"

    def test_extract_weapon_info_longsword_afterblow(self):
        """Test weapon extraction for longsword AFTERBLOW files"""
        parser = RulebookParser(".")
        weapon, variant = parser._extract_weapon_info("05.c-hosszukard-AFTERBLOW.md")

        assert weapon == "longsword"
        assert variant == "AFTERBLOW"

    def test_extract_weapon_info_rapier(self):
        """Test weapon extraction for rapier files"""
        parser = RulebookParser(".")
        weapon, variant = parser._extract_weapon_info("06-rapir.md")

        assert weapon == "rapier"
        assert variant == ""

    def test_extract_weapon_info_general(self):
        """Test weapon extraction for general files"""
        parser = RulebookParser(".")
        weapon, variant = parser._extract_weapon_info("01-altalanos.md")

        assert weapon == "general"
        assert variant == ""

    def test_detect_variant_in_rule_text_vor(self):
        """Test VOR variant detection in rule text"""
        parser = RulebookParser(".")

        text = "**Vor**: This is a VOR specific rule"
        detected = parser._detect_variant_in_rule_text(text)
        assert detected == "VOR"

        text = "**Vor**:This is a VOR specific rule"
        detected = parser._detect_variant_in_rule_text(text)
        assert detected == "VOR"

    def test_detect_variant_in_rule_text_combat(self):
        """Test COMBAT variant detection in rule text"""
        parser = RulebookParser(".")

        text = "**Combat**: This is a COMBAT specific rule"
        detected = parser._detect_variant_in_rule_text(text)
        assert detected == "COMBAT"

    def test_detect_variant_in_rule_text_afterblow(self):
        """Test AFTERBLOW variant detection in rule text"""
        parser = RulebookParser(".")

        text = "**Afterblow**: This is an AFTERBLOW specific rule"
        detected = parser._detect_variant_in_rule_text(text)
        assert detected == "AFTERBLOW"

    def test_detect_variant_in_rule_text_none(self):
        """Test variant detection with no variant present"""
        parser = RulebookParser(".")

        text = "This is a general rule without variant"
        detected = parser._detect_variant_in_rule_text(text)
        assert detected == ""

    # Note: test_variant_to_subrule_index removed - method was dead code and has been deleted

    def test_rule_id_pattern(self):
        """Test rule ID pattern matching"""
        parser = RulebookParser(".")

        # Valid patterns
        assert parser.rule_id_pattern.match("**GEN-1**")
        assert parser.rule_id_pattern.match("**GEN-1.1**")
        assert parser.rule_id_pattern.match("**GEN-1.1.1**")
        assert parser.rule_id_pattern.match("**LS-VOR-1.1.1**")
        assert parser.rule_id_pattern.match("**LS-COMBAT-1.2.3.4**")

        # Invalid patterns
        assert not parser.rule_id_pattern.match("GEN-1")  # Missing **
        assert not parser.rule_id_pattern.match("**GEN**")  # No numeric part
        assert not parser.rule_id_pattern.match("**123**")  # No prefix

    def test_anchor_pattern(self):
        """Test anchor ID pattern matching"""
        parser = RulebookParser(".")

        match = parser.anchor_pattern.search('<span id="GEN-1"></span>')
        assert match is not None
        assert match.group(1) == "GEN-1"

        match = parser.anchor_pattern.search('<span id="LS-VOR-1.1"></span>')
        assert match is not None
        assert match.group(1) == "LS-VOR-1.1"

    def test_reference_pattern(self):
        """Test rule reference pattern matching"""
        parser = RulebookParser(".")

        text = "See rules [GEN-1.1] and [GEN-2.3.4] for details"
        matches = parser.reference_pattern.findall(text)

        assert "GEN-1.1" in matches
        assert "GEN-2.3.4" in matches
        assert len(matches) == 2

    def test_multiline_comments_excluded_from_index(self):
        """Rule IDs inside multi-line HTML comment blocks must not be indexed."""
        content = """\
# Test Section

**GEN-1.1**
Active rule text.

<!-- TODO
**GEN-1.2**
This rule is commented out and must not appear in the index.

**GEN-1.3**
Also commented out.
-->

**GEN-1.4**
Another active rule.
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", encoding="utf-8", delete=False
        ) as f:
            f.write(content)
            tmp_path = Path(f.name)

        try:
            parser = RulebookParser(".")
            parser.parse_file(tmp_path)
            indexed_ids = {r.rule_id for r in parser.rules}
        finally:
            tmp_path.unlink()

        assert "GEN-1.1" in indexed_ids
        assert "GEN-1.4" in indexed_ids
        assert "GEN-1.2" not in indexed_ids, "Commented-out rule must not be indexed"
        assert "GEN-1.3" not in indexed_ids, "Commented-out rule must not be indexed"
