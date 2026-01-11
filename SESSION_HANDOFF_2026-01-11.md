# Session Handoff - AlTi Platform Consolidation
## Date: 2026-01-11

---

## Executive Summary

This session focused on consolidating the dev and prod RPC dashboards, preparing the RAG service for Windows production deployment, and creating a migration manifest for the AI features.

**Key Principle Established**: Surgical file changes only - ADD, APPEND, INSERT, MODIFY specific code blocks rather than replacing entire files.

---

## Codebases Involved

| Codebase | Location | Purpose |
|----------|----------|---------|
| **Dev Dashboard** | `/Users/xavi_court/dev/alti-rpc-dashboard/` | Development version with AI features |
| **Prod Dashboard** | `/Users/xavi_court/Downloads/Risk & PC App 2/` | Production version on Windows Server |
| **RAG Service** | `/Users/xavi_court/claude_code/alti-rag-service/` | AI backend for Q&A |

---

## Completed Workstreams

### ✅ Workstream 1: Login Background Update

**What was done:**
- Copied architectural image (`AlTi Architectural Image_07.jpg`) to both dev and prod assets as `login-background.jpg`
- Updated `login_layout` container style with `backgroundImage`, `backgroundSize: cover`, etc.
- Added frosted glass effect to login card (`backdropFilter: blur(8px)`, semi-transparent white)
- Increased card shadow for contrast
- **Removed Dev Bypass button** from dev version

**Files changed:**
- `dev/assets/login-background.jpg` (added)
- `prod/assets/login-background.jpg` (added)
- `dev/app_dashboard3.py` lines ~1235-1257 (login layout styles)
- `prod/app_dashboard3.py` lines ~529-550 (login layout styles)

---

### ✅ Workstream 2: RAG Feedback API

**What was done:**
- Created complete feedback system for collecting thumbs up/down on RAG responses
- Added `query_id` to v2 query responses for correlation

**Files created:**
```
alti-rag-service/
├── models/
│   ├── __init__.py
│   └── feedback.py          # FeedbackSubmission, FeedbackRecord, FeedbackStats
├── storage/
│   ├── __init__.py
│   └── feedback.py          # JSONFileStorage class
└── api/
    └── feedback.py          # POST/GET endpoints
```

**Files modified:**
- `api/__init__.py` - Added `feedback_router` export
- `main.py` - Mounted feedback router at `/api/v1/feedback/*`
- `api/routes.py` - Added `query_id` field to `PrismQueryResponse` model

**API Endpoints:**
```
POST   /api/v1/feedback              # Submit feedback
GET    /api/v1/feedback/stats        # Aggregated statistics
GET    /api/v1/feedback/by-query/{id}  # Feedback for specific query
GET    /api/v1/feedback/by-user?email=  # Feedback by user
```

**Storage:** `logs/feedback.jsonl` (JSON Lines format, correlates with `metrics.jsonl`)

---

### ✅ FAQ Questions Updated (Part of Workstream 2)

**Location:** `dev/app_dashboard3.py` lines ~938-972 (`CONTEXT_FAQS` dict)

**Changed from basic to technical wealth management questions:**

| Context | Old (Basic) | New (Technical) |
|---------|-------------|-----------------|
| **all** | "What questions can I ask here?" | "How should I interpret my Sharpe ratio relative to the benchmark?" |
| **all** | "How do I interpret my risk-adjusted returns?" | "What's driving the dispersion between my risk buckets?" |
| **all** | "What metrics matter most for my portfolio?" | "Which asset classes are contributing most to tracking error?" |
| **mcs** | "What does my 95th percentile outcome mean?" | "What's the sensitivity of my success probability to sequence of returns risk?" |
| **mcs** | "What determines my success probability?" | "How does my spending rate impact the left-tail outcomes?" |
| **mcs** | "How can I improve my projected outcomes?" | "What withdrawal rate keeps me above the 10th percentile floor?" |
| **risk** | "What does my VaR number mean?" | "How does my ex-ante VaR compare to realized volatility?" |
| **risk** | "How is maximum drawdown calculated?" | "What's my marginal contribution to risk from private equity?" |
| **risk** | "What is a good Sharpe ratio?" | "Is my factor exposure consistent with my stated risk budget?" |
| **portfolio** | "Am I on track with my target allocation?" | "Where should I trim to reduce tracking error vs target?" |
| **portfolio** | "What is causing my portfolio drift?" | "What's the tax-efficiency trade-off of rebalancing now vs deferring?" |
| **portfolio** | "How do I rebalance?" | "How does my current allocation compare to the efficient frontier?" |
| **cma** | "What returns should I expect from bonds?" | "How are the forward-looking equity risk premia adjusted for current valuations?" |
| **cma** | "What is the equity risk premium?" | "What correlation assumptions drive the diversification benefit?" |
| **cma** | "How are these assumptions derived?" | "How sensitive is the efficient frontier to the inflation assumption?" |
| **esg** | "What is Clarity AI?" | "How does my portfolio's WACI compare to the Paris-aligned benchmark?" |
| **esg** | "How is impact measured?" | "What's the look-through carbon exposure from my equity funds?" |
| **esg** | "What is the difference between..." | "Which holdings are flagged for SFDR Article 8/9 compliance?" |

**Rationale:** End users are wealth managers who know basics - questions now use industry terminology (WACI, SFDR, ex-ante VaR, marginal contribution to risk).

---

### ✅ Workstream 4: FAB + AI Modal Migration Manifest

**What was done:**
- Created comprehensive migration manifest document
- Identified all code blocks that need to be surgically added to prod

**Manifest location:** `/Users/xavi_court/Downloads/Risk & PC App 2/AI_FEATURE_MIGRATION_MANIFEST.md`

