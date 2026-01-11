# RAG Service Development Log

> Detailed technical log of development sessions for future agents.

---

## Session: 2026-01-09 - RAG Quality Improvements

### Overview

**Goal**: Improve RAG retrieval quality for the RPC Dashboard's AI assistant features.

**Outcome**: Retrieval scores improved from ~36% to ~62% (+26% average) by adding interpretive FAQ content.

---

## 1. Initial Exploration

### Codebase Structure Discovered

**RAG Service** (`/Users/xavi_court/claude_code/alti-rag-service/`):
- FastAPI backend with LangGraph workflow
- ChromaDB vector store with OpenAI embeddings (`text-embedding-3-small`)
- Dual provider support (Ollama local / OpenAI cloud)
- Multi-domain collections (investments, estate_planning, app_education)

**Key Files**:
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app entry point |
| `api/routes.py` | API endpoints (v1 basic, v2 LangGraph) |
| `retrieval/engine.py` | Query engine with llama_index |
| `ingestion/pipeline.py` | Document ingestion with SentenceSplitter |
| `ingestion/loaders.py` | Custom loaders for PDF, Excel, CSV, PPTX, JSON |
| `graph/workflow.py` | LangGraph agentic RAG workflow |
| `config.py` | Settings via pydantic-settings |

**RPC Dashboard** (`/Users/xavi_court/dev/alti-rpc-dashboard/`):
- Dash/Plotly multi-app dashboard
- Consumes RAG service via HTTP (synchronous requests)
- Main apps: Portfolio Evaluation, Monte Carlo, Risk Analytics, CMA, Clarity AI
- RAG integration in `app_dashboard3.py` lines 2548-2687

### Integration Pattern

Dashboard → RAG Service flow:
```
app_dashboard3.py:query_rag_service()
  → POST /api/v1/query/custom
  → RetrievalEngine.query_with_prompt()
  → ChromaDB semantic search
  → LLM synthesis (gpt-4o-mini or llama3.2)
  → Return answer + sources
```

---

## 2. Strategic Context Gathered

See `BACKGROUND_INFO.md` for full details. Key points:

- **Status**: R&D/exploration phase, not in production
- **Primary consumer**: RPC Dashboard only (Estate Planning is demo)
- **Tech direction**: React migration eventually, focus on RAG core + Dash for now
- **Testing needs**: Query playground, evaluation harness, better logging
- **LangGraph value**: Unknown - haven't compared v1 vs v2

---

## 3. Database Audit

### Collections Found

```
alti_investments (456 docs)
  - Source: Model Archetypes.xlsm (1 file)
  - Types: fund_profile (52), fund_model_allocation (44), fund_universe_summary (4)
  - Priority: critical

app_education_docs (47 docs)
  - Sources: AlTi_Risk_Dashboard_Documentation.pdf, RPC_UseCases.pptx
  - Types: pdf_document (33), presentation_slide (14)
  - Priority: normal
```

### Content Analysis

The PDF documentation covered all apps but was **procedural** (how to use) not **interpretive** (what results mean):

| Content Type | Present? | Example |
|--------------|----------|---------|
| How to use | ✅ | "Click Download Results to export..." |
| Definitions | ✅ | "Tracking Error: Volatility of difference..." |
| Interpretation | ❌ | "When 5th percentile is low, it means..." |
| Advisory | ❌ | "If tracking error > 3%, consider..." |

---

## 4. Retrieval Quality Testing

### Initial Test Results

```python
test_queries = [
    "What does the 5th percentile mean in Monte Carlo?",
    "How do I interpret tracking error?",
    "What is an efficient frontier?",
    "What factors drive portfolio risk?",
]
```

| Query | Score | Assessment |
|-------|-------|------------|
| 5th percentile | 36.3% | 🔴 Too low |
| Tracking error | 35.6% | 🔴 Too low |
| Efficient frontier | 37.1% | 🔴 Too low |
| Portfolio risk | 42.9% | 🔴 Too low |

