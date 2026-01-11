# Session: 2026-01-10 - RAG Finetuning & Frontend UX Review

> Systematic evaluation, content expansion, bug fixes, and Command Palette UX feedback.

---

## Session Goals

1. Bulk test RAG queries to identify quality gaps
2. Expand test coverage for ClarityAI/ESG metrics
3. Fix identified content gaps
4. Review frontend Command Palette UX
5. Fix any backend issues affecting frontend

---

## Key Outcomes

| Deliverable | Status | Impact |
|-------------|--------|--------|
| ClarityAI FAQ created | ✅ Complete | 18 new ESG metric definitions with calculations |
| Test suite expanded | ✅ Complete | 44 → 62 queries (+41%) |
| Content gaps fixed | ✅ Complete | Max drawdown, Effective N, factor explained |
| Evaluation improved | ✅ Complete | 91.9% → 96.8% pass rate |
| V1 prompt brevity bug fixed | ✅ Complete | Custom prompts now concise |
| UX feedback documented | ✅ Complete | Expand button, response length, etc. |

---

## Technical Changes

### 1. ClarityAI FAQ Content (`data/app_education/FAQ_ClarityAI_ESG.md`)

**Created comprehensive FAQ** covering all Clarity AI metrics from the PDF guide:

| Category | Metrics Covered |
|----------|-----------------|
| **Climate** | Temp Rating Scope 1+2/3, Net Zero Target, Financed Intensity, Carbon Intensity |
| **Environment** | Environmental Score, Water Recycled Ratio, Waste Recycling Ratio |
| **Social** | Social Score, Gender Pay Gap, Female Board Members, Diversity Targets |
| **Governance** | Governance Score, Board Independence, Anti-Bribery Score |
| **General** | Score interpretation, Framework alignment (PCAF, SFDR, SBTi), Data limitations |

**Includes example calculations:**
```
Investment = $5M | Company EV = $250M | Emissions = 50,000 tCO₂e
Ownership share = $5M / $250M = 2%
Financed emissions = 2% × 50,000 = 1,000 tCO₂e
Financed Intensity = 1,000 / 5 = 200 tCO₂e/$M invested
```

### 2. Risk Analytics FAQ Updates (`data/app_education/FAQ_Risk_Analytics.md`)

Added 3 missing FAQ sections:

| Topic | Content |
|-------|---------|
| **Maximum Drawdown** | Definition, interpretation benchmarks (-10%, -20-30%, -40%+), client conversation tips |
| **Effective N** | Formula, interpretation, concentration benchmarks (>20, 10-20, <10) |
| **Factor Explained %** | 80-90% factor-driven vs 60-80% mixed vs <60% idiosyncratic |

### 3. Test Suite Expansion (`eval/queries.yaml`)

| Category | Before | After |
|----------|--------|-------|
| Monte Carlo | 10 | 10 |
| Risk Analytics | 12 | 12 |
| Portfolio Eval | 8 | 8 |
| General | 4 | 4 |
| Edge Cases | 5 | 5 |
| Investments | 6 | 6 |
| **ClarityAI** | **0** | **18** |
| **Total** | **44** | **62** |

### 4. V1 Prompt Brevity Fix (`graph/nodes/generate.py`)

**Bug:** When `prompt_name` was provided (e.g., `monte_carlo_interpreter_cited`), v2 loaded the v1 prompt without brevity constraints, producing verbose 4-5 paragraph responses.

**Fix:** Modified `load_v1_prompt()` to inject brevity constraints:

```python
brevity_suffix = """

RESPONSE LENGTH:
- Keep your response to 2-4 sentences MAX.
- Be direct and specific - no preamble, no filler.
- Include key numbers/percentages from the context.
- Users can ask follow-up questions for more detail."""

system_content = system_content.rstrip() + brevity_suffix
```

**Result:**
| Scenario | Before | After |
|----------|--------|-------|
| API without app_context | 41 words | 43 words |
| API with app_context | ~300 words | ~155 words |
| Frontend display | 4-5 paragraphs | 3 paragraphs |

---

## Evaluation Results

### Before Content Fixes
```
Pass Rate: 91.9% (57/62)
Avg Retrieval: 82.2%
Failures: 5
```

### After Content Fixes
```
Pass Rate: 96.8% (60/62)
Avg Retrieval: 86.7%
Failures: 2
```

### Remaining Failures

| Query | Status | Reason |
|-------|--------|--------|
| `edge_out_of_domain` | Expected | "What's the weather?" should fail gracefully |
| `inv_us_vs_international` | Content gap | Fund comparison content missing in investments domain |

**Effective pass rate: 98.4%** (61/62 excluding expected failure)

---

## Frontend UX Review: Command Palette (⌘K)

### What Works Well

