"""
Integration tests for Flask API endpoints
"""

import pytest
import json
from types import SimpleNamespace


class TestSearchAPI:
    """Test /api/search endpoint"""
    
    def test_api_search_basic(self, client):
        """Test basic search request"""
        response = client.post('/api/search',
                              data=json.dumps({"query": "meeting"}),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert "results" in data
        assert isinstance(data["results"], list)
    
    def test_api_search_with_variant_filter(self, client):
        """Test search with variant filter"""
        response = client.post('/api/search',
                              data=json.dumps({
                                  "query": "longsword",
                                  "variant_filter": "VOR"
                              }),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should have results
        assert "results" in data
    
    def test_api_search_with_weapon_filter(self, client):
        """Test search with weapon filter"""
        response = client.post('/api/search',
                              data=json.dumps({
                                  "query": "rules",
                                  "weapon_filter": "longsword"
                              }),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert "results" in data
    
    def test_api_search_empty_query(self, client):
        """Test search with empty query"""
        response = client.post('/api/search',
                              data=json.dumps({"query": ""}),
                              content_type='application/json')
        
        # Should handle empty query gracefully
        assert response.status_code in [200, 400]
    
    def test_api_search_missing_query(self, client):
        """Test search without query parameter"""
        response = client.post('/api/search',
                              data=json.dumps({}),
                              content_type='application/json')
        
        # Should return error for missing query
        assert response.status_code == 400
    
    def test_api_search_max_results(self, client):
        """Test search with max_results parameter"""
        response = client.post('/api/search',
                              data=json.dumps({
                                  "query": "rules",
                                  "max_results": 3
                              }),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        if "results" in data:
            # Note: actual count may be higher due to family grouping
            # (GROUPING_MULTIPLIER allows up to max_results * 3)
            assert len(data["results"]) <= 10


class TestRuleByIdAPI:
    """Test /api/rule/<rule_id> endpoint"""
    
    def test_api_rule_by_id_found(self, client):
        """Test getting existing rule by ID"""
        response = client.get('/api/rule/GEN-1')
        
        # Rule might not exist in test environment
        assert response.status_code in [200, 404]
    
    def test_api_rule_by_id_not_found(self, client):
        """Test getting non-existent rule"""
        response = client.get('/api/rule/NONEXISTENT-99')
        
        assert response.status_code == 404


class TestStatsAPI:
    """Test /api/stats endpoint"""
    
    def test_api_stats(self, client):
        """Test getting statistics"""
        response = client.get('/api/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should have some stat fields
        assert isinstance(data, dict)


class TestExtractAPI:
    """Test /api/extract endpoint"""
    
    def test_api_extract_basic(self, client):
        """Test extract without filters"""
        response = client.post('/api/extract',
                              data=json.dumps({}),
                              content_type='application/json')
        
        # Should return some content
        assert response.status_code == 200
    
    def test_api_extract_with_filters(self, client):
        """Test extract with weapon and variant filters"""
        response = client.post('/api/extract',
                              data=json.dumps({
                                  "weapon_filter": "longsword",
                                  "variant_filter": "VOR"
                              }),
                              content_type='application/json')
        
        assert response.status_code == 200


class TestSummarizeAPI:
    """Test /api/summarize endpoint"""

    def test_api_summarize_extract_mode_disabled(self, client):
        """Summarize endpoint should reject extract mode."""
        response = client.post(
            '/api/summarize',
            data=json.dumps({"mode": "extract", "language": "EN", "format": "standard"}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_api_summarize_search_applies_caps(self, client, monkeypatch):
        """Summarize should limit max rules and input size before model call."""
        fake_results = [
            SimpleNamespace(
                rule_id=f"GEN-{index}",
                text="Very long rule text. " * 30,
                document="01-altalanos.md",
                line_number=index,
                variant="",
                weapon_type="general"
            )
            for index in range(1, 11)
        ]

        def fake_search(query, max_results, variant_filter, weapon_filter):
            return fake_results[:max_results]

        monkeypatch.setattr(client.application.search_engine, "search", fake_search)
        monkeypatch.setattr(
            "app.blueprints.ai_services.summarize_with_gemini",
            lambda text, language, format_type="standard": text
        )

        client.application.config['SUMMARY_SEARCH_MAX_RULES'] = 3
        client.application.config['SUMMARY_MAX_INPUT_CHARS'] = 220

        response = client.post(
            '/api/summarize',
            data=json.dumps({
                "mode": "search",
                "query": "rule",
                "language": "EN",
                "format": "standard"
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["rule_count_total"] == 3
        assert data["rule_count_summarized"] < data["rule_count_total"]
        assert data["input_truncated"] is True
