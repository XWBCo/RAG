# Session: Production Deployment - AI Features Migration

**Date:** 2026-01-12
**Duration:** ~2 hours
**Focus:** Deploy AI features (FAB + Command Palette) to Windows production

---

## Summary

Migrated AI features from dev to prod Dashboard, fixed FAB visibility logic, updated login background, and prepared RAG service for Windows deployment via GitHub.

---

## Completed Work

### 1. AI Feature Migration to Prod Dashboard

Applied migration manifest to `/Users/xavi_court/Downloads/Risk & PC App 2/app_dashboard3.py`:

| Component | Lines Added | Location |
|-----------|-------------|----------|
| `requests` import + `icon_ask_alti` | 2 | Line 18-23 |
| RAG constants (`RAG_SERVICE_URL`, `AI_AUTHORIZED_USERS`, `is_ai_authorized()`) | 17 | Line 26-42 |
| CSS (modal, pills, feedback, loader) | ~245 | Line 311-555 |
| JavaScript (drag/resize handlers) | ~165 | Line 565-728 |
| Context dicts + `build_faq_suggestions()` | ~115 | Line 861-970 |
| dcc.Store components (mcs/risk/eval results, cmd-palette state) | 10 | Line 1464-1655 |
| FAB + Modal layout | ~180 | Line 1474-1646 |
| All RAG callbacks | ~670 | Line 1961-2624 |

**Files modified in prod:**
- `app_dashboard3.py` (+~1200 lines)
- `icons.py` (+25 lines - `icon_ask_alti()`)

**Assets added:**
- `assets/ai-fab-icon.svg` (FAB button)
- `assets/login-background-architectural.jpg` (new login background)

### 2. FAB Visibility Fix

**Problem:** FAB was showing on login page and for all users.

**Solution:** Added `control_fab_visibility()` callback that checks:
1. `session.get('authenticated')` - must be True
2. `is_ai_authorized(user_email)` - must be in `AI_AUTHORIZED_USERS`

**FAB now hidden by default** (`display: none`) and only shown via callback for authorized users.

**Authorized users:**
- xavier.court@alti-global.com
- alex.hokanson@alti-global.com
- joao.abrantes@alti-global.com

### 3. Login Background Update

Changed login page background from generic to architectural image with AlTi brand teal accents.

```python
# Before
"backgroundImage": "url('/assets/login-background.jpg')"

# After
"backgroundImage": "url('/assets/login-background-architectural.jpg')"
```

### 4. RAG Service GitHub Deployment

**Repository:** https://github.com/XWBCo/alti-rag-service (public)

Created `.gitignore`, initialized repo, pushed 115 files including:
- All Python code
- `chroma_db/` vector store (70MB, 456 indexed documents)
- `data/` source documents
- `requirements.txt`

**Excluded:**
- `.env` (contains API keys)
- `venv/`
- `__pycache__/`

### 5. RAG URL Fix

Changed RAG service URL from `localhost` to `127.0.0.1` for consistency:

```python
RAG_SERVICE_URL = "http://127.0.0.1:8080/api/v1/v2/query"
```

---

## Windows Deployment Instructions

### Dashboard (Already Deployed)

4 files to copy to Windows prod:
1. `app_dashboard3.py`
2. `icons.py`
3. `assets/ai-fab-icon.svg`
4. `assets/login-background-architectural.jpg`

### RAG Service (Pending)

**Clone:**
```powershell
git clone https://github.com/XWBCo/alti-rag-service.git "$env:USERPROFILE\Downloads\alti-rag-service"
```

**Setup:**
```powershell
Move-Item "$env:USERPROFILE\Downloads\alti-rag-service" "D:\App\rag-service"
cd D:\App\rag-service
& "C:\Program Files\Python313\python.exe" -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Create `.env`:**
```ini
ENVIRONMENT=production
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-xxxxx
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4o-mini
HOST=127.0.0.1
PORT=8080
DEBUG=false
```

**Start:**
```powershell
python main.py
```

**Expected install time:** 10-20 minutes (slow machine), ~700MB of packages.

---

## Architecture Decisions

### FAB Visibility via Callback (Not Layout Conditional)

In Dash, you can't conditionally render components in the static `app.layout`. Instead:
1. Component exists in layout with `display: none`
2. Callback fires on URL change
3. Checks session state and returns `display: block` or `display: none`

This pattern matches the existing `control_debug_toolbar()` callback.

### RAG Service URL: 127.0.0.1 vs localhost

Used `127.0.0.1` instead of `localhost` to:
- Avoid DNS resolution
- Match Dashboard's binding pattern
- Be explicit about loopback interface

---

## Files Reference

**Prod Dashboard:** `/Users/xavi_court/Downloads/Risk & PC App 2/`
**Dev Dashboard:** `/Users/xavi_court/dev/alti-rpc-dashboard/`
**RAG Service:** `/Users/xavi_court/claude_code/alti-rag-service/`
**GitHub Repo:** https://github.com/XWBCo/alti-rag-service

---

## Testing Checklist

- [x] Dashboard starts without errors
- [x] FAB hidden on login page
- [x] FAB hidden for non-authorized users
- [x] FAB visible for Xavier after login
- [x] Login background updated
- [ ] RAG service deployed to Windows
- [ ] RAG health check passes
- [ ] E2E query test (FAB → question → answer)

---

## Known Issues / Blockers

None currently. Waiting for RAG service deployment on Windows.

---

## Next Steps

1. Complete RAG service deployment on Windows
2. Start RAG service and verify health endpoint
3. E2E test: Login as Xavier → Click FAB → Ask question → Get answer
4. (Optional) Install RAG as Windows service via NSSM for auto-start
5. Delete legacy files:
   - Prod: `app_eval - Copy.py`
   - Dev: `app_risk_old.py`, `app_risk_w.py`

---

*Session completed: 2026-01-12*
