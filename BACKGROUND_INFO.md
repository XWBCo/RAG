# RAG Service - Background & Context

> Strategic context gathered January 2026 to guide development priorities.

---

## Project Status

| Aspect | Status |
|--------|--------|
| **Production readiness** | Not in production yet |
| **Timeline pressure** | Months out, R&D/exploration phase |
| **Primary pain points** | Unknown - haven't tested enough to identify |

---

## Consumers

| App | Status | Endpoint |
|-----|--------|----------|
| **RPC Dashboard** (Dash/Plotly) | ✅ Integrated via Command Palette (⌘K) | **v2** `/api/v1/v2/query` |
| **React Portfolio App** | Uses v2 by default with v1 fallback | v2 with v1 fallback |
| **Estate Planning** | Demo purposes - uses v2 for queries, v1 for summarization | Mixed |
| **Query Playground** | `/playground` - manual v1/v2 testing | Both |

**Note:** Dashboard migrated to v2 on 2026-01-09. V2 now supports context-aware features (`prompt_name`, `app_context`) with 90% retrieval quality.

---

## Tech Direction

| Decision | Answer |
|----------|--------|
| **React migration** | Likely eventually, unclear when |
| **Current focus** | RAG core + Dash only (not React-readiness) |
| **LangGraph value** | **Confirmed valuable** - 46% better retrieval, but 6x slower (see v1 vs v2 section) |

---

## Deployment Environment

- Remote Windows machine
- Docker installed but **not used for current prod version**
- **Azure** - current cloud platform (flexibility TBD)
- **Snowflake** - centralized data source of truth (Q1 2026 rollout)

---

## Snowflake Integration Roadmap (Q1 2026)

**Status:** Planned, not yet implemented

### Why Snowflake Cortex?

Research validated (see `research/SYNTHESIS_AND_IMPLEMENTATION.md`):
- **Arctic Embed M v1.5** outperforms OpenAI text-embedding-3-large on MTEB (score: 55.14)
- Native `VECTOR` type with `VECTOR_L2_DISTANCE` for similarity search
- Data governance: embeddings never leave Snowflake boundary
- Single audit system for compliance

### Migration Path

| Phase | Timeline | Deliverable |
|-------|----------|-------------|
| POC | Weeks 1-2 | Benchmark Arctic vs OpenAI embeddings |
| Hybrid | Weeks 3-4 | Snowflake for investments, ChromaDB for FAQ |
| Production | Weeks 5-8 | Full Snowflake Cortex migration |
| Decommission | Week 9+ | ChromaDB retired to dev/test only |

### Technical Implementation

```sql
-- Snowflake Cortex vector search pattern
ALTER TABLE documents ADD COLUMN embedding VECTOR(FLOAT, 768);

UPDATE documents
SET embedding = SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', content);

SELECT content, VECTOR_L2_DISTANCE(embedding, query_embedding) as distance
FROM documents ORDER BY distance LIMIT 10;
```

### ChromaDB Deprecation

**Current:** Primary vector store (~530 documents)
**Issue:** No SOC 2 certification, single-node, not production-grade
**Plan:** Keep for local development, migrate production to Snowflake

---

## Compliance Timeline

**Critical deadline: SEC Regulation S-P - December 3, 2025**

| Requirement | Current State | Action Needed |
|-------------|---------------|---------------|
| Incident response program | ❌ | Written policies by Q3 |
| 30-day breach notification | ❌ | Process documentation |
| Third-party vendor oversight | ⚠️ | OpenAI/Snowflake attestations |
| 5-year audit trail | ⚠️ Partial | Extend QueryMetrics to full prompt/response |
| FINRA explainability | ⚠️ | CRAG grading + confidence scores (in place) |

See `research/SYNTHESIS_AND_IMPLEMENTATION.md` for full compliance gap analysis.

---

## RAG Service Priorities

| Priority | Assessment |
|----------|------------|
| **Answer quality** | v2 achieves 90% retrieval on FAQ content - good |
| **Response speed** | v1 ~2-4s; v2 ~5.5s (optimized from 24s) |
| **Knowledge management** | FAQ content (39 sections) working well |

