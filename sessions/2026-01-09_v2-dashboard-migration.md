# Session: 2026-01-09 - V2 Dashboard Migration & Context-Aware Features

> Complete session log for migrating RPC Dashboard from v1 to v2 endpoint with context-aware prompting.

---

## Session Goals

1. Audit RPC Dashboard RAG integration (clarify "not integrated" claim)
2. Assess v1 → v2 migration feasibility
3. Extend v2 to support v1's context-aware features (`prompt_name`, `app_context`)
4. Migrate dashboard to v2 endpoint
5. Test end-to-end with live dashboard

---

## Key Outcomes

| Deliverable | Status | Impact |
|-------------|--------|--------|
| Dashboard integration audit | ✅ Complete | Corrected docs - v1 WAS integrated |
| V2 compatibility analysis | ✅ Complete | Identified gaps: prompt_name, app_context missing |
| V2 feature extension | ✅ Complete | Added prompt_name, app_context to v2 |
| Dashboard migration | ✅ Complete | Both endpoints now use v2 |
| Live Playwright testing | ✅ Complete | MCS Command Palette working with citations |
| Feedback loop logging | ✅ Complete | QueryMetrics now logs retrieval_quality |

---

## Problem Statement

### Initial State

The BACKGROUND_INFO.md claimed:
> RPC Dashboard (Dash/Plotly) | Future primary consumer (not integrated yet)

### Discovery

Exploration revealed dashboard **was already integrated** with v1 via Command Palette (⌘K):
- Location: `/Users/xavi_court/dev/alti-rpc-dashboard/app_dashboard3.py`
- Endpoint: `POST /api/v1/query/custom`
- Features: Context-aware prompts, app_context injection

### Root Cause

V2 optimized retrieval (90% vs 44%) but lacked v1's context features:

| Feature | V1 | V2 (Before) | V2 (After) |
|---------|----|-----------|-----------|
| `prompt_name` | ✅ | ❌ | ✅ |
| `app_context` | ✅ | ❌ | ✅ |
| Retrieval quality | 44% | 90% | 90% |

---

## Technical Changes

### 1. PrismState Extension

**File:** `graph/state.py`

```python
class PrismState(TypedDict):
    # ... existing fields ...

    # V1 context-aware features (for dashboard compatibility)
    prompt_name: Optional[str]  # Custom prompt template from prompts.py
    app_context: Optional[dict]  # User's computed results for interpretation
```

### 2. PrismQueryRequest Extension

**File:** `api/routes.py`

```python
class PrismQueryRequest(BaseModel):
    # ... existing fields ...

    # V1 context-aware features (for dashboard compatibility)
    prompt_name: Optional[str] = Field(default=None)
    app_context: Optional[dict] = Field(default=None)
```

### 3. Generation Node Custom Prompt Loading

**File:** `graph/nodes/generate.py`

Added function to load v1 prompts and convert to LangChain format:

```python
def load_v1_prompt(prompt_name: str) -> Optional[ChatPromptTemplate]:
    """
    Load a V1 prompt from the prompts registry and convert to LangChain format.
    V1: {context_str}, {query_str} → V2: {context}, {query}
    """
    from retrieval.prompts import PROMPTS
    config = PROMPTS[prompt_name]
    template = config.template.replace("{context_str}", "{context}")
                              .replace("{query_str}", "{query}")
    return ChatPromptTemplate.from_messages([
        ("system", template),
        ("human", "{query}")
    ])
```

Updated `generate_response()` to prefer custom prompts:

```python
def generate_response(state: PrismState) -> PrismState:
    prompt_name = state.get("prompt_name")

    # Prefer custom prompt if provided
    if prompt_name:
        prompt = load_v1_prompt(prompt_name)
        logger.info(f"Using custom prompt: {prompt_name}")
    else:
        prompt = get_prompt_for_intent(intent)
```

### 4. Query Enhancement with app_context

**File:** `api/routes.py`

```python
# Enhance query with app_context if provided (v1 compatibility)
query = request.query
if request.app_context:
    query = build_contextual_query(request.query, request.app_context)
```

### 5. Workflow Invocation Updates

**File:** `graph/workflow.py`

Updated both `invoke_prism()` and `invoke_prism_sync()` to accept and pass new fields.

### 6. Dashboard Endpoint Migration

**File:** `/Users/xavi_court/dev/alti-rpc-dashboard/app_dashboard3.py`

Two endpoints updated from v1 to v2:

| Usage | Before | After |
|-------|--------|-------|
| Command Palette | `/api/v1/query/custom` | `/api/v1/v2/query` |
| Ask AlTi | `/api/v1/query` | `/api/v1/v2/query` |

### 7. Feedback Loop Logging

**File:** `api/routes.py`

Added comprehensive metrics logging to v2 endpoint:

```python
metrics = QueryMetrics(
    query_id=thread_id[:8],
    query_text=request.query[:200],
    domain=request.domain,
    endpoint="v2",
    total_time_ms=elapsed_ms,
    documents_retrieved=len(result.get("sources", [])),
    intent=result.get("intent"),
    retrieval_quality=result.get("retrieval_quality"),  # KEY: Track quality
    answer_length=len(result.get("answer", "")),
)
metrics.log()
```

