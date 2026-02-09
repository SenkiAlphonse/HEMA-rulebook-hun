# REST API Reference

Complete documentation of all REST endpoints exposed by the HEMA Rulebook Q&A System.

## Overview

**Base URL:** `http://localhost:5000` (development) or `https://hema-rulebook-hun.onrender.com` (production)

**Authentication:** None (public API in current version)

**Rate Limiting:** None (implement in production via nginx or middleware)

**Response Format:** JSON (UTF-8 encoded)

**Error Format:** Standard HTTP status codes + JSON error messages

---

## Search Endpoints

### 1. Basic Search

**Endpoint:** `POST /api/search`

Search for rules using natural language queries with automatic alias resolution.

**Request Body:**
```json
{
  "query": "longsword target areas",
  "language": "en",
  "limit": 10,
  "threshold": 0.5
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✓ | — | Search query (Hungarian or English) |
| `language` | string | ✗ | "auto" | Force language: "hu", "en", or "auto" |
| `limit` | integer | ✗ | 10 | Max results to return (1-50) |
| `threshold` | float | ✗ | 0.5 | Relevance threshold (0.0-1.0) |

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
  -d '{"query":"hosszúkard szabályok","language":"hu"}'
```

*English query with custom limit:*
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"longsword rules","limit":5}'
```

*Low threshold for more results:*
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"target","threshold":0.3,"limit":20}'
```

---

### 2. Variant-Specific Search

**Endpoint:** `POST /api/search/variant`

Search for rules specific to longsword variants (VOR, COMBAT, AFTERBLOW).