**Key insight**: V1 and V2 are complementary. Dashboard uses v1 for context-aware features; v2 excels at general queries.

---

## Testing Needs (Prioritized)

1. ~~**Query playground UI**~~ ✅ Done - `/playground`
2. ~~**Evaluation harness**~~ ✅ Done - `python -m eval.cli`
3. ~~**Better logging**~~ ✅ Done - JSON metrics via `utils/logging.py`

**Current gaps:**
- Production monitoring (observability in deployed environment)
- User feedback loop (which queries fail in real usage)

---

## Strategic Decisions

| Decision | Choice |
|----------|--------|
| **Build tooling first** | Yes - feedback loops before optimization |
| **Start with** | Query playground UI |
| **Skip for now** | Python SDK, React/TS support, production hardening |

---

## What NOT to Build (Yet)

- Formal Python client SDK (only 1 real consumer)
- TypeScript/React client (migration timeline unclear)
- Production hardening (retries, circuit breakers, observability)
- ~~Remove LangGraph~~ **Keep it** - data shows it's valuable

---

## v1 vs v2 Endpoint Decision

**Tested 2026-01-09 with 44 queries across investments and app_education domains.**

### Comparison Results

| Metric | v1 (Basic) | v2 (LangGraph) |
|--------|------------|----------------|
| Retrieval Score | 44% | **90%** |
| Topic Coverage | 71% | 71% |
| Latency | **~4s** | ~24s |
| Grade Distribution | 0🟢/7🟡/2🔴 | 9🟢/0🟡/0🔴 |

### Why v2 is Better (Quality)

- **CRAG document grading**: LLM evaluates each retrieved doc for relevance
- **Reranking**: Cohere or fallback confidence-based reordering
- **Intent routing**: Specialized prompts for archetype/pipeline/clarity queries

### Why v2 is Slower (6x)

Each query requires:
1. Retrieve 10 documents
2. 10 LLM calls for grading (~1-2s each, sequential)
3. Rerank remaining docs
4. Generate final response

**Optimization opportunity:** Parallelize grading calls, use faster model for grading.

**Status:** ✅ Fully optimized (2026-01-09).
- `grade_documents_async()` runs all LLM grading calls via `asyncio.gather()`
- Prompts tuned for 2-4 sentence responses
- **Final v2 latency: ~5-6s** (down from 24s = **75% faster**)
- Response length: ~40-50 words (down from 393 = **89% shorter**)

### Recommendation (Updated 2026-01-09)

| Use Case | Endpoint | Reason |
|----------|----------|--------|
| **Dashboard Command Palette** | **v1** | Requires `prompt_name` + `app_context` for results interpretation |
| General FAQ questions | **v2** | 90% retrieval quality, 5.5s latency |
| Multi-turn conversations | **v2** | Has `thread_id` for memory |
| Archetype selection | **v2** | Intent routing for IBI, Impact 100%, etc. |
| Quick lookups | **v1** | 2s latency, simpler responses |

**Key insight:** V1 and V2 serve different purposes. Dashboard stays on v1 for context-aware features.

---

## V1 vs V2 Compatibility

**V2 now supports all V1 context-aware features.** (Updated 2026-01-09)

### Feature Comparison

| Feature | V1 `/query/custom` | V2 `/v2/query` |
|---------|-------------------|----------------|
| `prompt_name` (specialized prompts) | ✅ Yes | ✅ **Yes** (added 2026-01-09) |
| `app_context` (computed results) | ✅ Yes | ✅ **Yes** (added 2026-01-09) |
| `top_k`, `min_similarity` | ✅ Configurable | ❌ Hardcoded (optimized defaults) |
| `mode` (COMPACT, REFINE, etc.) | ✅ Yes | ❌ Fixed |
| Multi-turn conversation | ❌ No | ✅ `thread_id` |
| Intent routing | ❌ No | ✅ archetype/pipeline/clarity |
| CRAG quality signal | ❌ No | ✅ `retrieval_quality` |
| Retrieval quality | 44% | **90%** |
| Streaming | ❌ No | ✅ `/v2/query/stream` |

