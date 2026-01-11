# Session: All Pill Restoration & Feedback UI

**Date:** 2026-01-11
**Duration:** ~30 minutes
**Focus:** Command Palette UX improvements

---

## Summary

Two features added to the Command Palette:
1. Restored "All" context pill with cross-domain FAQ content
2. Added subtle feedback interface (checkmark/X with optional text input)

---

## 1. "All" Pill Restoration

### Problem
The "All" pill was previously removed, but users need a general context for cross-domain questions when they don't know which specific tool applies.

### Solution
Restored "All" as the first pill (default active) with purpose-built FAQ content.

### Changes

**Dashboard (`app_dashboard3.py`):**

| Location | Change |
|----------|--------|
| Line 1605 | Added `html.Button("All", id="ctx-all", ...)` as first pill |
| Line 862 | Updated `CONTEXT_HINTS['all']` with meaningful hint |
| Lines 873-877 | Updated `CONTEXT_FAQS['all']` with cross-domain questions |
| Line 1726 | Changed default store from `"portfolio"` to `"all"` |
| Line 1669 | Changed initial suggestions to `build_faq_suggestions('all')` |
| Lines 2348, 2361 | Added Output/Input for `ctx-all` in callback |
| Line 2384 | Added `"ctx-all": "all"` to `pill_to_context` mapping |
| Line 2407 | Added class generation for "all" context |

**New FAQ Content:**

Created `/Users/xavi_court/claude_code/alti-rag-service/data/app_education/FAQ_General.md` with 7 sections:
- What questions can I ask here?
- How do I interpret my risk-adjusted returns?
- What metrics matter most for my portfolio?
- How do the different analysis tools connect?
- What does "confidence level" mean across the dashboard?
- How often should I rebalance my portfolio?
- How do I export or share my analysis?

**RAG Re-index Results:**
- Before: 790 documents
- After: 899 documents (+109)
- Files: 6 → 7 (added FAQ_General.md)

### "All" Context Configuration

```python
CONTEXT_HINTS = {
    'all': "I am exploring the RPC Dashboard and want to understand my overall wealth picture. ",
    ...
}

CONTEXT_FAQS = {
    'all': [
        "What questions can I ask here?",
        "How do I interpret my risk-adjusted returns?",
        "What metrics matter most for my portfolio?",
    ],
    ...
}
```

---

## 2. Feedback UI

### Problem
No way to collect user feedback on RAG response quality.

### Design Requirements (from user)
- Subtle, "nonchalant" like keyboard shortcut toggle
- Checkmark and X icons (no emoji, no prominent buttons)
- Optional text input expands after selection
- Placeholder: "Please specify (optional)"

### Solution

**Visual Flow:**
1. Default: `Helpful? [✓] [✗]` - subtle gray icons
2. After click: Selected icon highlights (green/red), text input slides in
3. After submit (or ignore): Everything resets to subtle gray

### CSS Added (lines 442-508)

```css
.feedback-icon {
    background: transparent;
    border: none;
    color: #ccc;
    /* ... */
}
.feedback-icon.selected-up { color: #16a34a; }
.feedback-icon.selected-down { color: #dc2626; }
.feedback-input-wrap { display: none; }
.feedback-input-wrap.visible { display: flex; }
```

### HTML Structure

```python
html.Div([
    html.Span("Helpful?", style={"fontSize": "12px", "color": "#aaa"}),
    html.Button(html.Img(src=check_svg), id="feedback-up", className="feedback-icon"),
    html.Button(html.Img(src=x_svg), id="feedback-down", className="feedback-icon"),
    html.Div([
        dbc.Input(id="feedback-text", placeholder="Please specify (optional)"),
        html.Button(html.Img(src=send_svg), id="feedback-submit"),
    ], id="feedback-input-wrap", className="feedback-input-wrap"),
], className="feedback-bar")
```

### Callbacks Added

**`handle_feedback_click` (lines 3027-3057):**
- Triggered by checkmark or X click
- Logs initial feedback: `[FEEDBACK] positive/negative | context=X | query=Y...`
- Highlights selected icon, shows text input

**`handle_feedback_submit` (lines 3060-3089):**
- Triggered by send button or Enter key in text input
- Logs detail: `[FEEDBACK-DETAIL] positive/negative | context=X | detail=Y`
- Resets UI to subtle state

### Logging Format

```
[FEEDBACK] positive | context=mcs | query=What does my 95th percentile...
[FEEDBACK-DETAIL] positive | context=mcs | detail=Missing inflation adjustment info
```

---

## Files Modified

| File | Lines Changed | Description |
|------|---------------|-------------|
| `app_dashboard3.py` | +70 CSS, +30 HTML, +60 callback | All pill + feedback UI |
| `FAQ_General.md` | +180 (new file) | Cross-domain FAQ content |

---

## Testing Checklist

1. Open Command Palette (Cmd+K)
2. Verify "All" pill is first and active by default
3. Verify 3 FAQ suggestions show for "All" context
4. Ask a question, verify response appears
5. Click checkmark - verify it turns green, text input appears
6. Type optional feedback, press Enter or click arrow
7. Verify UI resets to subtle gray
8. Check app logs for `[FEEDBACK]` entries

---

## Future Considerations

- **Feedback endpoint:** Placeholder exists in callback for sending feedback to RAG service metrics endpoint
- **Analytics:** Could aggregate feedback by context/query to identify content gaps
- **Negative feedback triage:** High-value signal for improving FAQ content

---

*Session completed: 2026-01-11*