**Target**: 60-80% for reliable retrieval.

### Root Cause Analysis

1. **Content-query mismatch**: User asks conceptual questions, content is procedural
2. **Chunking issues**: 8/47 chunks cut mid-sentence (17%)
3. **Embedding dimension**: Collection uses OpenAI 1536-dim (not ChromaDB default 384-dim)

---

## 5. Fix Attempt 1: Chunking Improvements

### Changes Made

**config.py**:
```python
# Before
chunk_size: int = 512
chunk_overlap: int = 128

# After
chunk_size: int = 768
chunk_overlap: int = 200
```

**loaders.py** - Added PDF text preprocessor:
```python
def preprocess_pdf_text(text: str) -> str:
    """Clean up PDF-extracted text for better chunking."""
    # Remove page headers (AlTi Tiedemann Global 10)
    text = re.sub(r'AlTi Tiedemann Global\s+\d+\s*\n', '\n', text)

    # Add periods after headers lacking punctuation
    text = re.sub(r'\n(Purpose)\s*\n', r'\n\n\1.\n', text)
    # ... more patterns

    # Merge lines broken mid-sentence
    text = re.sub(r'([a-z,])\n([a-z])', r'\1 \2', text)

    return text
```

### Results

| Metric | Before | After |
|--------|--------|-------|
| Chunks | 47 | 35 |
| Avg size | 981 chars | 1134 chars |
| Mid-sentence cuts | 8 | 7 |

**Retrieval improvement**: Minimal (+0-4%). Chunking wasn't the bottleneck.

---

## 6. Fix Attempt 2: Interpretive FAQ Content (Success)

### Hypothesis

The problem isn't chunking - it's **content type**. Need FAQ-style content that directly answers user questions.

### Implementation

Created 3 markdown FAQ files:

| File | Questions | Topics |
|------|-----------|--------|
| `FAQ_Monte_Carlo_Simulation.md` | 12 | Percentiles, probabilities, withdrawals, assumptions |
| `FAQ_Risk_Analytics.md` | 13 | Tracking error, beta, factors, Sharpe, diversification |
| `FAQ_Portfolio_Evaluation.md` | 14 | Efficient frontier, optimization, constraints, scenarios |

**FAQ format**:
```markdown
## Q: What does the 5th percentile mean in my Monte Carlo simulation?

The 5th percentile represents your **pessimistic but plausible scenario**...

**How to interpret:**
- This is your "bad luck" scenario...

**When to be concerned:**
- 5th percentile falls below minimum acceptable...

**What to discuss with clients:**
- "Even in a pessimistic scenario..."
```

### Loader Added

**loaders.py** - New markdown loader:
```python
def load_markdown_documents(file_path: Path) -> List[Document]:
    """Load markdown docs, split by ## headers."""
    # Splits by ## headers to create logical sections
    # Each Q&A becomes one document
    # Priority: high (0.85)
```

**pipeline.py** - Added `.md` support:
```python
extensions = [..., ".md"]

elif suffix == ".md":
    documents = load_markdown_documents(path)
```

### Results

| Query | Before | After | Change |
|-------|--------|-------|--------|
| 5th percentile | 36.6% | **67.2%** | +30.6% 🟢 |
| Tracking error | 35.6% | **63.3%** | +27.7% 🟢 |
| Efficient frontier | 36.6% | **58.4%** | +21.8% 🟢 |
| Portfolio risk | 46.6% | **58.4%** | +11.8% 🟢 |

**Collection stats after**:
- Total documents: 74 (was 47)
- FAQ sections: 39 (new)
- PDF documents: 21
- Presentation slides: 14

---

## 7. Other Deliverables

### Query Playground UI

Created `/playground` endpoint for interactive RAG testing.

**Files**:
- `static/playground.html` - Self-contained HTML/JS UI
- `main.py` - Added static file serving + redirect