**Summary of what needs to be added to prod:**

| Category | Items |
|----------|-------|
| **SVG Assets** | `ai-fab-icon.svg`, `isometric-cubes.svg` |
| **icons.py** | APPEND `icon_ask_alti()` function |
| **app_dashboard3.py** | 9 insertion points (imports, constants, CSS, JS, stores, FAB, modal, callbacks) |
| **Delete** | `app_eval - Copy.py` (cleanup) |

**Access Control (Built-in):**
```python
AI_AUTHORIZED_USERS = [
    "xavier.court@alti-global.com",
    "alex.hokanson@alti-global.com",
    "joao.abrantes@alti-global.com"
]
```
Only these 3 users will see the FAB button and AI modal during dev testing.

---

### ✅ Workstream 5: RAG Windows Deployment Prep

**What was done:**
- Added environment-based configuration (dev vs production)
- Added startup validation for required env vars
- Added graceful error handling for port binding
- Created Windows deployment guide
- Verified no Unix-specific code in our codebase

**Files modified:**
- `config.py` - Added `environment`, `validate_environment()`, Windows path functions
- `main.py` - Added `run_server()` with validation and error handling

**Files created:**
- `WINDOWS_DEPLOYMENT.md` - Step-by-step Windows deployment guide

**Key config changes:**
```python
# .env for production
ENVIRONMENT=production
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Auto-uses Windows paths:
# D:\App\rag-service\chroma_db
# D:\App\rag-service\logs
```

---

## Remaining Work

### Workstream 3: Look-Through to Dev - SKIPPED
**Reason:** User determined this was unnecessary - Look-Through is already in prod where it needs to be.

### Workstream 6: Code Reconciliation - NOT STARTED
**Tasks:**
- [ ] Delete `app_eval - Copy.py` from prod
- [ ] Remove `app_risk_old.py` from dev
- [ ] Remove `app_risk_w.py` from dev
- [ ] Verify SAML certs exist in both dev and prod

---

## Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **RAG Host** | Same Windows Server as Dashboard | Simplest - localhost:8080, no firewall changes |
| **Feedback Storage** | JSON file (`logs/feedback.jsonl`) | Consistent with metrics.jsonl pattern |
| **AI Feature Access** | Restricted to 3 users | Dev testing only (Xavier, Alex, Joao) |
| **Deployment Approach** | Surgical file changes | Minimize risk vs wholesale replacement |
| **FAQ Style** | Technical/professional | Wealth managers know basics |

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│           Windows Server (Prod)              │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │ RPC Dashboard   │  │   RAG Service    │  │
│  │ (port 443)      │──│   (port 8080)    │  │
│  │                 │  │   localhost      │  │
│  └─────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────┘

Dashboard calls: http://localhost:8080/api/v1/v2/query
```

---

## File Locations Reference

| Component | Path |
|-----------|------|
| Dev Dashboard | `/Users/xavi_court/dev/alti-rpc-dashboard/` |
| Prod Dashboard | `/Users/xavi_court/Downloads/Risk & PC App 2/` |
| RAG Service | `/Users/xavi_court/claude_code/alti-rag-service/` |
| Migration Manifest | `/Users/xavi_court/Downloads/Risk & PC App 2/AI_FEATURE_MIGRATION_MANIFEST.md` |
| Windows Deploy Guide | `/Users/xavi_court/claude_code/alti-rag-service/WINDOWS_DEPLOYMENT.md` |
| Plan File | `/Users/xavi_court/.claude/plans/nested-nibbling-yeti.md` |
| Login Background | Both `assets/login-background.jpg` |
| Feedback Storage | `alti-rag-service/logs/feedback.jsonl` |

---

## Dev vs Prod Feature Delta

| Feature | Dev | Prod | Action Needed |
|---------|-----|------|---------------|
| Login background | ✅ | ✅ | Done |
| FAB + AI Modal | ✅ | ❌ | Apply manifest |
| Look-Through | ❌ | ✅ | Not migrating |
| Technical FAQs | ✅ | ❌ | Part of AI modal migration |
| Feedback API | ✅ | N/A | RAG service feature |
| Windows config | ✅ | N/A | RAG service feature |
| CMA v3 (experimental) | ✅ | ❌ | Keep dev-only |
| Legacy files | ✅ | ✅ | Delete both |

---

## Dependencies

**No new Python packages required** - both codebases use identical `requirements.txt`.

The RAG service requires:
- `requests` (already in Flask)
- `OPENAI_API_KEY` environment variable for production

---

## Testing Notes

**RAG Service tested and working:**
```bash
# Feedback submission
curl -X POST http://127.0.0.1:8080/api/v1/feedback \
  -H "Content-Type: application/json" \
  -d '{"query_id": "test", "rating": "positive", "comment": "Test"}'

# Feedback stats
curl http://127.0.0.1:8080/api/v1/feedback/stats
```

**Login page tested via Playwright** - screenshots saved to:
- `/Users/xavi_court/dev/alti-rpc-dashboard/UX-UI-database/login-page-final.png`

---

## Next Steps for New Agent

1. **Apply the migration manifest** to prod dashboard (if user is ready)
2. **Complete Workstream 6** - delete legacy files
3. **Deploy RAG service to Windows** using `WINDOWS_DEPLOYMENT.md` guide
4. **Test end-to-end** on production server

---

## Important Context

- **User's employer:** AlTi Global (wealth management)
- **End users:** Wealth managers/advisors (professional, technical audience)
- **Production URL:** https://plotly.alti-global.com
- **Current tech stack:** Dash/Plotly (Python), not React
- **Data storage:** CSV files (Snowflake planned Q1 2026)
- **Deployment:** Windows Server for production

---

*Session conducted by Claude Opus 4.5 - 2026-01-11*
