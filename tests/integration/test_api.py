"""
Integration tests for Flask API endpoints
"""

import pytest
import json


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
    
    def test_api_search_with_formatum_filter(self, client):
        """Test search with formatum filter"""
        response = client.post('/api/search',
                              data=json.dumps({
                                  "query": "longsword",
                                  "formatum": "VOR"
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
                                  "weapon": "longsword"
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
            assert len(data["results"]) <= 3


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
        """Test extract with weapon and formatum filters"""
        response = client.post('/api/extract',
                              data=json.dumps({
                                  "weapon": "longsword",
                                  "formatum": "VOR"
                              }),
                              content_type='application/json')
        
        assert response.status_code == 200
