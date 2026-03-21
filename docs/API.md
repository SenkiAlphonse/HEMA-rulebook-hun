# REST API Reference

Complete documentation of all REST endpoints exposed by the HEMA Rulebook Q&A System.

## Overview

**Base URL:** `http://localhost:5000` (development) or `https://hema-rulebook-hun.onrender.com` (production)

**Authentication:** None (public API in current version)

**Rate Limiting:** None (implement in production via nginx or middleware)

**Response Format:** JSON (UTF-8 encoded)

**Error Format:** Standard HTTP status codes + JSON error messages

## Bilingual Ruleset Selection (`rules_lang`)

The API now supports **language-specific rule indexes**:

- `hun` → Hungarian ruleset (`data/search/rules_index_hun.json`)
- `eng` → English ruleset (`data/search/rules_index_eng.json`)

If omitted, endpoints default to `hun`.

### Endpoints supporting `rules_lang`

- `POST /api/search` (request body)
- `GET /api/stats` (query parameter)
- `POST /api/extract` (request body)
- `GET /api/rule/<rule_id>` (query parameter)
- `POST /api/summarize` (request body)

### Rulebook language parameter

- `GET /rulebook?lang=hun|eng`
- `GET /api/rulebook?lang=hun|eng`

### Example

```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"valid target","rules_lang":"eng"}'
```

---

## Search Endpoints

### 1. Basic Search

**Endpoint:** `POST /api/search`

Search for rules using natural language queries with automatic alias resolution.

**Request Body:**
```json
{
  "query": "longsword target areas",
  "rules_lang": "eng",
  "max_results": 10,
  "variant_filter": null,
  "weapon_filter": null
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✓ | — | Search query (Hungarian or English) |
| `rules_lang` | string | ✗ | `hun` | Ruleset language: `hun` or `eng` |
| `max_results` | integer | ✗ | 10 | Max results to return (1-100) |
| `variant_filter` | string | ✗ | null | Filter by variant: "VOR", "COMBAT", "AFTERBLOW" |
| `weapon_filter` | string | ✗ | null | Filter by weapon type: "longsword", "rapier", "armored" |

**Response (200 OK):**
```json
{
  "success": true,
  "query": "longsword target areas",
  "results": [
    {
      "rule_id": "GEN-1.2.3",
      "title": "Valid Target Areas",
      "content": "Valid target areas include head, torso, arms, and legs...",
      "section": "General Rules",
      "score": 0.95,
      "source_file": "03-altalanos.md",
      "weapon_type": "all",
      "anchor_id": "GEN-1.2.3"
    },
    {
      "rule_id": "HOSSZU-2.1.1",
      "title": "Longsword-Specific Target Restrictions",
      "content": "In longsword, the following additional restrictions apply...",
      "section": "Longsword Rules",
      "score": 0.87,
      "source_file": "05-hosszukard.md",
      "weapon_type": "longsword",
      "anchor_id": "HOSSZU-2.1.1"
    }
  ],
  "result_count": 2,
  "execution_time_ms": 3.2
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Query too short (minimum 3 characters)"
}
```

**Response (500 Internal Server Error):**
```json
{
  "success": false,
  "error": "Search engine initialization failed"
}
```

**Examples:**

*Hungarian query:*
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"hosszúkard szabályok","rules_lang":"hun"}'
```

*English query with custom limit:*
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"longsword rules","rules_lang":"eng","max_results":5}'
```

*Filter for specific variant:*
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"target areas","variant_filter":"VOR","max_results":20}'
```

---

### 2. Variant-Specific Search

**Endpoint:** `GET /api/rule/<rule_id>?rules_lang=hun|eng`

Get a specific rule by ID from the selected language index.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `rules_lang` | string | ✗ | `hun` | Ruleset language: `hun` or `eng` |

**Response (200 OK):**
```json
{
  "success": true,
  "rules_lang": "eng",
  "rule": {
    "rule_id": "GEN-1.1",
    "text": "The purpose of this event is...",
    "section": "General Provisions",
    "subsection": "Introduction",
    "document": "01-general.en.md",
    "weapon_type": "general",
    "variant": "",
    "anchor_id": "GEN-1"
  }
}
```

