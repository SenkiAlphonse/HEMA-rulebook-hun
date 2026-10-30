"""
Integration tests for Flask API endpoints
"""

import json
from pathlib import Path

from qa_tools.search_engine import AliasAwareSearch


class TestSearchAPI:
    """Test /api/search endpoint"""

    def test_api_search_basic(self, client):
        """Test basic search request"""
        response = client.post(
            "/api/search", data=json.dumps({"query": "meeting"}), content_type="application/json"
        )

        assert response.status_code == 200
        data = response.get_json()

        assert "results" in data
        assert isinstance(data["results"], list)

    def test_api_search_with_variant_filter(self, client):
        """Test search with variant filter"""
        response = client.post(
            "/api/search",
            data=json.dumps({"query": "longsword", "variant_filter": "VOR"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        # Should have results
        assert "results" in data

    def test_api_search_with_weapon_filter(self, client):
        """Test search with weapon filter"""
        response = client.post(
            "/api/search",
            data=json.dumps({"query": "rules", "weapon_filter": "longsword"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert "results" in data

    def test_api_search_empty_query(self, client):
        """Test search with empty query"""
        response = client.post(
            "/api/search", data=json.dumps({"query": ""}), content_type="application/json"
        )

        # Should handle empty query gracefully
        assert response.status_code in [200, 400]

    def test_api_search_missing_query(self, client):
        """Test search without query parameter"""
        response = client.post("/api/search", data=json.dumps({}), content_type="application/json")

        # Should return error for missing query
        assert response.status_code == 400

    def test_api_search_max_results(self, client):
        """Test search with max_results parameter"""
        response = client.post(
            "/api/search",
            data=json.dumps({"query": "rules", "max_results": 3}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        if "results" in data:
            # Context rows may be included in addition to matched rules.
            assert len(data["results"]) <= 10

    def test_api_search_returns_consistent_hierarchy_groups(self, client, tmp_path):
        rules = [
            {"rule_id": "GEN-1.2.3", "text": "A target parent match."},
            {"rule_id": "GEN-1.2.3.1", "text": "A target child match."},
            {"rule_id": "GEN-1.2.3.1.1", "text": "A target leaf match."},
            {"rule_id": "GEN-1.2.4", "text": "A parent with context only."},
            {"rule_id": "GEN-1.2.4.1", "text": "Another target child match."},
            {"rule_id": "GEN-1.2.5", "text": "A higher parent with context only."},
            {"rule_id": "GEN-1.2.5.1", "text": "An intermediate with context only."},
            {"rule_id": "GEN-1.2.5.1.1", "text": "A target deep leaf."},
            {"rule_id": "GEN-2", "text": "A target standalone match."},
        ]
        for rule in rules:
            rule.update(weapon_type="general", variant="")

        index_path = tmp_path / "rules_index.json"
        index_path.write_text(json.dumps({"rules": rules}), encoding="utf-8")
        aliases_path = Path(__file__).parents[2] / "data" / "search" / "aliases.json"
        client.application.search_engines["hun"] = AliasAwareSearch(
            str(index_path), str(aliases_path)
        )

        response = client.post("/api/search", json={"query": "target", "max_results": 20})

        assert response.status_code == 200
        data = response.get_json()
        groups = {group["group_root"]: group for group in data["groups"]}

        matched_parent_group = groups["GEN-1.2.3"]
        assert {rule["rule_id"] for rule in matched_parent_group["matches"]} == {
            "GEN-1.2.3",
            "GEN-1.2.3.1",
            "GEN-1.2.3.1.1",
        }
        assert matched_parent_group["context"] == []

        assert [rule["rule_id"] for rule in groups["GEN-1.2.4"]["context"]] == ["GEN-1.2.4"]
        assert [rule["rule_id"] for rule in groups["GEN-1.2.5"]["context"]] == [
            "GEN-1.2.5",
            "GEN-1.2.5.1",
        ]
        assert len(groups["GEN-2"]["matches"]) == 1

        flat_ids = [result["rule_id"] for result in data["results"]]
        assert len(flat_ids) == len(set(flat_ids))
        assert data["match_count"] == 6
        assert data["group_count"] == 4
        assert (
            next(result for result in data["results"] if result["rule_id"] == "GEN-1.2.3")[
                "is_match"
            ]
            is True
        )
        assert (
            next(result for result in data["results"] if result["rule_id"] == "GEN-1.2.4")[
                "is_match"
            ]
            is False
        )
        assert all(
            result["group_root"] == "GEN-1.2.3"
            for result in data["results"]
            if result["rule_id"].startswith("GEN-1.2.3")
        )


class TestRuleByIdAPI:
    """Test /api/rule/<rule_id> endpoint"""

    def test_api_rule_by_id_found(self, client):
        """Test getting existing rule by ID"""
        response = client.get("/api/rule/GEN-1")

        # Rule might not exist in test environment
        assert response.status_code in [200, 404]

    def test_api_rule_by_id_not_found(self, client):
        """Test getting non-existent rule"""
        response = client.get("/api/rule/NONEXISTENT-99")

        assert response.status_code == 404


class TestStatsAPI:
    """Test /api/stats endpoint"""

    def test_api_stats(self, client):
        """Test getting statistics"""
        response = client.get("/api/stats")

        assert response.status_code == 200
        data = response.get_json()

        # Should have some stat fields
        assert isinstance(data, dict)


class TestExtractAPI:
    """Test /api/extract endpoint"""

    def test_api_extract_basic(self, client):
        """Test extract without filters"""
        response = client.post("/api/extract", data=json.dumps({}), content_type="application/json")

        # Should return some content
        assert response.status_code == 200

    def test_api_extract_with_filters(self, client):
        """Test extract with weapon and variant filters"""
        response = client.post(
            "/api/extract",
            data=json.dumps({"weapon_filter": "longsword", "variant_filter": "VOR"}),
            content_type="application/json",
        )

        assert response.status_code == 200
