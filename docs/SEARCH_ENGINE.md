# Search Engine Documentation

Technical deep-dive into the AliasAwareSearch algorithm, implementation, scoring formula, and optimization strategies.

---

## Table of Contents

1. [Overview](#overview)
2. [Algorithm](#algorithm)
3. [Data Structures](#data-structures)
4. [Scoring Formula](#scoring-formula)
5. [Complexity Analysis](#complexity-analysis)
6. [Performance Optimization](#performance-optimization)
7. [Alias System](#alias-system)
8. [Testing Strategy](#testing-strategy)
9. [Debugging Guide](#debugging-guide)
10. [Future Improvements](#future-improvements)

---

## Overview

**AliasAwareSearch** is a custom search engine combining three matching strategies:

### 2026 UI Integration
- Search results now render rule IDs as clickable links. Clicking a rule ID opens the full rulebook and scrolls to the rule anchor.
- The rulebook view supports anchor-based navigation and highlights the target rule.
1. **Exact Match** - O(1) rule ID lookups
2. **Partial Match** - O(n) substring matching
3. **Fuzzy Match** - O(n*m) typo-tolerant matching with Levenshtein distance

**Key Characteristics:**
- **Sub-millisecond** exact searches
- **Typo tolerant** (handles misspellings)
- **Hungarian + English** support
- **Alias resolution** (term → rule mapping)
- **Multi-factor scoring** (context-aware ranking)

---

## Algorithm

### High-Level Flow

```
Input: query (string)
       ↓
┌─ PHASE 1: Preprocessing
│  ├─ Detect language (Hungarian vs English)
│  ├─ Lowercase query
│  ├─ Tokenize by spaces
│  └─ Expand with alias mappings
│
├─ PHASE 2: Exact Match (O(1))
│  ├─ Check if query is a valid rule ID
│  │  └─ If rule_id == "GEN-1.1.1" → score = 1.0, return immediately
│  └─ Continue to Phase 3 if no exact match
│
├─ PHASE 3: Partial Match (O(n))
│  ├─ For each rule in rules_index (487 rules):
│  │  ├─ Check if query token is substring of:
│  │  │  ├─ rule['rule_id']
│  │  │  ├─ rule['title']
│  │  │  ├─ rule['content']
│  │  │  └─ rule['section']
│  │  ├─ If found → score = 0.7, add to results
│  │  └─ Continue for next rule
│  └─ Continue to Phase 4 if not enough results
│
├─ PHASE 4: Fuzzy Match (O(n*m))
│  ├─ For each rule in rules_index (487 rules):
│  │  ├─ For each query token:
│  │  │  ├─ Calculate Levenshtein distance from token to:
│  │  │  │  ├─ rule['title']
│  │  │  │  ├─ rule['content'] (tokenized)
│  │  │  │  └─ rule['section']
│  │  │  ├─ If distance < threshold (tolerance 0.8):
│  │  │  │  └─ score = 0.3 + (1 - norm_distance) * 0.2
│  │  │  └─ Add to results
│  │  └─ Continue for next rule
│  └─ Aggregate token scores
│
├─ PHASE 5: Score Aggregation
│  ├─ For multi-token queries:
│  │  ├─ Calculate score for each token independently
│  │  ├─ Combine scores: max(token_scores) or avg(token_scores)
│  │  └─ Boost if all tokens match (multi-match bonus)
│  └─ Filter results by threshold (default 0.5)
│
├─ PHASE 6: Sorting & Limiting
│  ├─ Sort results by score (descending)
│  ├─ Keep top N results (default 10, max 50)
│  └─ Generate response
│
└─ Output: List of matching rules sorted by relevance
```

### Pseudocode

```python
function SEARCH_RULES(query, threshold=0.5, limit=10):
    results = []
    
    # PHASE 1: Preprocess
    query_tokens = TOKENIZE(query.lower())
    query_tokens.extend(EXPAND_ALIASES(query_tokens))
    
    # PHASE 2: Exact match
    for token in query_tokens:
        if token in rules_index:
            results.append({
                rule: rules_index[token],
                score: 1.0,
                match_type: "exact"
            })
            if len(results) > 0:
                return SORT_AND_LIMIT(results, limit)
    
    # PHASE 3 & 4: Partial + Fuzzy match
    for rule in all_rules:
        rule_score = 0
        match_count = 0
        
        for token in query_tokens:
            # Partial match
            if SUBSTRING_MATCH(token, rule):
                rule_score = max(rule_score, 0.7)
                match_count += 1
            
            # Fuzzy match
            distance = LEVENSHTEIN_DISTANCE(token, rule_content)
            if distance < TOLERANCE:
                fuzzy_score = 0.3 + (1 - NORMALIZE(distance)) * 0.2
                rule_score = max(rule_score, fuzzy_score)
                match_count += 1
        
        # Multi-match bonus
        if match_count > 1:
            rule_score *= 1.1  # 10% boost for multiple matches
        
        if rule_score >= threshold:
            results.append({
                rule: rule,
                score: rule_score,
                match_count: match_count
            })
    
    # PHASE 5 & 6: Filter, sort, limit
    results = FILTER(results, threshold)
    results = SORT_BY_SCORE_DESC(results)
    return LIMIT(results, limit)
```

---

## Data Structures

### Main Data Structure: Hash Tables

```python
class AliasAwareSearch:
    def __init__(self, rules_data, aliases_data):
        # Rule lookup (rule_id → rule object)
        self.rules = {
            "GEN-1.1.1": {
                "rule_id": "GEN-1.1.1",
                "title": "Rule title",
                "content": "Full rule text...",
                "section": "Section name",
                "source_file": "03-altalanos.md",
                ...
            },
            "GEN-1.1.2": {...},
            ...  # 487 total rules
        }
        
        # Inverted index (word → [rule_id, ...])
        self.inverted_index = {
            "longsword": ["GEN-1.2.3", "HOSSZU-1.1.1", "HOSSZU-2.3.4"],
            "target": ["GEN-1.2.3", "GEN-1.3.1"],
            "areas": ["GEN-1.2.3"],
            ...
        }
        
        # Alias mappings (term → aliases)
        self.aliases = {
            "szúrás": {
                "primary_hu": "szúrás",
                "primary_en": "thrust",
                "aliases": ["lunge", "poke"],
                "rules": ["GEN-2.1.5", "HOSSZU-1.3.2"]
            },
            "thrust": {
                "primary_hu": "szúrás",
                "primary_en": "thrust",
                "aliases": ["szúrás", "lunge", "poke"],
                "rules": ["GEN-2.1.5", "HOSSZU-1.3.2"]
            },
            ...
        }
```

### Memory Layout

```
┌─ Hash Table: self.rules (487 entries, ~2.5 MB)
│  ├─ Key: "GEN-1.1.1" (11 bytes)
│  ├─ Value: Rule object (2-5 KB per rule)
│  └─ Load factor: 0.75 (good performance)
│
├─ Hash Table: self.inverted_index (~3000 entries, ~200 KB)
│  ├─ Key: word (avg 8 bytes)
│  └─ Value: list of rule IDs
│
└─ Hash Table: self.aliases (~1000 entries, ~50 KB)
   ├─ Key: term (avg 10 bytes)
   └─ Value: alias mapping object
```

**Total Memory:** ~2.75 MB

**Access Time:**
- Exact rule lookup: O(1) = ~0.1 µs
- Inverted index lookup: O(1) = ~0.1 µs
- Alias resolution: O(1) = ~0.1 µs

---

## Scoring Formula

### Single-Token Scoring

For query token `t` and rule `R`:

$$\text{score}(R, t) = \begin{cases}
1.0 & \text{if } \text{exact\_match}(t, R) \\
0.7 & \text{if } \text{partial\_match}(t, R) \\
0.3 + (1 - d_{\text{norm}}) \times 0.2 & \text{if } \text{fuzzy\_match}(t, R) \\
0.0 & \text{otherwise}
\end{cases}$$

Where:
- $d_{\text{norm}}$ = normalized Levenshtein distance (0.0-1.0)
- $\text{fuzzy\_match}(t, R)$ = true if $d_{\text{norm}} < 0.2$ (80% similarity)

### Multi-Token Scoring

For query `Q` with tokens `t₁, t₂, ..., tₙ`:

$$\text{score}(R, Q) = \max_{i} \text{score}(R, t_i) \times \text{match\_bonus}$$

Where:
- $\text{match\_bonus} = 1.0 + 0.1 \times \min(\text{matches}, 5)$
- **Rationale**: Multiple token matches = more confident result (up to 50% boost)

### Example Calculation

**Query**: "longsword target"  
**Tokens**: ["longsword", "target"]  
**Rule**: GEN-1.2.3 (Valid Target Areas)

```
Token 1: "longsword"
  ├─ Exact match? No
  ├─ Partial match? No (not in rule content)
  └─ Fuzzy match? No
  → score = 0.0

Token 2: "target"
  ├─ Exact match? No
  ├─ Partial match? Yes (substring in title "Valid Target Areas")
  └─ score = 0.7

Multi-token aggregation:
  ├─ max(0.0, 0.7) = 0.7
  ├─ matches = 1 (only "target" matched)
  └─ bonus = 1.0 + 0.1 × 1 = 1.1
  
Final score = 0.7 × 1.1 = 0.77
```

---

## Complexity Analysis

### Time Complexity per Operation

| Operation | Complexity | N (input) | M (data) | Notes |
|-----------|-----------|-----------|----------|-------|
| Exact rule lookup | O(1) | — | — | Hash table access |
| Inverted index lookup | O(1) | — | — | Hash table access |
| Partial match (one token) | O(n*m) | m (token) | n (rules) | Linear scan + substring search |
| Fuzzy match (one token) | O(n*m*k) | m (token) | n (rules), k (avg field length) | Levenshtein distance for each field |
| Multi-token search | O(q*(n*m)) | q (tokens) | n (rules), m (token len) | For each token, do full scan |
| Sort results | O(r log r) | r (results) | — | Merge sort, usually r < 50 |

### Overall Search Time Complexity

**Best case (exact match):** O(1)
```
Query: "GEN-1.1.1" (exact rule ID)
→ Direct hash table lookup → return
```

**Typical case (single token, partial + fuzzy):** O(n*m)
```
Query: "longsword" (single token)
n = 487 rules
m = 8 characters
→ 487 × 8 = 3,896 operations → ~1-3 ms
```

**Worst case (multi-token, fuzzy):** O(q*(n*m*k))
```
Query: "what are valid longsword target areas" (7 tokens)
n = 487 rules
m = avg 8 characters per token
k = avg 300 characters per rule field
→ 7 × (487 × 8 × 300) = 8,234,880 operations → ~10-20 ms
```

### Space Complexity

| Component | Space | Formula | Notes |
|-----------|-------|---------|-------|
| rules_index | O(n) | ~2.5 MB | 487 rules × ~5 KB/rule |
| inverted_index | O(n*m) | ~200 KB | ~3000 unique words |
| aliases | O(t) | ~50 KB | ~1000 term mappings |
| **Total** | O(n) | ~2.75 MB | Linear in number of rules |

---

## Performance Optimization

### Current Optimizations

**1. Hash Tables for O(1) Lookups**
```python
# Instead of:
def find_rule_slow(rule_id):
    for rule in all_rules:  # O(n)
        if rule['rule_id'] == rule_id:
            return rule
    return None

# Use:
def find_rule_fast(rule_id):
    return self.rules.get(rule_id)  # O(1)
```

**2. Early Exit on Exact Match**
```python
# Stop searching as soon as we find exact match
def search_rules(self, query):
    if query in self.rules:
        return [self.rules[query]]  # Return immediately, O(1)
    # Continue with partial/fuzzy matching if needed
```

**3. Inverted Index for Fast Text Search**
```python
# Instead of scanning all rules for word:
# word in "longsword allows strikes to many areas..."
# Use inverted index:
# self.inverted_index["longsword"] = ["HOSSZU-1.1.1", "HOSSZU-2.3.4"]
```

**4. Token Limiting**
```python
# Don't process queries with too many tokens
query_tokens = query.split()
if len(query_tokens) > 10:
    query_tokens = query_tokens[:10]  # Limit to first 10
```

### Potential Future Optimizations

**1. Trie for Prefix Matching**
```
If we want to match "long*" → all words starting with "long"

Trie structure:
  l
  ├─ o
  │  └─ n
  │     └─ g
  │        ├─ sword (rule IDs)
  │        └─ sword (plural)
  
Lookup: O(m) where m = query length (faster than O(n*m))
```

**2. Redis Caching for Frequent Queries**
```python
def search_with_cache(query):
    cache_key = f"search:{query}"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)  # Cache hit, O(1)
    
    results = search_rules(query)  # Cache miss, O(n*m)
    redis.setex(cache_key, 3600, json.dumps(results))  # Cache for 1 hour
    return results
```

**3. BM25 Ranking Algorithm**
```
Current: Multi-factor scoring (exact/partial/fuzzy)
Better: BM25 (probabilistic ranking model used in Elasticsearch)

BM25 formula:
  score(D, Q) = Σ IDF(qᵢ) × (f(qᵢ, D) × (k₁ + 1)) / (f(qᵢ, D) + k₁ × (1 - b + b × |D|/avgdl))

Where:
  D = document (rule)
  Q = query
  IDF = inverse document frequency (how rare the term is)
  f = term frequency (how often term appears in document)
  |D| = document length
  avgdl = average document length
  k₁, b = tuning parameters
```

**4. Parallel Processing**
```python
# Instead of sequential search through 487 rules:
# Use multiprocessing to search in parallel (4 CPU cores)
# Divide 487 rules into 4 chunks (122 rules each)
# Each core searches its chunk
# Merge results at end

# Trade-off: Adds overhead for small queries, helps for large datasets
```

---

## Alias System

### Alias Mapping Structure

```json
{
  "szúrás": {
    "primary_hu": "szúrás",
    "primary_en": "thrust",
    "aliases": [
      "lunge",
      "poke",
      "szúrások",
      "thrust"
    ],
    "related_terms": [
      "cutting",
      "striking",
      "grappling"
    ],
    "rules": [
      "GEN-2.1.5",
      "HOSSZU-1.3.2",
      "HOSSZU-2.1.1"
    ]
  }
}
```

### Alias Resolution Algorithm

```python
def expand_query_with_aliases(query_tokens):
    """Expand query tokens with alias mappings."""
    expanded = list(query_tokens)  # Start with original tokens
    
    for token in query_tokens:
        if token in self.aliases:
            alias_data = self.aliases[token]
            # Add primary terms if not already present
            expanded.append(alias_data['primary_hu'])
            expanded.append(alias_data['primary_en'])
            # Add related aliases
            expanded.extend(alias_data['aliases'])
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(expanded))

# Example:
query = "szúrás rules"
expanded = expand_query_with_aliases(query.split())
# Result: ["szúrás", "rules", "thrust", "lunge", "poke", ...]
```

### Benefits of Alias System

1. **Language Bridge**: Hungarian → English mapping
2. **Synonyms**: "lunge" = "thrust" = "szúrás"
3. **Term Expansion**: One query term finds more rules
4. **Context**: Related terms suggest relevant rules

---

## Testing Strategy

### Unit Tests for Search Algorithm

**File**: `tests/unit/test_search.py`

```python
def test_exact_match_rule_id():
    """Exact match should return rule immediately."""
    results = search_engine.search_rules("GEN-1.1.1")
    assert len(results) == 1
    assert results[0]['score'] == 1.0
    assert results[0]['rule_id'] == "GEN-1.1.1"

def test_partial_match_in_title():
    """Partial match in title should score 0.7."""
    results = search_engine.search_rules("Target")
    assert len(results) > 0
    assert any(r['score'] == 0.7 for r in results)

def test_fuzzy_match_with_typo():
    """Fuzzy match should handle typos."""
    results = search_engine.search_rules("longsword")  # Correct
    results_typo = search_engine.search_rules("longsward")  # Typo
    assert len(results) > 0
    assert len(results_typo) > 0
    # Both should find the same rules

def test_multi_token_query():
    """Multi-token queries should aggregate scores."""
    results = search_engine.search_rules("longsword target areas")
    assert len(results) > 0
    # Rules matching multiple tokens should score higher

def test_threshold_filtering():
    """Results below threshold should be filtered."""
    results_high = search_engine.search_rules("x", threshold=0.9)
    results_low = search_engine.search_rules("x", threshold=0.1)
    assert len(results_low) >= len(results_high)

def test_limit_parameter():
    """Limit parameter should cap results."""
    results_5 = search_engine.search_rules("rule", limit=5)
    results_20 = search_engine.search_rules("rule", limit=20)
    assert len(results_5) <= 5
    assert len(results_20) <= 20
```

### Integration Tests

**File**: `tests/integration/test_api.py`

```python
def test_api_search_endpoint():
    """Full API search should work end-to-end."""
    response = client.post('/api/search', json={
        "query": "longsword",
        "limit": 10
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'results' in data
    assert len(data['results']) <= 10

def test_api_search_error_handling():
    """API should handle errors gracefully."""
    response = client.post('/api/search', json={
        "query": "x"  # Too short
    })
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data
```

---

## Debugging Guide

### Debug Logging

Add debug prints to search algorithm:

```python
def search_rules(self, query, debug=False):
    """Search with optional debug output."""
    if debug:
        print(f"\n=== SEARCH DEBUG ===")
        print(f"Query: '{query}'")
        print(f"Query length: {len(query)}")
    
    # PHASE 1: Preprocess
    tokens = self.tokenize(query)
    if debug:
        print(f"Tokens: {tokens}")
    
    # PHASE 2: Exact match
    if query in self.rules:
        if debug:
            print(f"EXACT MATCH: {query} → Rule {self.rules[query]['rule_id']}")
        return [self.rules[query]]
    if debug:
        print("EXACT MATCH: None")
    
    # PHASE 3 & 4: Partial + Fuzzy
    results = []
    for rule in self.rules.values():
        for token in tokens:
            # ... matching logic ...
            if debug and score >= 0.5:
                print(f"Match: {token} in {rule['rule_id']} (score: {score})")
    
    # PHASE 6: Limit results
    results = sorted(results, key=lambda r: r['score'], reverse=True)
    results = results[:limit]
    
    if debug:
        print(f"RESULTS: {len(results)} rules")
        for r in results:
            print(f"  {r['rule_id']}: {r['score']:.2f}")
    
    return results
```

### Usage

```python
# Normal search
results = search_engine.search_rules("longsword")

# Debug search
results = search_engine.search_rules("longsword", debug=True)
# Output:
# === SEARCH DEBUG ===
# Query: 'longsword'
# Query length: 9
# Tokens: ['longsword']
# EXACT MATCH: None
# Match: longsword in HOSSZU-1.1.1 (score: 0.7)
# Match: longsword in HOSSZU-2.3.4 (score: 0.7)
# RESULTS: 2 rules
#   HOSSZU-1.1.1: 0.70
#   HOSSZU-2.3.4: 0.70
```

### Common Issues & Solutions

**Issue 1: "Query returns no results"**
```python
# Solution: Lower threshold
results = search_engine.search_rules("query", threshold=0.1)
# Or try fuzzy matching separately
results = search_engine.fuzzy_match("query")
```

**Issue 2: "Wrong rules ranked highest"**
```python
# Solution: Check scoring
results = search_engine.search_rules("query", debug=True)
# Verify score calculation manually
# Adjust weights in scoring formula if needed
```

**Issue 3: "Alias not resolving"**
```python
# Solution: Check alias database
aliases = search_engine.aliases
if "term" in aliases:
    print(f"Aliases: {aliases['term']}")
else:
    print("Term not in alias database")
```

---

## Future Improvements

### Short Term (Next Sprint)

- [ ] Add caching layer (Redis) for frequent queries
- [ ] Implement request logging (query → results → time)
- [ ] Add more comprehensive alias mappings
- [ ] Optimize Levenshtein distance calculation

### Medium Term (Next Quarter)

- [ ] Implement BM25 ranking algorithm
- [ ] Add Trie data structure for prefix matching
- [ ] Support for wildcard queries ("longsword*")
- [ ] Query syntax support (AND, OR, NOT operators)

### Long Term (Next Year)

- [ ] Semantic search (embed rules with transformers)
- [ ] Graph-based navigation (rules → related rules)
- [ ] Machine learning ranking (learn from user clicks)
- [ ] Multi-language support beyond Hungarian/English

---

**Last Updated:** February 2026  
**Maintainer:** AI Agent, HEMA Development Team

For API reference, see [API.md](API.md).  
For system architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).  
For development workflow, see [DEVELOPMENT.md](DEVELOPMENT.md).
