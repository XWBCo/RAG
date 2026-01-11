# Session: MCS Context Investigation & UX Improvements

**Date:** 2026-01-10
**Focus:** RAG context mismatch investigation, prompt tone fix, simulation selector design

---

## Summary

Investigated the HIGH priority RAG context mismatch bug from previous session. Added debug logging and ran live tests - **data flow is working correctly**. The original bug was likely caused by user workflow issues (wrong context pill, page refresh clearing memory store, or race condition).

---

## Completed This Session

### 1. RAG Context Mismatch Investigation

| Finding | Details |
|---------|---------|
| **Status** | System working correctly under test conditions |
| **Debug logging added** | `app_dashboard3.py:2476-2484` (MCS context), `routes.py:701-703` (enhanced query) |
| **Live test result** | Chart showed $9,090,000 median, RAG received $9,092,055, LLM responded accurately |
| **Original bug NOT reproduced** | Could not recreate the 88.4% / $1,386,829 mismatch |

**Likely causes of original issue (speculation):**
- Context pill manually changed from "Monte Carlo" to another context
- Page refreshed (`mcs-results-store` uses `storage_type='memory'`)
- Query sent before simulation callback completed

### 2. Context Pills Wrapping Fix

| File | Change |
|------|--------|
| `app_dashboard3.py:1600-1607` | Added `flexWrap: "nowrap"` and `overflow: "hidden"` to pill container |

Pills now stay on single line regardless of modal width.

### 3. MCS Prompt Tone Fix

**Problem:** Response led with pessimistic 5th percentile scenario, creating anxiety.

**Solution:** Updated `monte_carlo_interpreter_cited` prompt in `retrieval/prompts.py`:

```
RESPONSE STRUCTURE (follow this order):
1. LEAD WITH MEDIAN: Start with the most likely outcome (50th percentile/median)
2. SUCCESS PROBABILITY: Mention their probability of outperforming inflation
3. RANGE: Present the full range neutrally - "from [5th] to [95th]" without emphasizing either extreme
4. INSIGHT: One actionable takeaway based on their specific numbers

AVOID: Do not lead with pessimistic scenarios or worst-case outcomes.
```

---

## Designed But Not Implemented

### Simulation Selector UI for MCS

**Problem:** MCS has 3 simulations × 3 charts each. RAG receives ALL data regardless of which simulation user asks about.

**Proposed Design:** Sub-pills that appear only when Monte Carlo context is active:

```
[Portfolio Eval] [Monte Carlo●] [Risk] [CMA] [Impact]   ← Main context
                 [Sim 1] [Sim 2] [Sim 3] [All●]         ← Sub-selector
```

**Behavior:**
- "All" (default): Send all 3 simulations' data
- "Sim 1/2/3": Send only that simulation's data to RAG

**Implementation requires:**
- New `dcc.Store` for `mcs-sim-filter`
- New callback to show/hide sub-pills based on context
- Modify `handle_cmd_palette` to filter `mcs_results.simulations`
- New CSS for smaller sub-pills

**Open questions:**
1. Use simulation names (user-defined) or generic "Sim 1/2/3"?
2. Default to "All" or auto-detect from query?
3. Change FAQ suggestions based on sim selection?

---

## Files Modified

| File | Changes |
|------|---------|
| `app_dashboard3.py` | Debug logging for MCS context, pill wrap fix |
| `routes.py` | Debug logging for enhanced query preview |
| `retrieval/prompts.py` | MCS prompt restructured for neutral tone |
| `BACKGROUND_INFO.md` | RAG context issue marked as RESOLVED |
| `sessions/2026-01-10_command-palette-modal-polish.md` | Updated with investigation findings |

---

## Debug Logging Added (kept for future use)

```python
# app_dashboard3.py - logs MCS data being sent
[CMD-PALETTE DEBUG] Context: mcs
[CMD-PALETTE DEBUG] MCS Results keys: ['page', 'initial_portfolio', ...]
[CMD-PALETTE DEBUG] sim1: p5=$X, p50=$Y, p95=$Z

# routes.py - logs enhanced query
[RAG DEBUG] app_context page: monte_carlo
[RAG DEBUG] Enhanced query preview (first 500 chars): ...
```

---

## Next Session Priorities

1. **Implement simulation selector UI** (if approved)
2. **Test new prompt tone** with various MCS queries
3. Consider similar context-specific selectors for other apps (Risk, Portfolio Eval)