### Use Case Guidance

| Use Case | Recommended Endpoint |
|----------|---------------------|
| **All production use** | **v2** - 90% retrieval + context-aware features |
| Legacy integrations | v1 - still available for backwards compatibility |
| Multi-turn conversations | **v2** - has `thread_id` for memory |
| Archetype selection queries | **v2** - intent routing for IBI, Impact 100%, etc. |

### RPC Dashboard Integration Details

**Location:** `/Users/xavi_court/dev/alti-rpc-dashboard/app_dashboard3.py`
**Migrated to V2:** 2026-01-09

**Command Palette (⌘K) Features:**
- Auto-detects page context from URL (`/mcs` → Monte Carlo)
- Injects computed results via `app_context`
- Uses specialized prompts per context:
  - `monte_carlo_interpreter_cited` for /mcs
  - `risk_metrics_interpreter_cited` for /risk
  - `esg_analysis_cited` for /clarity
  - `results_interpreter_cited` for general

**API Contract (V2):**
```python
POST /api/v1/v2/query
{
    "query": "What does my 95th percentile mean?",
    "domain": "app_education",
    "prompt_name": "monte_carlo_interpreter_cited",
    "app_context": {"percentile_95": 2500000, "success_probability": 0.92}
}
```

**Benefits of V2 Migration:**
- 90% retrieval quality (vs 44% on v1)
- CRAG document grading filters irrelevant results
- Hybrid search (BM25 + semantic) finds more matches

---

## Completed Work

- [x] Query Playground UI at `/playground`
- [x] PDF text preprocessor for better chunking
- [x] Markdown document loader for FAQ content
- [x] FAQ content for 3 apps (39 sections total)
- [x] Retrieval quality improvement: 36% → 62% avg
- [x] Evaluation harness CLI (`python -m eval.cli`)
- [x] v1 vs v2 comparison tooling (44 test queries)
- [x] Structured logging with timing/retrieval details
- [x] Fix v2 domain support (was hardcoded to investments)
- [x] v1 vs v2 comparison complete: v2 is 46% better but 6x slower
- [x] Parallelize v2 grading: `asyncio.gather()` for concurrent LLM calls
- [x] Concise prompts: 2-4 sentence responses (393 → 43 words)
- [x] v2 latency optimization: 24s → 5.5s (75% improvement)
- [x] Deep research: Google + Perplexity on RAG architecture
- [x] Research verification: All claims independently verified
- [x] Documentation restructure: sessions/, research/ folders
- [x] RPC Dashboard integration audit: confirmed v1 in use via Command Palette
- [x] V1 vs V2 compatibility analysis: documented feature gaps
- [x] Extended v2 to support prompt_name and app_context (v1 features)
- [x] Migrated RPC Dashboard from v1 to v2 endpoint
- [x] Test suite for 3 core apps (MCS, Portfolio Eval, Risk Factor)
- [x] Feedback loop: QueryMetrics logs retrieval_quality for v2 queries
- [x] ClarityAI FAQ content (18 ESG metrics with definitions and calculations)
- [x] Test suite expansion: 44 → 62 queries (+18 ClarityAI queries)
- [x] Content gap fixes: max drawdown, Effective N, factor explained
- [x] V1 prompt brevity fix: custom prompts now inject 2-4 sentence constraint
- [x] Evaluation pass rate: 91.9% → 96.8%
- [x] Command Palette: Slide-over panel (replaces centered modal)
- [x] Command Palette: 80-word max brevity (stricter than 2-4 sentences)
- [x] Command Palette: Source shown at top of response
- [x] Command Palette: Follow-up button (preserves previous response)
- [x] Command Palette: Scroll fade indicator
- [x] Command Palette: Removed expand button (marginal value)
- [x] Metrics logging: Now writes to `logs/metrics.jsonl`
- [x] Command Palette: Context pills moved to top (above search bar)
- [x] Command Palette: Draggable modal (grab header area to move)
- [x] Command Palette: Resizable modal (4 corner handles)
- [x] Command Palette: Wider default width (420px → 500px)
- [x] Command Palette: Simplified header (removed dots + X button)
- [x] Command Palette: Removed duplicate footnotes (only top source header)
- [x] Command Palette: Removed "Ask a follow-up" button (single-turn focus)
- [x] Command Palette: All-white modal background (removed grey bands)
- [x] Command Palette: Collapsible shortcuts footer (⌨ icon expands on hover)
- [x] Command Palette: Removed FAB tooltip (shortcuts now in modal footer)
- [x] Command Palette: Removed "All" pill (Portfolio Eval is default)
- [x] Command Palette: Renamed pills (Portfolio→Portfolio Eval, Risk→Risk Contribution, ESG→Impact)
- [x] Command Palette: Citation renumbering (sequential display regardless of source index)
- [x] Command Palette: Markdown code block rendering for formulas
- [x] RAG Prompts: Formula detection in `esg_analysis_cited` (3-part output: formula, example, description)
- [x] FAQ Content: "What is Clarity AI?" overview with company facts
- [x] FAQ Content: Carbon vs Financed Intensity comparison
- [x] FAQ Content: Grammar fixes across all contexts
- [x] MCS App: Fixed auto-run bug on page load (added n_clicks guard)
- [x] Command Palette: Pills no longer wrap (added flexWrap: nowrap)
- [x] RAG Prompts: MCS prompt tone fix - leads with median, not pessimistic 5th percentile
- [x] FAB Icon: Redesigned using AlTi "Ai" letterforms (pillar A + turquoise i)
- [x] FAB Icon: Rotating circle animation, square tittle with glow
- [x] FAB Icon: Teal gradient beta tag with shadow
- [x] Modal: Liquid glass styling (backdrop-filter blur, semi-transparent bg)
- [x] Modal: Border radius increased to 20px, glass effect on pills
- [x] FAQ Content: Financed Intensity formula matches Clarity AI Guide source
- [x] RAG Prompts: Formula template now requires COMPONENTS definitions table
- [x] Command Palette: "All" pill restored as default with cross-domain FAQs
- [x] FAQ Content: FAQ_General.md with 7 cross-domain sections (899 total docs)
- [x] Command Palette: Feedback UI (checkmark/X icons, optional text input)
- [x] Feedback logging: `[FEEDBACK]` and `[FEEDBACK-DETAIL]` entries in app logs