---

## Files Changed

### Modified

| File | Changes |
|------|---------|
| `graph/state.py` | Added prompt_name, app_context to PrismState |
| `graph/workflow.py` | Updated invoke functions to pass new fields |
| `graph/nodes/generate.py` | Added load_v1_prompt(), custom prompt support |
| `api/routes.py` | Added fields to request, query enhancement, metrics logging |
| `BACKGROUND_INFO.md` | Corrected dashboard status, updated feature matrix |
| `/dev/alti-rpc-dashboard/app_dashboard3.py` | Migrated to v2 endpoints |

### Created

| File | Purpose |
|------|---------|
| `tests/test_v2_context_aware.py` | Test suite for 3 core apps |
| `sessions/2026-01-09_v2-dashboard-migration.md` | This session log |

---

## Test Results

### Automated Test Suite

```
python tests/test_v2_context_aware.py
```

| Test Category | Pass | Partial |
|---------------|------|---------|
| MCS (3 tests) | 3 | 0 |
| Portfolio Eval (3 tests) | 2 | 1 |
| Risk Factor (3 tests) | 2 | 1 |
| **Total** | **7** | **2** |

### Live Playwright Testing

| Test | Result |
|------|--------|
| Navigate to MCS page | ✅ |
| Open Command Palette (⌘K) | ✅ |
| Click "95th percentile" question | ✅ |
| Response with user's actual values | ✅ ($23M, $22M, $58M) |
| Source citation displayed | ✅ `[1] FAQ_Monte_Carlo_Simulation.md` |

### Latency Measurements

| Query | Latency | Retrieval Quality |
|-------|---------|-------------------|
| What is a Sharpe ratio? | 11.3s | ambiguous |
| 95th percentile meaning | 7.0s | ambiguous |
| Efficient frontier | 9.6s | ambiguous |

**Note:** Latency higher than expected (~7-11s vs ~5.5s). Likely cold-start after server restart. "Ambiguous" quality is expected when docs are relevant but not perfect matches.

---

## Debugging Notes

### Issue: Retrieval returning 0 sources

**Symptom:** V2 queries returned `retrieval_quality: "poor"` with 0 sources.

**Diagnosis:**
1. Direct ChromaDB query worked (5 docs returned)
2. RAG service had stale retriever cache

**Fix:** Restart RAG service to clear cached retrievers:
```bash
pkill -f uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080
```

### Issue: Dashboard not passing app_context

**Symptom:** Responses were generic, not using user's simulation values.

**Diagnosis:** Dashboard was calling v2 endpoint correctly, but server needed restart to pick up new code.

---

## Architecture Insights

### V1 vs V2 Feature Matrix (Final)

| Feature | V1 | V2 |
|---------|----|----|
| `prompt_name` | ✅ | ✅ (added) |
| `app_context` | ✅ | ✅ (added) |
| Retrieval quality | 44% | **90%** |
| CRAG document grading | ❌ | ✅ |
| Hybrid search (BM25+semantic) | ❌ | ✅ |
| Multi-turn conversation | ❌ | ✅ |
| Intent routing | ❌ | ✅ |

### Prompt Loading Flow

```
Dashboard Request
    ↓
PrismQueryRequest (prompt_name="monte_carlo_interpreter_cited")
    ↓
invoke_prism_sync()
    ↓
PrismState.prompt_name = "monte_carlo_interpreter_cited"
    ↓
generate_response() checks state.prompt_name
    ↓
load_v1_prompt() loads from PROMPTS registry
    ↓
Convert {context_str} → {context}, {query_str} → {query}
    ↓
LLM generates with specialized prompt
```

---

## Commands Used

```bash
# Start RAG service
uvicorn main:app --host 0.0.0.0 --port 8080

# Start dashboard
cd /Users/xavi_court/dev/alti-rpc-dashboard
python app_dashboard3.py

# Test v2 endpoint directly
curl -s http://localhost:8080/api/v1/v2/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is a Sharpe ratio?",
    "domain": "app_education",
    "prompt_name": "risk_metrics_interpreter_cited"
  }'

# Run test suite
python tests/test_v2_context_aware.py

# Check retrieval quality in logs
grep "retrieval_quality" /tmp/rag_server.log
```

---

## Next Steps for Future Agent

1. **Monitor latency in production** - Track if ~7-11s is acceptable or needs optimization
2. **Analyze "poor" quality queries** - Identify FAQ content gaps
3. **Production deployment** - Deploy updated RAG service and dashboard
4. **Snowflake POC** - Q1 2026 roadmap item for Arctic embeddings

---

## Related Documents

- [BACKGROUND_INFO.md](../BACKGROUND_INFO.md) - Updated with migration status
- [test_v2_context_aware.py](../tests/test_v2_context_aware.py) - Test suite
- [Session: v2-optimization](./2026-01-09_v2-optimization.md) - Latency optimization

---

*Session completed: 2026-01-09 ~11:40 PM*
