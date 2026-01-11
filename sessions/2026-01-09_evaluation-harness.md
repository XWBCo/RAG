# Session: 2026-01-09 - Evaluation Harness & v1 vs v2 Comparison

> Complete session log for agent handoff. Covers evaluation harness creation, v2 bug fixes, and strategic findings.

---

## Session Goal

Build systematic evaluation tooling to measure RAG quality, compare v1 (basic) vs v2 (LangGraph) endpoints, and track improvements over time.

---

## Key Outcomes

| Deliverable | Status | Impact |
|-------------|--------|--------|
| Evaluation harness CLI | ✅ Complete | Enables systematic RAG testing |
| v2 score extraction fix | ✅ Complete | v2 now reports accurate scores |
| v2 domain support fix | ✅ Complete | v2 works with all collections |
| Structured logging | ✅ Complete | JSON metrics on every query |
| v1 vs v2 comparison | ✅ Complete | Data-driven endpoint decision |

---

## Strategic Finding: v1 vs v2 Trade-off

**The core question answered:** Is LangGraph (v2) worth the complexity?

### Comparison Results (After Fixes)

| Metric | v1 (Basic) | v2 (LangGraph) | Difference |
|--------|------------|----------------|------------|
| Retrieval Score (app_education) | 44.0% | 90.0% | **+46%** |
| Retrieval Score (investments) | 46.4% | 77.3% | **+31%** |
| Topic Coverage | 71.3% | 71.3% | Same |
| Latency | ~4s | ~24s | **6x slower** |
| Grade Distribution | 0🟢/7🟡/2🔴 | 9🟢/0🟡/0🔴 | All good |

### Recommendation

| Use Case | Recommended Endpoint | Reason |
|----------|---------------------|--------|
| Real-time chat | **v1** | 4s latency acceptable for UX |
| Quality-critical queries | **v2** | 90% retrieval worth the wait |
| Batch processing | **v2** | Latency doesn't matter |
| Demo/testing | **v2** | Best quality for impressions |

### Why v2 is Slower

The 6x latency comes from **CRAG document grading**:
1. Retrieve 10 documents
2. LLM call for each document to assess relevance (~1-2s each)
3. Rerank remaining documents
4. Generate response

**Optimization opportunity:** Run grading calls in parallel, or use smaller model for grading.

---

## Evaluation Harness Details

### Directory Structure

```
eval/
├── __init__.py       # Module exports
├── __main__.py       # python -m eval entry point
├── cli.py            # Click CLI with commands
├── runner.py         # Query execution against endpoints
├── scoring.py        # Retrieval grading, topic matching
├── models.py         # Data models (QueryResult, ScoredResult)
├── queries.yaml      # 44 test queries
└── reports/          # JSON output directory
```

### CLI Commands

```bash
# Run evaluation against v1
python -m eval.cli run --endpoint v1

# Run against v2
python -m eval.cli run --endpoint v2

# Filter by tags
python -m eval.cli run --endpoint v1 --tags monte_carlo

# Compare v1 vs v2
python -m eval.cli compare

# List available tags
python -m eval.cli list-tags

# Check service health
python -m eval.cli health
```

### Query Categories (44 total)

| Category | Count | Tags |
|----------|-------|------|
| Monte Carlo | 10 | `monte_carlo`, `interpretation` |
| Risk Analytics | 12 | `risk_analytics`, `interpretation` |
| Portfolio Evaluation | 8 | `portfolio_eval`, `interpretation` |
| Investments Domain | 6 | `investments`, `v2_test` |
| Edge Cases | 5 | `edge_case` |
| General | 3 | `general` |

### Scoring Logic

**Retrieval Grading:**
- 🟢 Good: 60%+ average retrieval score
- 🟡 Fair: 40-60%
- 🔴 Poor: <40%

**Topic Coverage:** Fuzzy matching of expected concepts in answer with synonym support.

### Sample Output

```
============================================================
Evaluation Results
============================================================

Endpoint: V1
Queries:  9
Duration: 45.8s

Score Distribution:
  🟢 60%+ (good):    0 (  0.0%)
  🟡 40-60% (fair):   7 ( 77.8%)
  🔴 <40% (poor):    2 ( 22.2%)

Averages:
  Retrieval Score:  44.0% (top source: 52.1%)
  Topic Coverage:   71.3%
  Latency:          5093ms
```

---

## Bugs Found & Fixed

### Bug 1: v2 Score Extraction

**Symptom:** v2 showed 0% retrieval scores in comparison.

**Root Cause:** v2 sources used `relevance` key, runner looked for `relevance_score`.

**Fix:** `eval/runner.py` - Handle both formats:
```python
score = src.get("relevance_score") or src.get("relevance") or 0.0
```

### Bug 2: v2 Domain Not Passed

**Symptom:** v2 always queried `alti_investments` regardless of domain parameter.