---

## Planned Features

### MCS Simulation Selector (Not Yet Implemented)

**Problem:** MCS has 3 simulations with dense data. RAG receives ALL simulation data regardless of which one user asks about.

**Proposed Solution:** Sub-pills that appear only when Monte Carlo context is active:
```
[Portfolio Eval] [Monte Carlo●] [Risk] [CMA] [Impact]
                 [Sim 1] [Sim 2] [Sim 3] [All●]
```

**Behavior:**
- Default "All": Current behavior, sends all 3 simulations
- Specific sim: Only sends that simulation's data to RAG

**Open questions before implementation:**
1. Use simulation names (user-defined) or generic "Sim 1/2/3"?
2. Auto-detect from query or require explicit selection?
3. Change FAQ suggestions based on selection?

**See:** `sessions/2026-01-10_mcs-context-investigation-and-ux.md`

---

## Known Issues

### RAG Context Mismatch (MCS Results) - RESOLVED

**Status:** ✅ Investigated 2026-01-10 - Working correctly

**Original Report:** RAG response contained numbers not matching chart output.

**Investigation Findings:**
Debug logging added and live test performed. Data flow verified:
1. `mcs-results-store` correctly populated by simulation callback
2. `app_context` correctly passed in API payload
3. `build_contextual_query()` correctly formats MCS data
4. LangGraph workflow correctly receives enhanced query
5. LLM response accurately references user's actual values

**Root Cause of Original Issue (Likely):**
- Context pill manually changed from "Monte Carlo" to another context
- Page refreshed (memory store cleared) without re-running simulations
- Query sent before simulation callback completed (race condition)

**Prevention:** Context auto-detection on URL change handles most cases. Users must run simulations before querying about results.

**See:** `sessions/2026-01-10_command-palette-modal-polish.md`

---