| Feature | Assessment |
|---------|------------|
| ⌘K trigger | Familiar pattern (Spotlight, VS Code) |
| Context auto-detection | "Monte Carlo" auto-selected on /mcs |
| Quick Questions | Pre-populated, context-aware |
| Context-aware values | Uses actual simulation values ($22M, etc.) |
| Keyboard hints | ↑↓ navigate, ↵ select, esc close |
| Source citation | Now visible with fix |

### Issues Identified

| Issue | Severity | Recommendation |
|-------|----------|----------------|
| **Expand button pointless** | Low | Only adds ~10% width, content still truncated. Remove or make full-screen. |
| **Response still verbose** | Medium | Even with fix, 3 paragraphs with app_context. Consider even stricter brevity. |
| **Modal obscures context** | Medium | Consider right-side slide-over panel instead |
| **No follow-up capability** | Low | One-shot interaction, can't continue conversation |
| **No scroll indicator** | Low | Content cut off with no visual cue |

### Expand Button Analysis

| State | Width | Content Visible | Value |
|-------|-------|-----------------|-------|
| Collapsed | ~35% | 2 paragraphs | - |
| Expanded | ~45% | 2.5 paragraphs | Marginal |

**Verdict:** Remove expand button or replace with meaningful full-screen/panel option.

---

## Files Changed

### Created

| File | Purpose |
|------|---------|
| `data/app_education/FAQ_ClarityAI_ESG.md` | Clarity AI ESG metrics FAQ |
| `sessions/2026-01-10_rag-finetuning-and-ux-review.md` | This session log |

### Modified

| File | Changes |
|------|---------|
| `data/app_education/FAQ_Risk_Analytics.md` | Added max drawdown, Effective N, factor explained |
| `eval/queries.yaml` | Added 18 ClarityAI test queries |
| `graph/nodes/generate.py` | Fixed V1 prompt brevity injection |

---

## Collection Stats

| Domain | Before | After |
|--------|--------|-------|
| `app_education_docs` | 74 → 86 → 102 | +28 docs |

---

## Debugging Notes

### Retriever Cache Issue (Confirmed)

After ingesting new content, server restart is REQUIRED:
```bash
pkill -f uvicorn
uvicorn main:app --host 0.0.0.0 --port 8080
```

Without restart:
- ClarityAI queries: 32.1% retrieval, 61% failure

After restart:
- ClarityAI queries: 89.9% retrieval, 0% failure

### V1 Prompt Verbosity Root Cause

Custom prompts loaded via `load_v1_prompt()` bypassed V2's concise prompt templates. The V2 intent-based prompts (ARCHETYPE_PROMPT, CLARITY_PROMPT, etc.) all have "2-4 sentences MAX" but V1 prompts did not.

---

## Recommended Next Steps

### Priority 1: Quick Wins
1. **Remove expand button** from Command Palette (or replace with full-screen)
2. **Stricter brevity** for app_context responses - currently ~155 words, target ~80
3. **Add scroll indicator** to modal when content is truncated

### Priority 2: Content
4. **Add US vs International fund comparison** content to investments domain (last failing query)
5. **Monitor retrieval_quality** in production logs to identify real-world failures

### Priority 3: UX Enhancements
6. **Consider slide-over panel** instead of centered modal
7. **Add follow-up capability** - "Ask more about this" button
8. **Show source at top** instead of bottom

### Priority 4: Production
9. **Deploy to remote Windows machine** when ready
10. **Set up periodic re-evaluation** schedule

---

## Commands Used

```bash
# Run ClarityAI-specific evaluation
python -m eval.cli run -e v2 -t clarity_ai -u http://localhost:8080

# Run full evaluation
python -m eval.cli run -e v2 -u http://localhost:8080

# Ingest new content
curl -X POST http://localhost:8080/api/v1/ingest/file \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/path/to/file.md", "domain": "app_education"}'

# Test V2 with custom prompt
curl -X POST http://localhost:8080/api/v1/v2/query \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "domain": "app_education", "prompt_name": "monte_carlo_interpreter_cited"}'
```

---

## Screenshots

| Screenshot | Description |
|------------|-------------|
| `command-palette-expanded.png` | Expand button - before assessment |
| `command-palette-collapsed.png` | Collapsed state comparison |
| `command-palette-after-fix.png` | After brevity fix - 3 paragraphs |

Location: `/Users/xavi_court/.playwright-mcp/`

---

## Related Documents

- [BACKGROUND_INFO.md](../BACKGROUND_INFO.md) - Updated with session outcomes
- [FAQ_ClarityAI_ESG.md](../data/app_education/FAQ_ClarityAI_ESG.md) - New content
- [2026-01-09_v2-dashboard-migration.md](./2026-01-09_v2-dashboard-migration.md) - Previous session

---

*Session completed: 2026-01-10 ~12:00 PM*