**Example:**
```bash
curl "http://localhost:5000/api/rule/GEN-1.1?rules_lang=eng"
```

---

### 3. Extract Rule by ID

**Endpoint:** `GET /api/stats?rules_lang=hun|eng`

Get statistics for the selected language ruleset.

**Response (200 OK):**
```json
{
  "rules_lang": "hun",
  "total_rules": 425,
  "vor_rules": 26,
  "combat_rules": 25,
  "afterblow_rules": 24,
  "longsword_rules": 173
}
```

**Example:**
```bash
curl "http://localhost:5000/api/stats?rules_lang=eng"
```

---

### 4. Resolve Alias

**Endpoint:** `POST /api/extract`

Download a markdown extract filtered by weapon + variant from selected language index.

**Request Body:**
```json
{
  "rules_lang": "eng",
  "weapon_filter": "longsword",
  "variant_filter": "VOR"
}
```

**Response (200 OK):**
- `text/markdown` attachment
- Filename format: `rulebook-extract_<rules_lang>_<weapon>_<variant>.md`

**Example:**
```bash
curl -X POST http://localhost:5000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"rules_lang":"hun","weapon_filter":"longsword","variant_filter":"VOR"}'
```

---

### 5. Fuzzy Match

**Endpoint:** `POST /api/summarize`

Summarize top matching rules from a selected ruleset language.

**Request Body:**
```json
{
  "mode": "search",
  "query": "valid targets",
  "rules_lang": "eng",
  "language": "EN",
  "format": "standard",
  "weapon_filter": null,
  "variant_filter": null
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "format": "standard",
  "language": "EN",
  "rules_lang": "eng",
  "summary": "...",
  "rule_count_total": 20,
  "rule_count_summarized": 12,
  "input_truncated": true
}
```

---

## Rulebook Endpoints

### 6. Get Rulebook Index

**Endpoint:** `GET /rulebook?lang=hun|eng`

Open pre-rendered full rulebook HTML in browser.

**Examples:**
```bash
curl "http://localhost:5000/rulebook?lang=hun"
curl "http://localhost:5000/rulebook?lang=eng"
```

---

### 7. Get Chapter Rules

**Endpoint:** `GET /api/rulebook?lang=hun|eng`

Return all indexed rules from the selected language index.

**Response (200 OK):**
```json
{
  "success": true,
  "lang": "hun",
  "rules": [
    {
      "rule_id": "GEN-1.1",
      "text": "..."
    }
  ],
  "total": 425
}
```

**Example:**
```bash
curl "http://localhost:5000/api/rulebook?lang=eng"
```

---

### 8. Legacy Endpoints Removed

These endpoints were part of an earlier draft and are **not implemented** in the current backend:

- `POST /api/search/variant`
- `POST /api/search/alias`
- `POST /api/search/fuzzy`
- `GET /api/rulebook/index`
- `GET /api/rulebook/chapter/<chapter_id>`
- `GET /api/rulebook/chapters`
- `POST /api/ai/explain`

---

## Error Handling

### Common HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | Search returned results |
| 400 | Bad Request | Invalid query format, missing required parameter |
| 404 | Not Found | Rule ID doesn't exist |
| 500 | Server Error | Search engine initialization failed |
| 503 | Service Unavailable | Database connection lost |

### Error Response Format

All error responses follow this format:
```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "ERROR_CODE_CONSTANT",
  "details": {
    "field": "query",
    "reason": "Query too short"
  }
}
```

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Query too short" | Query < 3 characters | Provide longer, more specific query |
| "Query too long" | Query > 500 characters | Break into multiple queries |
| "Invalid max_results" | max_results outside 1-100 | Use value between 1 and 100 |
| "Invalid variant_filter" | Unknown variant specified | Use "VOR", "COMBAT", "AFTERBLOW", or null |
| "Rate limit exceeded" | Too many requests | Wait 1 minute before retrying |
| "Search index not initialized" | System startup issue | Retry after 30 seconds |
| "Rule not found" | Invalid rule ID | Check rule ID format (e.g., "GEN-1.2.3") |

---

## Rate Limiting

**Current Status:** Not enabled in development

**Recommended Production Limits:**
- 100 requests per minute per IP
- 1000 requests per day per IP
- 10 concurrent connections per IP