## Research Decision: Chat Interface vs Smart Q&A Panel

### Context

Originally planned to implement a chat-style interface with conversation history. After researching 2025-2026 UX patterns, we pivoted.

### Key Research Findings

| Finding | Source |
|---------|--------|
| Chat is slow for intent expression (30-60s per input) | Smashing Magazine |
| 70% adoption with NLQ interfaces | ThoughtSpot |
| Proactive help reduces support tickets 30% | Chameleon |
| Task-oriented UIs outperform conversational UIs for help | Multiple |

### Decision: Skip Full Chat Interface

**Implemented instead (Smart Q&A Panel):**
- Context pills at top ✓
- Draggable + resizable panel ✓
- Simplified header (no X button, close via ESC/backdrop)
- Keep single-turn Q&A with follow-up button

**Skipped:**
- Chat bubbles and conversation metaphor
- Full chat history storage
- Position memory via localStorage

**Rationale:** Most queries are single-turn with context, not extended conversations. The existing "Ask follow-up" button already preserves previous response for reference.

### Implementation Guide

See: `sessions/2026-01-10_command-palette-interaction-redesign.md`

---

## Operational Notes

### Server Restart Required After Code Changes

**Issue:** After modifying retrieval or workflow code, the RAG service may use stale cached retrievers.

**Symptom:** Queries return 0 sources with `retrieval_quality: "poor"` even though ChromaDB has matching documents.

**Fix:**
```bash
pkill -f uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080
```

### Latency Expectations

| Condition | Latency |
|-----------|---------|
| Cold start (first query after restart) | 7-11s |
| Warm (subsequent queries) | ~5.5s |
| With app_context transformation | +0.5s |

---

## Documentation Structure

```
alti-rag-service/
├── BACKGROUND_INFO.md          # This file - strategic context (start here)
├── DEVELOPMENT_LOG.md          # Technical session logs
├── sessions/                   # Detailed session summaries
│   ├── 2026-01-09_evaluation-harness.md
│   ├── 2026-01-09_v2-optimization.md
│   ├── 2026-01-09_v2-dashboard-migration.md
│   ├── 2026-01-10_rag-finetuning-and-ux-review.md
│   ├── 2026-01-10_command-palette-ux-improvements.md
│   ├── 2026-01-10_command-palette-interaction-redesign.md
│   ├── 2026-01-10_command-palette-modal-polish.md
│   ├── 2026-01-10_mcs-context-investigation-and-ux.md
│   ├── 2026-01-10_fab-icon-liquid-glass-faq-fix.md
│   └── 2026-01-11_all-pill-feedback-ui.md  # Latest
├── research/                   # Architecture research & decisions
│   ├── SYNTHESIS_AND_IMPLEMENTATION.md  # Cross-validated findings
│   ├── GOOGLE_DEEP_RESEARCH_RAG_2025.md
│   ├── PERPLEXITY_DEEP_RESEARCH_RAG_2025.md
│   └── RAG_ARCHITECTURE_RESEARCH_PROMPT.md
├── eval/                       # Evaluation harness (python -m eval.cli)
├── graph/                      # LangGraph workflow nodes
└── data/                       # Knowledge base content
```

### Key Documents

| Document | Purpose | When to Read |
|----------|---------|--------------|
| **BACKGROUND_INFO.md** | Strategic context, current state | Start here |
| **research/SYNTHESIS_AND_IMPLEMENTATION.md** | Architecture decisions, Snowflake plan | Planning |
| **sessions/*.md** | Detailed session work logs | Debugging, handoff |
| **DEVELOPMENT_LOG.md** | Technical errors and fixes | Troubleshooting |

---

## Collection Reference

```
alti_investments (456 docs):
  - fund_model_allocation: 220 (48%)
  - fund_profile: 156 (34%)
  - cma_data: 54 (12%)
  - Other: 26 (6%)

app_education_docs (74 docs):
  - faq_section: 39 (53%)
  - pdf_document: 21 (28%)
  - presentation_slide: 14 (19%)
```

---

*Last updated: 2026-01-11 (All pill restored, FAQ_General.md, feedback UI with logging)*