**Request Body:**
```json
{
  "query": "distance rules",
  "variant": "VOR",
  "limit": 10
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✓ | — | Search query |
| `variant` | string | ✓ | — | Longsword variant: "VOR", "COMBAT", or "AFTERBLOW" |
| `limit` | integer | ✗ | 10 | Max results |

**Response (200 OK):**
```json
{
  "success": true,
  "query": "distance rules",
  "variant": "VOR",
  "results": [
    {
      "rule_id": "VOR-3.2.1",
      "title": "Minimum Distance in VOR",
      "content": "In VOR variant, fencers must maintain minimum distance of 1.5 meters...",
      "section": "VOR-Specific Rules",
      "score": 0.96,
      "source_file": "05.a-hosszukard-VOR.md",
      "variant": "VOR"
    }
  ],
  "result_count": 1,
  "execution_time_ms": 2.1
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Invalid variant. Must be one of: VOR, COMBAT, AFTERBLOW"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/search/variant \
  -H "Content-Type: application/json" \
  -d '{"query":"afterblow regulations","variant":"AFTERBLOW"}'
```

---

### 3. Extract Rule by ID

**Endpoint:** `POST /api/extract`

Get a specific rule by its rule ID (e.g., "GEN-1.2.3").

**Request Body:**
```json
{
  "rule_id": "GEN-1.2.3"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `rule_id` | string | ✓ | Rule identifier (e.g., "GEN-1.2.3", "HOSSZU-2.1") |

**Response (200 OK):**
```json
{
  "success": true,
  "rule": {
    "rule_id": "GEN-1.2.3",
    "title": "Valid Target Areas",
    "content": "Valid target areas include head, torso, arms, and legs. Strikes to the spine are prohibited.",
    "section": "General Rules",
    "source_file": "03-altalanos.md",
    "anchor_id": "GEN-1.2.3",
    "weapon_type": "all",
    "full_hierarchy": "01. General Rules > 1.2 Combat Rules > 1.2.3 Target Areas"
  }
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Rule 'GEN-1.2.99' not found in index"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"rule_id":"GEN-1.2.3"}'
```

---

### 4. Resolve Alias

**Endpoint:** `POST /api/search/alias`

Resolve a Hungarian or English term to its mapped rules and aliases.

**Request Body:**
```json
{
  "term": "szúrás",
  "language": "hu"
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `term` | string | ✓ | — | Term to resolve (Hungarian or English) |
| `language` | string | ✗ | "auto" | Force language: "hu" or "en" |

**Response (200 OK):**
```json
{
  "success": true,
  "term": "szúrás",
  "language": "hu",
  "primary_meaning": "thrust/lunge",
  "aliases": ["thrust", "lunge", "szúrások (plural)"],
  "related_rules": [
    {
      "rule_id": "GEN-2.1.5",
      "title": "Thrust Mechanics",
      "score": 0.98
    },
    {
      "rule_id": "HOSSZU-1.3.2",
      "title": "Valid Thrust Targets in Longsword",
      "score": 0.95
    }
  ],
  "result_count": 2
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Term 'unknown_word' not found in alias database"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/search/alias \
  -H "Content-Type: application/json" \
  -d '{"term":"vágás"}'
```

---

### 5. Fuzzy Match

**Endpoint:** `POST /api/search/fuzzy`

Find rules using fuzzy/approximate string matching (tolerance for typos).

**Request Body:**
```json
{
  "query": "longsword taget",
  "tolerance": 0.8
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✓ | — | Query with potential typos |
| `tolerance` | float | ✗ | 0.8 | Match tolerance (0.0-1.0, higher = stricter) |
| `limit` | integer | ✗ | 10 | Max results |

**Response (200 OK):**
```json
{
  "success": true,
  "query": "longsword taget",
  "corrected_query": "longsword target",
  "results": [
    {
      "rule_id": "GEN-1.2.3",
      "title": "Valid Target Areas",
      "content": "...",
      "fuzzy_match_score": 0.92
    }
  ],
  "result_count": 1
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/search/fuzzy \
  -H "Content-Type: application/json" \
  -d '{"query":"afterblow regelz","tolerance":0.75}'
```

---

## Rulebook Endpoints

### 6. Get Rulebook Index

**Endpoint:** `GET /api/rulebook/index`

Get the complete rulebook structure with all chapters and sections.

**Query Parameters:** None

**Response (200 OK):**
```json
{
  "success": true,
  "chapters": [
    {
      "id": "01",
      "title": "Bevezetés",
      "filename": "01-altalanos.md",
      "rule_count": 15
    },
    {
      "id": "03",
      "title": "Felszerelés",
      "filename": "03-felszereles.md",
      "rule_count": 22
    },
    {
      "id": "04",
      "title": "Általános szabályok",
      "filename": "04-altalanos.md",
      "rule_count": 45
    }
  ],
  "total_rules": 487,
  "total_chapters": 9,
  "last_updated": "2026-02-09T14:32:00Z"
}
```

**Example:**
```bash
curl http://localhost:5000/api/rulebook/index
```

---

### 7. Get Chapter Rules

**Endpoint:** `GET /api/rulebook/chapter/<chapter_id>`

Get all rules in a specific chapter.

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `chapter_id` | string | Chapter ID (e.g., "03", "05") |

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `detailed` | boolean | true | Include full rule content (false = summaries only) |

**Response (200 OK):**
```json
{
  "success": true,
  "chapter_id": "04",
  "chapter_title": "Általános szabályok",
  "filename": "04-altalanos.md",
  "rules": [
    {
      "rule_id": "GEN-1.1",
      "title": "Match Structure",
      "content": "A match consists of three phases...",
      "section": "1. Match Phases"
    },
    {
      "rule_id": "GEN-1.2",
      "title": "Round Duration",
      "content": "Each round lasts 3 minutes...",
      "section": "1. Match Phases"
    }
  ],
  "rule_count": 45
}
```

**Example:**
```bash
curl "http://localhost:5000/api/rulebook/chapter/04?detailed=true"
```

---

### 8. Get Chapter Metadata

**Endpoint:** `GET /api/rulebook/chapters`

Get metadata for all chapters without full rule content.

**Query Parameters:** None

**Response (200 OK):**
```json
{
  "success": true,
  "chapters": [
    {
      "id": "01",
      "title": "Bevezetés",
      "filename": "01-altalanos.md",
      "rule_count": 15,
      "weapon_type": "all"
    },
    {
      "id": "05",
      "title": "Hosszúkard",
      "filename": "05-hosszukard.md",
      "rule_count": 78,
      "weapon_type": "longsword"
    }
  ],
  "total_chapters": 9,
  "total_rules": 487
}
```

**Example:**
```bash
curl http://localhost:5000/api/rulebook/chapters
```

---

## AI Service Endpoints

### 9. AI-Enhanced Rule Explanation

**Endpoint:** `POST /api/ai/explain`

Get an AI-generated explanation of a rule with examples and clarifications.

**Request Body:**
```json
{
  "rule_id": "GEN-1.2.3",
  "context": "I'm new to HEMA and need simple explanation"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `rule_id` | string | ✓ | Rule to explain |
| `context` | string | ✗ | Additional context for AI (e.g., experience level) |
| `language` | string | ✗ | Output language: "hu" or "en" |

**Response (200 OK):**
```json
{
  "success": true,
  "rule_id": "GEN-1.2.3",
  "original_rule": "Valid target areas include head, torso, arms, and legs...",
  "ai_explanation": "Think of valid target areas as the parts of your opponent's body where you can score points. This includes the head (any part above the shoulders), torso (front and back), arms (from shoulder to wrist), and legs (from hip to ankle). You cannot strike the spine, groin, or joints as these are protected areas.",
  "examples": [
    "A thrust to the chest = valid target",
    "A slash to the forearm = valid target",
    "A strike to the back of the head = valid target",
    "A strike to the spine = INVALID (protected)"
  ],
  "generated_at": "2026-02-09T14:32:00Z"
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "error": "Rule 'UNKNOWN-1.1' not found"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/ai/explain \
  -H "Content-Type: application/json" \
  -d '{"rule_id":"GEN-1.2.3","context":"beginner fencer"}'
```

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
| "Invalid threshold" | Threshold outside 0.0-1.0 | Use value between 0.0 and 1.0 |
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
  -d '{"query":"longsword match rules","limit":5}'

# Response includes top 5 relevant rules from 05-hosszukard.md
```

### Use Case 2: Judge Needs Quick Rule Lookup

```bash
# Judge asks: "What's the ruling on striking the back of the head?"
curl -X POST http://localhost:5000/api/search \
  -d '{"query":"back of head strike","threshold":0.7}'

# Response includes applicable target area rules
```

### Use Case 3: Mobile App Integration

```bash
# App fetches all chapters for offline cache
curl http://localhost:5000/api/rulebook/index

# User searches locally using /api/search endpoint
# App translates user query to JSON and posts to /api/search
```

### Use Case 4: VOR vs COMBAT Comparison

```bash
# Coach asks: "What's different about VOR distance rules?"
curl -X POST http://localhost:5000/api/search/variant \
  -d '{"query":"distance requirements","variant":"VOR"}'

# Gets VOR-specific rules, then repeat with variant=COMBAT to compare
```

### Use Case 5: Glossary Lookup

```bash
# Student asks: "What does 'szúrás' mean?"
curl -X POST http://localhost:5000/api/search/alias \
  -d '{"term":"szúrás","language":"hu"}'

# Returns definition + related rules using this term
```

### Use Case 6: AI-Powered Learning

```bash
# Beginner asks for explanation
curl -X POST http://localhost:5000/api/ai/explain \
  -d '{"rule_id":"GEN-1.2.3","context":"I am a beginner"}'

# Gets AI explanation with examples and clarifications
```

---

## Response Time Expectations

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| `/api/search` | 2-5 ms | Hash-based index lookup |
| `/api/extract` | <1 ms | Direct index access |
| `/api/search/variant` | 3-7 ms | Filters + scoring |
| `/api/search/alias` | 1-3 ms | Hash-based alias lookup |
| `/api/ai/explain` | 1-3 seconds | LLM inference time |
| `/api/rulebook/index` | <1 ms | Cached metadata |
| `/api/rulebook/chapter/*` | 5-10 ms | Full chapter retrieval |

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
  -d '{"rule_id":"GEN-1.1.1"}'

# Test 3: Index
echo -e "\n\nTesting rulebook index..."
curl $BASE_URL/api/rulebook/index

# Test 4: Variant search
echo -e "\n\nTesting variant search..."
curl -X POST $BASE_URL/api/search/variant \
  -H "Content-Type: application/json" \
  -d '{"query":"VOR rules","variant":"VOR"}'
```

---

## Changelog

### v2.0 (Current - February 2026)
- Added AI-enhanced explanation endpoint (`/api/ai/explain`)
- Improved error messages with error codes
- Added fuzzy matching endpoint
- Variant search endpoint added
- Full type hints in responses

### v1.0 (Original)
- Basic search endpoint
- Extract rule endpoint
- Rulebook index endpoints
- Alias resolution

---

**Last Updated:** February 2026  
**Maintainer:** AI Agent, HEMA Development Team  
**Status:** Production Ready

For implementation questions, see [ARCHITECTURE.md](ARCHITECTURE.md) → API Layer section.