**Features**:
- Query input with example pre-filled
- Endpoint toggle (v1 basic vs v2 LangGraph)
- Domain/mode/top_k/similarity controls
- Response display with metrics and expandable sources
- Health indicator in header
- Keyboard shortcut (Ctrl+Enter)

**Access**: `http://localhost:8000/playground`

### Background Info Document

Created `BACKGROUND_INFO.md` with strategic context from user Q&A.

---

## 8. Errors Encountered & Fixes

### Error 1: ChromaDB Embedding Dimension Mismatch

```
chromadb.errors.InvalidArgumentError: Collection expecting embedding
dimension of 1536, got 384
```

**Cause**: Tried to query with ChromaDB's default embedding (MiniLM, 384-dim) but collection was created with OpenAI (1536-dim).

**Fix**: Use the RAG service's RetrievalEngine which initializes with correct provider.

### Error 2: dotenv Load Failure in Heredoc

```
AssertionError: frame.f_back is not None
```

**Cause**: `python-dotenv`'s `find_dotenv()` doesn't work in heredoc scripts.

**Fix**: Manual env loading:
```python
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"')
```

### Error 3: macOS Missing `timeout` Command

```
command not found: timeout
```

**Cause**: macOS doesn't have GNU `timeout`.

**Fix**: Remove timeout wrapper, use Python's built-in timeout handling.

---

## 9. Technical Notes

### Embedding Configuration

The RAG service supports dual providers:

```python
# config.py
llm_provider: str = "ollama"  # or "openai"

# Ollama (local)
ollama_embedding_model: str = "nomic-embed-text"
ollama_llm_model: str = "llama3.2:3b"

# OpenAI (cloud)
openai_embedding_model: str = "text-embedding-3-small"
openai_llm_model: str = "gpt-4o-mini"
```

**Important**: Collection embeddings must match query embeddings. Can't mix providers for same collection.

### v1 vs v2 Endpoints

- **v1** (`/api/v1/query`): Basic RAG with llama_index
- **v2** (`/api/v1/v2/query`): LangGraph workflow with intent routing, CRAG grading

Note: v2 routes are at `/api/v1/v2/*` due to router mounting. TODO: Clean up to proper `/api/v2/*`.

### Priority Scoring

Documents have priority metadata for retrieval boosting:
```python
priority_scores = {
    "critical": 1.0,  # Model Archetypes
    "high": 0.85,     # FAQ content
    "normal": 0.5,    # Documentation
    "low": 0.3
}

# Boost formula in search:
boosted_score = (0.7 * semantic_score) + (0.3 * priority_score)
```

---

## 10. Next Steps / Future Work

### Immediate
- [ ] Test playground with actual queries
- [ ] Run v1 vs v2 comparison to evaluate LangGraph value
- [ ] Add structured logging for debugging

### Short-term
- [ ] Evaluation harness for batch testing
- [ ] More FAQ content as gaps are discovered
- [ ] Clean up v2 endpoint routing

### Longer-term
- [ ] TypeScript client for React migration
- [ ] Streaming responses in dashboard
- [ ] Production deployment (Docker)

---

## File Changes Summary

| File | Change |
|------|--------|
| `config.py` | Increased chunk_size (512→768), chunk_overlap (128→200) |
| `main.py` | Added static file serving, /playground redirect |
| `ingestion/loaders.py` | Added `preprocess_pdf_text()`, `load_markdown_documents()` |
| `ingestion/pipeline.py` | Added markdown import, .md extension support |
| `static/playground.html` | New - Query playground UI |
| `data/app_education/FAQ_*.md` | New - 3 FAQ documents (39 sections) |
| `BACKGROUND_INFO.md` | New - Strategic context |
| `DEVELOPMENT_LOG.md` | New - This file |

---

## Session: 2026-01-09 - Evaluation Harness

### Goal

