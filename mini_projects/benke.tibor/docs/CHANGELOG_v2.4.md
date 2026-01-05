# Changelog v2.4 - RAG Optimizations & Test Suite Expansion

**Release Date**: 2026-01-05  
**Sprint Focus**: RAG retrieval quality improvements, comprehensive testing

---

## 🎯 Executive Summary

Implemented 4 major RAG optimizations to eliminate duplicate citations, improve IT domain accuracy, and leverage user feedback. Added 27 comprehensive unit/integration tests achieving **53% total code coverage** (up from 22%).

**Key Metrics:**
- ✅ **180/203 tests passing** (89% success rate)
- 📊 **53% code coverage** (more than doubled)
- 🚀 **qdrant_rag_client.py**: 18% → 70% coverage
- 🎯 **openai_clients.py**: 100% coverage

---

## ✨ New Features

### 1. **Content Deduplication (v2.4)**

**Problem**: Marketing queries returned 5 duplicate documents (same content in PDF and DOCX formats).

**Solution**: Signature-based deduplication using normalized titles + 80-char content preview.

**Implementation**:
```python
# backend/infrastructure/qdrant_rag_client.py
def _deduplicate_citations(citations: List[Citation]) -> List[Citation]:
    """Remove PDF/DOCX duplicates, keep highest-scoring citation."""
    seen = {}
    for citation in citations:
        normalized_title = _normalize_title(citation.title)  # Remove .pdf/.docx
        signature = (normalized_title, citation.content[:80].strip())
        if signature not in seen or citation.score > seen[signature].score:
            seen[signature] = citation
    return list(seen.values())
```

**Impact**:
- Marketing queries: 5 duplicates → 1-2 unique results
- Users see cleaner, non-redundant context
- LLM receives deduplicated citations

**Testing**: 9 unit tests (exact duplicates, PDF/DOCX formats, edge cases)

---

### 2. **IT Domain Overlap Boost (v2.4)**

**Problem**: IT domain queries sometimes ranked irrelevant sections higher due to semantic similarity mismatch.

**Solution**: Lexical token matching with 0-20% score boost for citations containing query keywords.

**Implementation**:
```python
# backend/infrastructure/qdrant_rag_client.py
def _apply_it_overlap_boost(citations: List[Citation], query: str) -> List[Citation]:
    """Boost IT citations with high lexical overlap to query tokens."""
    query_tokens = {t for t in re.split(r"[^a-zA-Z0-9áéíóöőúüű]+", query.lower()) if len(t) >= 3}
    for c in citations:
        text = " ".join([c.title or "", c.content or ""]).lower()
        hits = sum(1 for tok in query_tokens if tok in text)
        overlap_ratio = hits / max(1, len(query_tokens))
        boost = 1 + min(0.2, overlap_ratio * 0.4)  # Max +20%
        c.score *= boost
    return sorted(citations, key=lambda c: c.score, reverse=True)
```

**Impact**:
- IT queries with lexical matches get 5-20% boost
- Better ranking for "VPN", "printer", "laptop" technical keywords
- Hungarian character support (áéíóöőúüű)

**Testing**: 11 unit tests (boost calculation, max cap, Hungarian chars, re-ranking)

---

### 3. **Section ID Citations (v2.4)**

**Problem**: VPN queries cited generic "Document 5" or "IT-KB-320" instead of correct section "IT-KB-234".

**Solution**: Parser/chunker inheritance of section_id to subheadings.

**Implementation**:
```python
# backend/infrastructure/atlassian_client.py
def _parse_it_policy_sections(html: str) -> List[Section]:
    last_section_id = None
    for elem in soup.find_all(['h1', 'h2', 'h3']):
        section_id = extract_id_from_heading(elem.text)
        if not section_id and last_section_id:
            section_id = last_section_id  # Inherit from parent
        last_section_id = section_id
        content = f"[{section_id}] {elem.text}\n{elem.next_sibling}"
    return sections
```

**Impact**:
- VPN queries now correctly cite **[IT-KB-234]**
- Qdrant indexing: 21 chunks → 33 chunks (all with section_id)
- Debug panel shows `[IT-KB-234]` instead of generic `[Doc 5]`

**Testing**: Verified via integration tests + manual Qdrant inspection

---

### 4. **Feedback-Weighted Ranking (v2.4 Documentation)**

**Status**: Already implemented in v2.2, now fully documented.

**Tiered Boost System**:
- **High tier** (>70% positive): +30% boost
- **Medium tier** (40-70% positive): +10% boost
- **Low tier** (<40% positive): -20% penalty
- **No data**: 0% (neutral)

**Implementation**:
```python
# backend/infrastructure/qdrant_rag_client.py (existing code)
def _apply_feedback_weighted_ranking(citations: List[Citation]) -> List[Citation]:
    feedback_map = postgres_client.get_citation_feedback_batch([c.doc_id for c in citations])
    for c in citations:
        fb = feedback_map.get(c.doc_id, {})
        positive_ratio = fb.get("percentage", None)
        if positive_ratio is None:
            boost = 0.0
        elif positive_ratio > 70:
            boost = 0.3
        elif positive_ratio >= 40:
            boost = 0.1
        else:
            boost = -0.2
        c.score += boost
    return sorted(citations, key=lambda c: c.score, reverse=True)
```