**Root Cause:**
1. `PrismState` didn't have `domain` field
2. `invoke_prism_sync()` didn't accept domain parameter
3. Retriever hardcoded `collection_name="alti_investments"`

**Fix:** Chain of changes:
1. `graph/state.py` - Added `domain: str` to PrismState
2. `graph/state.py` - Added domain to `get_initial_state()`
3. `graph/workflow.py` - Added domain param to `invoke_prism()` and `invoke_prism_sync()`
4. `graph/nodes/retrieve.py` - Use domain from state for collection lookup
5. `api/routes.py` - Pass `request.domain` to invoke_prism_sync()

### Bug 3: Score Discrepancy (44% vs 62%)

**Symptom:** Evaluation showed 44% average, dev log documented 62%.

**Root Cause:** Measurement methodology difference:
- Dev log: Measured **top score** per query
- Eval harness: Measured **average of top 5**

**Resolution:** Added `avg_top_retrieval_score` to metrics for comparison.

---

## Structured Logging

### New Module: `utils/logging.py`

Provides `QueryMetrics` dataclass for structured JSON logging:

```python
@dataclass
class QueryMetrics:
    query_id: str
    query_text: str
    domain: str
    endpoint: str
    timestamp: str
    total_time_ms: float
    retrieval_time_ms: float
    llm_time_ms: float
    documents_retrieved: int
    top_score: float
    avg_score: float
    top_sources: list
    answer_length: int
    error: Optional[str]
```

### Sample Log Output

```json
{
  "query_id": "9bba4b5b",
  "query_text": "What is tracking error?",
  "domain": "app_education",
  "endpoint": "v1",
  "total_time_ms": 1968.24,
  "documents_retrieved": 3,
  "top_score": 0.552,
  "avg_score": 0.457,
  "top_sources": [
    {"file": "FAQ_Risk_Analytics.md", "score": 0.552}
  ],
  "answer_length": 141
}
```

---

## File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `eval/__init__.py` | Module exports |
| `eval/__main__.py` | Entry point for `python -m eval` |
| `eval/cli.py` | CLI commands (run, compare, list-tags, health) |
| `eval/runner.py` | Query execution, HTTP client |
| `eval/scoring.py` | Grading logic, metrics calculation |
| `eval/models.py` | Data models |
| `eval/queries.yaml` | 44 test queries |
| `utils/__init__.py` | Utils module init |
| `utils/logging.py` | QueryMetrics, structured logging |

### Modified Files

| File | Changes |
|------|---------|
| `requirements.txt` | Added click, pyyaml |
| `api/routes.py` | Structured logging, domain passthrough to v2 |
| `graph/state.py` | Added domain field to PrismState |
| `graph/workflow.py` | Accept domain in invoke_prism functions |
| `graph/nodes/retrieve.py` | Use domain from state for collection lookup |
| `DEVELOPMENT_LOG.md` | Session documentation |
| `BACKGROUND_INFO.md` | Updated completed items |

---

## Dependencies Added

```
# requirements.txt additions
click>=8.1.0             # CLI framework
pyyaml>=6.0.0            # YAML parsing for test queries
```

---

## Testing Commands Used

```bash
# Start RAG service on alternate port
PORT=8001 python -c "
import uvicorn
from main import app
uvicorn.run(app, host='0.0.0.0', port=8001)
"

# Check service health
curl -s http://localhost:8001/api/v1/health

# Test v1 query
curl -s "http://localhost:8001/api/v1/query/custom" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is tracking error?", "domain": "app_education"}'

# Test v2 query
curl -s "http://localhost:8001/api/v1/v2/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is tracking error?", "domain": "app_education"}'

# Run evaluation
python -m eval.cli run --endpoint v1 --tags core --base-url http://localhost:8001

# Run comparison
python -m eval.cli compare --base-url http://localhost:8001
```

---

## Collection Stats Reference

```
alti_investments (456 documents):
  - fund_model_allocation: 220 (48%)
  - fund_profile: 156 (34%)
  - cma_data: 54 (12%)
  - fund_universe_summary: 12 (3%)
  - pdf_document: 11 (2%)
  - model_overview: 3 (1%)

app_education_docs (74 documents):
  - faq_section: 39
  - pdf_document: 21
  - presentation_slide: 14
```

---

## Next Steps for Future Agent

1. **Optimize v2 latency** - Run CRAG grading in parallel
2. **Add more test queries** - As gaps are discovered in production
3. **Consider hybrid approach** - v1 for speed, fall back to v2 for low-confidence results
4. **Production monitoring** - Use structured logging for observability

---

## Report Locations

All evaluation reports saved to:
```
eval/reports/
├── 2026-01-09_193254_v1_core.json
├── 2026-01-09_195654_comparison.json
├── 2026-01-09_200230_comparison.json
├── 2026-01-09_213329_v1_core.json
├── 2026-01-09_214305_comparison.json
```

---

*Session completed: 2026-01-09*
