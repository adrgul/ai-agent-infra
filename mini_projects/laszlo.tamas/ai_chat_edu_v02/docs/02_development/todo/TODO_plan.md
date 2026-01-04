# TODO_plan.md
## Future Development Opportunities

**Purpose:** "Nice-to-have" features - not critical, consider for future.

**Last Updated:** 2026-01-02

---

## 🎯 **Decision Criteria**

Ask before implementing:
1. Real use case? (not just "cool feature")
2. Cost vs benefit justified?
3. Core system stable enough?

---

## 📊 **PRIORITIZED BACKLOG**

### 🟢 **HIGH VALUE**

#### TEMP.4 OpenAI Prompt Caching 💰
**Value:** 80-90% cost reduction  
**Effort:** Medium  

**Why:** Real cost impact ($2-3/day → $0.20/day), educational cache patterns.

**Implementation:** 3-tier cache (Memory → PostgreSQL → LLM), OpenAI `cache_control` parameter.

**Spec:** `docs/04_implementations/TEMP.4_PROMPT_CACHING_IMPLEMENTATION.md`

---

#### P0.9.2 Enhanced Source Attribution (Page Numbers) 📄
**Value:** User trust & verification  
**Effort:** Low-Medium  

**Why:** "Check page 42" = verifiable answers, shows system precision.

**Implementation:**
- PDF: Track page_number during extraction
- Qdrant: `chunk_metadata: {page_number, chapter}`
- Frontend: "📄 Document.pdf (p. 42)"

---

### 🟡 **MEDIUM VALUE**

#### TEMP.5 Chat Message Telemetry 📊
**Value:** Production monitoring & cost visibility  
**Effort:** Medium  

**Why:** Metrics-driven optimization, not needed until production.

**Implementation:** 12 telemetry fields (tokens, cache hits, response time), analytics endpoints.

**Spec:** `docs/04_implementations/TEMP.5_CHAT_MESSAGE_TELEMETRY.md`

**Decision:** Wait for production deployment.

---

#### P0.10.1 Document Summary ❓
**Value:** UI preview & "What's this about?" queries  
**Effort:** Low  

**Why Questionable:**
- ✅ Educational demo
- ❌ Vector search already works
- ❌ No document list UI
- ❌ Extra cost per upload

**Recommendation:** 
- **SKIP** (current chat-only interface)
- **IMPLEMENT** only if document browsing UI exists

---

#### P0.9.3 Search Performance ⚡
**Value:** Faster retrieval at scale  
**Effort:** Low  

**Why:** Premature optimization (current <2s, ~1000 chunks).

**Trigger:** Implement when >2s or >5000 chunks.

---

### 🔴 **LOW VALUE**

#### P1.1 Long-term Chat Memory 🧠
**Why Skip:** Complex, uncertain value, RAG already provides memory.

#### P1.2 Product Knowledge 🛍️
**Why Skip:** Different domain (e-commerce), scope creep.

#### P1.3 Multi-source RAG 🔀
**Why Skip:** Depends on P1.2.

---

## 🚫 **EXPLICITLY REJECTED**

- **P0.10.2 Keyword Detection** - Obsolete (P0.12 uses LLM routing)
- **P2.x Admin Features** - Out of scope for educational project

---

## 🎓 **LEARNING FOCUS**

| Skill | Feature |
|-------|---------|
| Cost Optimization | TEMP.4 (Caching) |
| Monitoring | TEMP.5 (Telemetry) |
| UX Polish | P0.9.2 (Page Numbers) |

---

## 🔄 **Review**

Re-evaluate:
- After P0.11-P0.17 complete ✅
- Before Phase 3
- On instructor request

**Next Review:** 2026-01-10

---

**Note:** Planning document only. Features move to TODO_v02.md when approved.