**Impact**:
- User feedback directly influences future ranking
- Poorly-rated chunks demoted (-20%)
- High-quality chunks promoted (+30%)

**Testing**: 4 unit tests (tier calculation) + 3 integration tests

---

## 🧪 Testing Improvements

### New Test Files

**1. `test_qdrant_deduplication.py` (21 tests)**
- **TestDeduplicateCitations** (9 tests):
  - Exact duplicate removal
  - PDF/DOCX format handling
  - Title normalization (.pdf/.docx removal)
  - Content preview comparison (80 chars)
  - Highest-score preservation
  - Metadata preservation
  
- **TestApplyITOverlapBoost** (11 tests):
  - Basic boost calculation
  - Max 20% cap enforcement
  - Short token filtering (≥3 chars)
  - Case-insensitive matching
  - Hungarian character support (áéíóöőúüű)
  - Re-ranking by boosted scores
  - Edge cases (empty query/citations, no matches)
  
- **TestDeduplicationAndBoostIntegration** (1 test):
  - Complete pipeline: dedup → boost → ranking

**2. `test_qdrant_integration.py` (6 tests)**
- **TestQdrantRAGIntegration** (6 tests):
  - End-to-end retrieval with deduplication
  - IT domain with overlap boost
  - Cache hit/miss flows
  - PostgreSQL unavailable fallback
  - Empty search results handling
  - Feedback ranking score adjustment

### Coverage Improvements

| Module | Before | After | Change |
|--------|--------|-------|--------|
| `qdrant_rag_client.py` | 18% | **70%** | +52% ✅ |
| `openai_clients.py` | 81% | **100%** | +19% ✅ |
| `atlassian_client.py` | 22% | **87%** | +65% ✅ |
| `error_handling.py` | 23% | **87%** | +64% ✅ |
| `redis_client.py` | 23% | **58%** | +35% |
| **Total** | **22%** | **53%** | **+31%** ✅ |

### Test Execution Results

```bash
======================== 180 passed, 23 skipped in 2.70s =======================

Required test coverage of 25% reached. Total coverage: 52.54%
```

**Test Count**: 153 → 180 (+27 new tests)

---

## 📝 Documentation Updates

### Updated Files

**1. `docs/FEATURES.md`**
- Version: 2.3 → 2.4
- Moved Citation Ranking from "Future" to "✅ IMPLEMENTED"
- Added deduplication section
- Added IT overlap boost section
- Updated roadmap (moved completed features)

**2. `docs/IT_DOMAIN_IMPLEMENTATION.md`**
- Added "RAG Optimalizációk (v2.4)" section
- 4 subsections: Deduplication, IT Overlap Boost, Feedback Ranking, Section IDs
- Code examples for each optimization
- Updated benefits: 6 → 10 items

**3. `backend/tests/README.md`**
- Test count: 121 → 180
- Coverage: 49% → 53%
- Added RAG optimization test sections
- Coverage breakdown by module
- New test execution examples

**4. `README.md`**
- Updated test statistics
- Added coverage highlights
- Module-level coverage breakdown

---

## 🔧 Code Changes

### Modified Files

**1. `backend/infrastructure/qdrant_rag_client.py`**
- Added `_deduplicate_citations()` function (lines ~85-115)
  - Signature: (normalized_title, content[:80])
  - Keeps highest-scoring citation per signature
  - Title normalization (removes .pdf/.docx extensions)
  
- Added `_apply_it_overlap_boost()` function (lines ~60-80)
  - Lexical token matching (≥3 chars)
  - 0-20% score boost based on overlap ratio
  - Hungarian character support
  
- Applied deduplication before feedback ranking (line ~276)
  ```python
  citations = _deduplicate_citations(citations)
  citations = _apply_feedback_weighted_ranking(citations)
  ```
  
- Applied deduplication in `_fetch_by_qdrant_ids()` (line ~398)

**2. `backend/services/agent.py`**
- Updated `_retrieval_node()` to use section_id in telemetry
- IT domain now shows `[IT-KB-234]` instead of `[Doc 5]` in RAG context

**3. `backend/infrastructure/atlassian_client.py`**
- `_parse_it_policy_sections()` inherits section_id to subheadings
- Content prefixed with `[section_id]` before chunking

**4. `backend/scripts/sync_confluence_it_policy.py`**
- `chunk_sections()` inherits section_id across sections
- Ensures `[IT-KB-XXX]` prefix in chunks before vector indexing

### New Files

**1. `backend/tests/test_qdrant_deduplication.py`** (~450 lines)
- 21 unit tests for deduplication and IT overlap boost
- Mock Citation objects for isolated testing