**Implementation:** Use nginx reverse proxy or Flask-Limiter middleware

**Example nginx configuration:**
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;

location /api {
    limit_req zone=api_limit burst=20;
    proxy_pass http://localhost:5000;
}
```

---

## Authentication & Authorization

**Current Status:** None (public API)

**For Production:**
- Implement API key authentication
- Add rate limiting per key
- Optional: JWT token-based access
- Consider: IP whitelisting for internal services

---

## Use Cases & Examples

### Use Case 1: Beginner Fencer Learns Rules

```bash
# User asks: "What are the rules for longsword matches?"
curl -X POST http://localhost:5000/api/search \
  -d '{"query":"longsword match rules","rules_lang":"eng","max_results":5}'

# Response includes top 5 relevant rules from 05-hosszukard.md
```

### Use Case 2: Judge Needs Quick Rule Lookup

```bash
# Judge asks: "What's the ruling on striking the back of the head?"
curl -X POST http://localhost:5000/api/search \
  -d '{"query":"back of head strike","max_results":10}'

# Response includes applicable target area rules
```

### Use Case 3: Mobile App Integration

```bash
# App fetches full rule list for offline cache (English)
curl "http://localhost:5000/api/rulebook?lang=eng"

# User searches locally using /api/search endpoint
# App translates user query to JSON and posts to /api/search
```

### Use Case 4: VOR vs COMBAT Comparison

```bash
# Coach compares variant behavior using filters in one endpoint
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"distance requirements","rules_lang":"hun","variant_filter":"VOR"}'

# Repeat with variant_filter="COMBAT" to compare
```

### Use Case 5: Glossary Lookup

```bash
# Student asks: "What does 'szúrás' mean?" (alias-aware search)
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"szúrás","rules_lang":"hun"}'
```

### Use Case 6: AI-Powered Summary

```bash
# Beginner asks for search-based summary
curl -X POST http://localhost:5000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"mode":"search","query":"target areas","rules_lang":"eng","language":"EN","format":"standard"}'
```

---

## Response Time Expectations

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| `/api/search` | 2-5 ms | Hash-based index lookup |
| `/api/stats` | <1 ms | Preloaded in-memory counters |
| `/api/rule/<id>` | <1 ms | Direct rule lookup |
| `/api/extract` | 2-8 ms | Filter + markdown export |
| `/api/summarize` | 1-3 seconds | LLM inference time |
| `/api/rulebook` | 2-10 ms | Returns full index rules array |

**Note:** Times are for production deployment with optimizations. Development mode may be 2-3x slower.

---

## Testing Endpoints

### Quick Test Script

```bash
#!/bin/bash
BASE_URL="http://localhost:5000"

# Test 1: Search
echo "Testing search..."
curl -X POST $BASE_URL/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"longsword"}'

# Test 2: Extract
echo -e "\n\nTesting extract..."
curl -X POST $BASE_URL/api/extract \
  -H "Content-Type: application/json" \
  -d '{"rules_lang":"hun","weapon_filter":"longsword","variant_filter":"VOR"}'

# Test 3: Stats (English ruleset)
echo -e "\n\nTesting stats..."
curl "$BASE_URL/api/stats?rules_lang=eng"

# Test 4: Rule lookup
echo -e "\n\nTesting rule lookup..."
curl "$BASE_URL/api/rule/GEN-1.1?rules_lang=hun"

# Test 5: Summarize
echo -e "\n\nTesting summarize..."
curl -X POST $BASE_URL/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"mode":"search","query":"target area","rules_lang":"eng","language":"EN","format":"standard"}'
```

---

## Changelog

### v2.0 (Current - February 2026)
- Added bilingual ruleset indexing and `rules_lang` parameter support
- Added language-specific pre-rendered rulebooks (`/rulebook?lang=hun|eng`)
- Added search-engine selection by index language (`hun`/`eng`)

### v1.0 (Original)
- Basic search endpoint
- Rule extract export

---

**Last Updated:** March 2026  
**Maintainer:** AI Agent, HEMA Development Team  
**Status:** Production Ready

For implementation questions, see [ARCHITECTURE.md](ARCHITECTURE.md) → API Layer section.
