# RAG Service Refinements & Testing Session - 2026-01-14

## Session Summary

Comprehensive testing of 6 new enhancements, fixed LangChain compatibility issues, and implemented 3 Snowflake-agnostic improvements for ongoing refinement.

---

## Part 1: Enhancement Testing

### Issue Discovered: LangChain 1.2.x Breaking Changes

**Problem**: Service fell back to V1 with error:
```
No module named 'langchain.retrievers'
```

**Root Cause**: LangChain 1.2.x removed the `retrievers` submodule. The imports for `EnsembleRetriever` and `BM25Retriever` no longer work.

**Fix Applied** (`graph/nodes/retrieve.py`):
- Created `SimpleBM25Retriever` using `rank_bm25.BM25Okapi` directly
- Created `SimpleEnsembleRetriever` implementing weighted Reciprocal Rank Fusion
- Both classes extend `BaseRetriever` for LangChain compatibility

**Benefit**: More robust than depending on changing LangChain APIs.

### Test Results (All Passing)

| Test | Result | Details |
|------|--------|---------|
| Cache Endpoints | ✅ | `/cache/stats`, `/cache/invalidate` working |
| Circuit Breaker | ✅ | State tracking, 0 failures during testing |
| BM25 Hybrid Retrieval | ✅ | Exact fund names found with "good" quality |
| Response Caching | ✅ | **7.90s → 0.17s** (97% faster on cache hit) |
| Playground UI | ✅ | V2 endpoint, intent detection, sources display |
| Stress Test | ✅ | 5 concurrent requests, 41.9s total, 0 failures |

### Key Metrics Observed

- V2 cold query: ~7-8s
- V2 cached query: ~0.17s
- Intent detection: Working (archetype, clarity, general)
- Circuit breaker: Stayed closed through all tests

---

## Part 2: Snowflake Research & Planning

### Updated Snowflake Capabilities (Web Search Jan 2026)

| Feature | Status | Notes |
|---------|--------|-------|
| `AI_EMBED` | GA (Nov 2025) | Replaces `EMBED_TEXT_768`, supports multimodal |
| Arctic Embed L v2.0 | Available | 1024-d, 74 languages, 8192 token context |
| Cortex Search | Public Preview | **Managed hybrid search for RAG** |
| `VECTOR` data type | Available | Native vector column support |

**Key Finding**: Cortex Search could replace most of the custom RAG code - it handles embedding, hybrid search, and semantic reranking automatically.

### Questions for IT (Email Draft Provided)

1. Is Cortex Search available on our account?
2. Do we have access to `AI_EMBED` and `COMPLETE` functions?
3. Can we create tables and Cortex Search Services?
4. What warehouse can we use?
5. How should our application authenticate?

---

## Part 3: Snowflake-Agnostic Improvements Implemented

Given uncertainty about Snowflake availability, implemented improvements that work with any backend:

### 1. Document Re-ingestion

```
Before: 456 documents
After:  1844 documents
```

Enhanced loaders now active:
- PDF table extraction (PyMuPDF)
- Excel intelligent sheet classification (returns_risk, correlation, time_series)

### 2. LLM-Based Query Expansion

**File**: `graph/nodes/retrieve.py`

Added `expand_query_with_llm()` function that uses GPT-4o-mini to expand queries with domain-specific terms.

**Example**:
```
Original: "What is IBI?"
Expanded: "What is IBI? investment model portfolios, fund allocations,
          Impact 100%, Enhanced Balance, sustainable investing,
          portfolio diversification, risk management strategies."
```

**Impact**: Improved recall for ambiguous queries without changing retrieval backend.

### 3. Cohere Reranking (Ready)

**File**: `graph/nodes/grade.py`

- Fixed broken import (`DocumentCompressorPipeline` removed)
- Code wired into workflow at `rerank` node
- Uses `rerank-english-v3.0` model
- Falls back to confidence sort when no API key

**To Enable**: Add `COHERE_API_KEY` to `.env` (free tier: 1000/month)

---

## Files Modified

| File | Changes |
|------|---------|
| `graph/nodes/retrieve.py` | Custom BM25/Ensemble retrievers, query expansion |
| `graph/nodes/grade.py` | Fixed Cohere import |
| `.env.example` | Added `COHERE_API_KEY` |

---

## Architecture: Snowflake Migration Path

```
Current:
  Query → Expansion → ChromaDB + BM25 → Rerank → Grade → Generate

With Snowflake Cortex Search:
  Query → Expansion → Cortex Search (hybrid built-in) → Rerank → Grade → Generate
                      └── Only this layer changes ──┘
```

**Key Insight**: Query expansion and reranking are backend-agnostic - they transfer directly to Snowflake.

---

## Outstanding Tasks

### Immediate
- [ ] Ingest new fund documents from `~/Downloads/RAG Files.zip` (22 PDFs/Excel files)
- [ ] Add COHERE_API_KEY to production .env
- [ ] Run eval baseline with new document set

### When Snowflake Confirmed
- [ ] Implement `SnowflakeRAGRetriever` against `BaseRAGRetriever` interface
- [ ] Test Cortex Search performance vs ChromaDB
- [ ] Plan data migration

---

## New Content to Ingest

**Source**: `/Users/xavi_court/Downloads/RAG Files.zip`

| File | Type | Fund |
|------|------|------|
| BTG TIG OEF LP REPORT 09_25.pdf | Quarterly Report | BTG Timberland |
| CIM Enterprise Loan Fund LP - Q2 2025.pdf | Quarterly Update | CIM |
| BXINFRA_Pitchbook__Q1_2025.pdf | Pitchbook | Blackstone Infra |
| Ares Core Infrastructure - Fact Sheet.PDF | Fact Sheet | Ares |
| Ares Core Infrastructure - Presentation.PDF | Presentation | Ares |
| Community EM Credit Fund - Q2 2025.pdf | Quarterly Update | Community EM |
| Galvanize Global Equities Q4_2025.pdf | Presentation | Galvanize |
| Generation IM Global Equity Factsheet.pdf | Fact Sheet | Generation |
| Generation IM Holdings October 2025.XLSX | Holdings | Generation |
| TCI Fund Presentation - October 2025.pdf | Presentation | TCI |
| TCI Monthly Exposure Report.xlsx | Exposure Data | TCI |
| ValueAct Due Diligence June 2025.pdf | Due Diligence | ValueAct |
| ValueAct Public Position Summary.pdf | Holdings | ValueAct |
| ValueAct Quarterly Letter - 2025-2Q.pdf | Quarterly Letter | ValueAct |
| Wellington Global Stewards Review.pdf | Review | Wellington |
| Wellington Global Stewards Presentation.pdf | Presentation | Wellington |
| + 6 more files | Various | Various |

**Total**: 22 files, ~33MB

---

*Session Date: 2026-01-14*
*Duration: ~2 hours*