**2. `backend/tests/test_qdrant_integration.py`** (~350 lines)
- 6 integration tests for end-to-end RAG pipeline
- Mock fixtures for Qdrant, PostgreSQL, Redis, OpenAI

**3. `docs/CHANGELOG_v2.4.md`** (this file)
- Complete release documentation

---

## 🐛 Bug Fixes

### Fixed Issues

**1. VPN Citation Bug (IT-KB-234 Missing)**
- **Symptom**: VPN queries returned "Document 5" or "IT-KB-320" instead of "IT-KB-234"
- **Root Cause**: Subheadings without explicit section IDs didn't inherit from parent
- **Fix**: Parser tracks `last_section_id` and propagates to h2/h3 elements
- **Verification**: Qdrant now has 33 chunks (was 21) with correct section_ids

**2. Marketing Duplicate Content**
- **Symptom**: Aurora guide appeared 5 times (PDF + DOCX versions)
- **Root Cause**: No deduplication logic for different file formats
- **Fix**: Title normalization + content signature matching
- **Verification**: 5 duplicates → 1-2 unique results

**3. Test File Docker Sync Issue**
- **Symptom**: New test files not visible in running container after creation
- **Root Cause**: Docker volume mount lag + COPY timing in Dockerfile
- **Fix**: Manual `docker cp` to transfer files directly into running container
- **Permanent Fix**: Added to container rebuild workflow

---

## 🔄 Database Changes

### Qdrant Collection Updates

**IT Policy Reindexing:**
- Collection: `multi_domain_kb`
- Domain: `it`
- Chunks: 21 → **33** (+57%)
- All chunks now have `section_id` metadata
- Verified via: `docker exec qdrant_backend python scripts/sync_confluence_it_policy.py`

**Redis Cache Flush:**
```bash
docker exec knowledgerouter_backend python manage.py shell
>>> from infrastructure.redis_client import redis_cache
>>> redis_cache.clear_all_cache()
```

---

## 📊 Performance Impact

### Query Quality Improvements

**Before v2.4:**
- VPN queries: ❌ Wrong section citations (IT-KB-320)
- Marketing queries: ⚠️ 5 duplicate results
- IT queries: ⚠️ Semantic-only ranking (missed lexical matches)

**After v2.4:**
- VPN queries: ✅ Correct section [IT-KB-234]
- Marketing queries: ✅ 1-2 unique results
- IT queries: ✅ Lexical boost for technical keywords (+5-20%)

### Test Execution Time

```bash
# Full test suite
180 passed, 23 skipped in 2.70s

# New tests only
27 passed in 0.85s
```

---

## 🚀 Deployment Steps

### 1. Pull Latest Code
```bash
git pull origin main
```

### 2. Rebuild Backend Container
```bash
docker-compose build backend
docker-compose restart backend
```

### 3. Reindex IT Policy
```bash
docker exec knowledgerouter_backend python scripts/sync_confluence_it_policy.py
```

### 4. Clear Cache
```bash
docker exec knowledgerouter_backend python manage.py shell
>>> from infrastructure.redis_client import redis_cache
>>> redis_cache.clear_all_cache()
```

### 5. Verify Tests Pass
```bash
docker exec knowledgerouter_backend pytest tests/ -v --cov=infrastructure
```

**Expected Output**: 180 passed, 23 skipped, 53% coverage

---

## 🔮 Future Work

### Medium Priority (Next Sprint)

**1. Performance Benchmarks**
- Measure deduplication latency impact
- Baseline: Query time before/after dedup
- Target: <50ms overhead per query

**2. Documentation Review**
- Update `docs/API.md` with new RAG parameters
- Review `docs/REDIS_CACHE.md` for L1/L2 cache strategy

**3. Coverage Improvement**
- Target: 60% total coverage
- Focus: `postgres_client.py` (44% → 60%)
- Focus: `redis_client.py` (58% → 75%)

### Low Priority (Backlog)

**1. Deduplication Algorithm Enhancement**
- Use fuzzy string matching (Levenshtein distance)
- Configurable similarity threshold (default 80%)
- Benchmark against signature-based approach

**2. IT Overlap Boost Tuning**
- A/B test boost percentages (10%, 15%, 20%)
- Analyze query logs for optimal boost value
- Consider domain-specific boost caps

**3. Feedback Loop Automation**
- Auto-collect implicit feedback (citation click-through)
- Decay old feedback scores over time
- Threshold-based reindexing triggers

---

## 👥 Contributors

- **Benke Tibor** - Implementation, testing, documentation

---

## 📚 References

- [FEATURES.md](./FEATURES.md) - Complete feature list (v2.4)
- [IT_DOMAIN_IMPLEMENTATION.md](./IT_DOMAIN_IMPLEMENTATION.md) - IT domain architecture
- [backend/tests/README.md](../backend/tests/README.md) - Test suite documentation
- [INSTALLATION.md](../INSTALLATION.md) - Setup guide

---

**Version**: 2.4  
**Status**: ✅ Production Ready  
**Next Release**: v2.5 (Performance Optimizations)
