"""
Integration tests for Flask API endpoints
"""

import json
from pathlib import Path

import pytest

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

    @pytest.mark.parametrize(
        "kwargs",
        [
            {},
            {"data": "{bad", "content_type": "application/json"},
            {"data": "x=1", "content_type": "text/plain"},
            {"json": [1, 2]},
            {"json": "text"},
        ],
        ids=["no-body", "malformed-json", "wrong-content-type", "json-list", "json-string"],
    )
    def test_api_search_unusable_body_is_a_client_error(self, client, kwargs):
        response = client.post("/api/search", **kwargs)

        assert response.status_code == 400
        assert "JSON object" in response.get_json()["error"]

    @pytest.mark.parametrize("query", [5, None, ["a"], {"a": 1}])
    def test_api_search_non_string_query_is_a_client_error(self, client, query):
        response = client.post("/api/search", json={"query": query})

        assert response.status_code == 400
        assert response.get_json()["error"] == "Query must be a string"

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

    def test_api_search_by_rule_id_lists_citing_rules_per_group(self, client, tmp_path):
        rules = [
            {"rule_id": "GEN-1", "text": "A cited rule.", "references_from": ["GEN-2"]},
            {"rule_id": "GEN-2", "text": "It cites [GEN-1]."},
        ]
        for rule in rules:
            rule.update(weapon_type="general", variant="")
        index_path = tmp_path / "rules_index.json"
        index_path.write_text(json.dumps({"rules": rules}), encoding="utf-8")
        aliases_path = Path(__file__).parents[2] / "data" / "search" / "aliases.json"
        client.application.search_engines["hun"] = AliasAwareSearch(
            str(index_path), str(aliases_path)
        )

        by_id = client.post("/api/search", json={"query": "GEN-1"}).get_json()
        by_keyword = client.post("/api/search", json={"query": "cited"}).get_json()

        (group,) = by_id["groups"]
        assert [rule["rule_id"] for rule in group["matches"]] == ["GEN-1"]
        assert [rule["rule_id"] for rule in group["cited_by"]] == ["GEN-2"]
        assert group["cited_by"][0]["is_match"] is False
        assert by_id["match_count"] == 1
        assert [rule["rule_id"] for rule in by_id["results"]] == ["GEN-1"]
        assert all(group["cited_by"] == [] for group in by_keyword["groups"])


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

    def test_api_extract_without_body_returns_everything(self, client):
        response = client.post("/api/extract")

        assert response.status_code == 200
        assert "all-weapons_all-variants" in response.headers["Content-Disposition"]

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"data": "{bad", "content_type": "application/json"},
            {"json": [1]},
        ],
        ids=["malformed-json", "json-list"],
    )
    def test_api_extract_unusable_body_is_a_client_error(self, client, kwargs):
        assert client.post("/api/extract", **kwargs).status_code == 400

    @pytest.mark.parametrize(
        "filters",
        [{"weapon_filter": "NOPE"}, {"variant_filter": "NOPE"}, {"variant_filter": 5}],
    )
    def test_api_extract_rejects_invalid_filters(self, client, filters):
        response = client.post("/api/extract", json=filters)

        assert response.status_code == 400
        assert "filter" in response.get_json()["error"].lower()

    @pytest.mark.parametrize("weapon", ["rapier", "Rapier", "RAPIER"])
    def test_api_extract_weapon_filter_keeps_only_that_weapon_and_general_rules(
        self, client, tmp_path, weapon
    ):
        rules = [
            {"rule_id": "GEN-1", "text": "General rule.", "weapon_type": "general"},
            {"rule_id": "LS-1", "text": "Longsword rule.", "weapon_type": "longsword"},
            {"rule_id": "RP-1", "text": "Rapier rule.", "weapon_type": "rapier"},
        ]
        for line_number, rule in enumerate(rules):
            rule.update(document="doc.md", line_number=line_number, variant="")
        index_path = tmp_path / "rules_index.json"
        index_path.write_text(json.dumps({"rules": rules}), encoding="utf-8")
        aliases_path = Path(__file__).parents[2] / "data" / "search" / "aliases.json"
        client.application.search_engines["hun"] = AliasAwareSearch(
            str(index_path), str(aliases_path)
        )

        response = client.post("/api/extract", json={"weapon_filter": weapon})
        text = response.get_data(as_text=True)

        assert response.status_code == 200
        assert "_rapier_" in response.headers["Content-Disposition"]
        assert "Weapon: rapier" in text
        assert "GEN-1" in text
        assert "RP-1" in text
        assert "LS-1" not in text