Build systematic evaluation tooling to measure RAG quality, compare endpoints, and track improvements over time.

### Deliverables

#### Evaluation Harness CLI

Created `eval/` module with:

| File | Purpose |
|------|---------|
| `cli.py` | CLI interface with run, compare, list-tags commands |
| `runner.py` | Query execution against v1/v2 endpoints |
| `scoring.py` | Retrieval grading, topic matching, metrics |
| `models.py` | Data models for results and reports |
| `queries.yaml` | 38 test queries across 4 categories |

**CLI Commands**:
```bash
# Run evaluation against endpoint
python -m eval.cli run --endpoint v1 --tags core

# Compare v1 vs v2 side-by-side
python -m eval.cli compare

# List available tags
python -m eval.cli list-tags

# Check service health
python -m eval.cli health
```

#### Test Query Suite

38 queries organized by category:

| Category | Queries | Focus |
|----------|---------|-------|
| Monte Carlo | 10 | Percentiles, probability, assumptions |
| Risk Analytics | 12 | Tracking error, beta, Sharpe, factors |
| Portfolio Eval | 8 | Efficient frontier, optimization |
| Edge Cases | 5 | Vague queries, typos, out-of-domain |
| General | 3 | CMA, data updates, exports |

### Scoring Logic

**Retrieval Grading**:
- 🟢 Good: 60%+ average retrieval score
- 🟡 Fair: 40-60%
- 🔴 Poor: <40%

**Topic Coverage**: Checks if expected concepts appear in answer using fuzzy matching with synonym support.

### Sample Output

```
============================================================
Evaluation Results
============================================================

Endpoint: V1
Queries:  9
Duration: 44.7s

Score Distribution:
  🟢 60%+ (good):    0 (  0.0%)
  🟡 40-60% (fair):   7 ( 77.8%)
  🔴 <40% (poor):    2 ( 22.2%)

Averages:
  Retrieval Score:  44.0%
  Topic Coverage:   67.6%
  Latency:          4961ms
```

### Key Findings & Fixes

**Issue 1: v2 score extraction bug**
- v2 sources used `relevance` key, runner looked for `relevance_score`
- Fixed in `eval/runner.py` to handle both formats

**Issue 2: v2 domain parameter not passed**
- v2 was hardcoded to `alti_investments` collection
- Fixed by adding `domain` to PrismState and passing through workflow

**Results after fixes:**

| Query Type | v1 | v2 (Fixed) | Winner |
|------------|-----|------------|--------|
| app_education (core) | 44% | 90% | v2 (+46%) |
| investments (archetype) | 46% | 77% | v2 (+31%) |
| Latency | ~4s | ~24s | v1 (6x faster) |

**Conclusion:** v2 (LangGraph) produces significantly better retrieval quality due to CRAG grading and reranking, but at 6x latency cost. Use v2 for quality-critical queries, v1 for speed.

### File Changes

| File | Change |
|------|--------|
| `eval/__init__.py` | New - Module init |
| `eval/__main__.py` | New - Module entry point |
| `eval/cli.py` | New - CLI commands, added top score display |
| `eval/runner.py` | New - Query execution, fixed v1/v2 format handling |
| `eval/scoring.py` | New - Metrics calculation, added avg_top_retrieval_score |
| `eval/models.py` | New - Data models |
| `eval/queries.yaml` | New - Test suite (44 queries including investments) |
| `eval/reports/` | New - Report output directory |
| `requirements.txt` | Added click, pyyaml |
| `utils/__init__.py` | New - Utils module init |
| `utils/logging.py` | New - Structured logging (QueryMetrics) |
| `api/routes.py` | Added structured logging to custom_query |
| `graph/state.py` | Added `domain` field to PrismState |
| `graph/workflow.py` | Pass `domain` through invoke_prism functions |
| `graph/nodes/retrieve.py` | Use domain from state for collection lookup |

---

*Last updated: 2026-01-09*
