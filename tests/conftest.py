"""
Pytest configuration and shared fixtures
"""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# Ensure imports work even when pytest-pythonpath plugin is not installed (e.g., CI)
project_root = Path(__file__).parent.parent
src_root = project_root / "src"
for _path in (str(project_root), str(src_root)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


@pytest.fixture
def sample_rules() -> list[dict[str, Any]]:
    """Sample rules for testing"""
    return [
        {
            "rule_id": "GEN-1",
            "text": "General meeting rules and structure",
            "section": "Meeting Structure",
            "subsection": "",
            "document": "01-altalanos.md",
            "weapon_type": "general",
            "variant": "",
            "anchor_id": "GEN-1",
            "line_number": 10,
            "references_to": [],
            "references_from": [],
        },
        {
            "rule_id": "GEN-1.1",
            "text": "A meeting consists of exchanges",
            "section": "Meeting Structure",
            "subsection": "Exchange Rules",
            "document": "01-altalanos.md",
            "weapon_type": "general",
            "variant": "",
            "anchor_id": "GEN-1.1",
            "line_number": 15,
            "references_to": ["GEN-1"],
            "references_from": [],
        },
        {
            "rule_id": "LS-VOR-1",
            "text": "VOR variant longsword rules",
            "section": "VOR Variant",
            "subsection": "",
            "document": "02.a-hosszukard-VOR.md",
            "weapon_type": "longsword",
            "variant": "VOR",
            "anchor_id": "LS-VOR-1",
            "line_number": 20,
            "references_to": [],
            "references_from": [],
        },
        {
            "rule_id": "LS-VOR-1.1",
            "text": "VOR specific scoring rules for longsword",
            "section": "VOR Variant",
            "subsection": "Scoring",
            "document": "02.a-hosszukard-VOR.md",
            "weapon_type": "longsword",
            "variant": "VOR",
            "anchor_id": "LS-VOR-1.1",
            "line_number": 25,
            "references_to": ["LS-VOR-1"],
            "references_from": [],
        },
        {
            "rule_id": "LS-COMBAT-1",
            "text": "COMBAT variant longsword rules",
            "section": "COMBAT Variant",
            "subsection": "",
            "document": "02.b-hosszukard-COMBAT.md",
            "weapon_type": "longsword",
            "variant": "COMBAT",
            "anchor_id": "LS-COMBAT-1",
            "line_number": 30,
            "references_to": [],
            "references_from": [],
        },
        {
            "rule_id": "LS-COMBAT-1.1.1.1",
            "text": "Detailed COMBAT scoring rule at depth 4",
            "section": "COMBAT Variant",
            "subsection": "Scoring Details",
            "document": "02.b-hosszukard-COMBAT.md",
            "weapon_type": "longsword",
            "variant": "COMBAT",
            "anchor_id": "LS-COMBAT-1.1.1.1",
            "line_number": 40,
            "references_to": ["LS-COMBAT-1"],
            "references_from": [],
        },
        {
            "rule_id": "LS-AB-1",
            "text": "AFTERBLOW variant longsword rules",
            "section": "AFTERBLOW Variant",
            "subsection": "",
            "document": "02.c-hosszukard-AFTERBLOW.md",
            "weapon_type": "longsword",
            "variant": "AFTERBLOW",
            "anchor_id": "LS-AB-1",
            "line_number": 50,
            "references_to": [],
            "references_from": [],
        },
    ]


@pytest.fixture
def sample_rules_index(tmp_path, sample_rules) -> Path:
    """Create a temporary rules index file"""
    index_data = {
        "rules": sample_rules,
        "total_rules": len(sample_rules),
        "documents": [
            "01-altalanos.md",
            "02.a-hosszukard-VOR.md",
            "02.b-hosszukard-COMBAT.md",
            "02.c-hosszukard-AFTERBLOW.md",
        ],
    }

    index_file = tmp_path / "rules_index.json"
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    return index_file


@pytest.fixture
def search_engine(sample_rules_index):
    """Create AliasAwareSearch instance for testing"""
    from qa_tools.search_engine import AliasAwareSearch

    return AliasAwareSearch(str(sample_rules_index))


@pytest.fixture
def app():
    """Create Flask app for testing"""
    from app import create_app

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()
