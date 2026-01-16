# Fund Document Ingestion & UX Brainstorm Session - 2026-01-14

## Session Summary

Ingested 22 fund documents (812 chunks) into ChromaDB for the Impact pill, expanding the collection from 1,844 to 2,656 documents. Followed with a comprehensive brainstorm on whether the pill/FAQ-based AI modal interface is still optimal for wealth advisors who "don't know what they don't know."

---

## Part 1: Fund Document Ingestion

### Source Material

**File**: `~/Downloads/RAG Files.zip` (22 files, ~33MB)

| Fund | Files | Documents Created |
|------|-------|-------------------|
| BTG Timberland | Q3 2025 LP Report, Market Report | 154 |
| Blackstone Infra | Q1 2025 Pitchbook, Sep 2025 Fact Card | 139 |
| Galvanize | Q4 2025 Presentation | 120 |
| Ares Core Infra | Nov 2025 Fact Sheet + Presentation | 79 |
| Wellington | Presentation, Q2/Q3 2025 Reviews | 78 |
| TCI Fund | Oct 2025 Presentation, MER, Exposure Report | 74 |
| ValueAct | Due Diligence, Position Summary, Q2 Letter | 53 |
| Community EM | Feb 2025 Presentation, Q2 Update | 53 |
| CIM | Feb 2025 Presentation, Q2 Update | 48 |
| Generation IM | Oct 2025 Factsheet + Holdings (XLSX) | 14 |
| **Total** | **22 files** | **812 chunks** |

### Process

1. Extracted zip to `data/fund_docs_staging/RAG Files/`
2. Created `ingest_fund_docs.py` script using existing `IngestionPipeline`
3. Ran ingestion with OpenAI `text-embedding-3-small` embeddings
4. Verified counts by fund in ChromaDB
5. Cleaned up staging folder and script
6. Updated `BACKGROUND_INFO.md` with new collection stats

### Results

| Metric | Before | After |
|--------|--------|-------|
| `alti_investments` docs | 1,844 | **2,656** |
| Fund coverage | 0 funds | **10 funds** |
| Ingestion time | - | ~40 seconds |

### Note: One File Issue

`Wellington Global Stewards Portfolio Manager Review_Q2 2025.pdf` extracted 0 pages - likely a scanned PDF without OCR text layer. May need manual review or OCR processing.

---

## Part 2: UX Brainstorm - Discovery vs. Retrieval

### The Problem

Current AI modal design assumes advisors know what to ask:
- Pill-based context selection
- FAQ-driven content (39 sections)
- Single-turn Q&A

**Reality**: Advisors often don't know what they don't know. They need **discovery**, not just **retrieval**.

### Current System Strengths

| Strength | Why It Works |
|----------|--------------|
| Context pills | Narrows scope, reduces cognitive load |
| FAQ-driven content | 90% retrieval quality on known queries |
| Quick single-turn | Fast answers in client meetings |
| App context injection | Interprets their actual numbers |

### Research That Drove Current Design

- Chat is slow (30-60s per input) - Smashing Magazine
- Task-oriented UIs outperform conversational UIs for help
- 70% adoption with NLQ interfaces - ThoughtSpot
- Proactive help reduces support tickets 30% - Chameleon

### Six Alternative Approaches Evaluated

#### 1. Proactive Context Cards (Recommended - Low effort, High impact)

Surface suggestions before user asks:
```
┌─────────────────────────────────────────┐
│ 📊 You're viewing Monte Carlo Results   │
│                                         │
│ Things to know:                         │
│ • What the 95th percentile means        │
│ • How success probability is calculated │
│ • Why simulations vary between runs     │
└─────────────────────────────────────────┘
```

#### 2. Related Questions After Answers (Recommended)

Enable organic exploration:
```
Related:
• How is concentration risk measured?
• What's a good Effective N value?
• How does this affect my portfolio?
```

#### 3. Limited Multi-turn (2-3 follow-ups) (Recommended)

V2 endpoint already has `thread_id`. Re-enable follow-up button with limit:
```
↩️ Follow-up (2 remaining)
```

#### 4. "Explain This View" Mode

One-click contextual overview of current page - good for "I don't know what to ask."

#### 5. Copilot Sidebar

Persistent panel instead of modal - major UI overhaul, more screen real estate needed.

#### 6. Inline Metric Explanations

Tooltips with depth on every metric - high maintenance overhead.

### Recommendation: Hybrid Approach

Layer discovery on top of existing retrieval system:

| Layer | Feature | Effort | Impact |
|-------|---------|--------|--------|
| 1 | Proactive suggestions per context | Low | High |
| 2 | Related questions after answers | Medium | High |
| 3 | "Explain This Page" button | Medium | High |
| 4 | 2-3 follow-ups via thread_id | Low | Medium |

### Proposed Flow

```
User lands on Monte Carlo page
           ↓
┌─────────────────────────────────────────┐
│ 💡 Quick insights for this view:        │
│ • What does 95th percentile mean?       │
│ • How is success probability calculated?│
│ • [Explain everything on this page]     │
│                                         │
│ Or ask your own question:               │
│ [________________________________]      │
└─────────────────────────────────────────┘
           ↓
User asks question OR clicks suggestion
           ↓
┌─────────────────────────────────────────┐
│ [Answer...]                             │
│                                         │
│ Related:                                │
│ • How does this compare to benchmarks?  │
│ • What if I adjust the withdrawal rate? │
│                                         │
│ [↩️ Ask follow-up] [✓ Done]             │
└─────────────────────────────────────────┘
```

### Why Not Full Chat?

Research still holds:
- 30-60s per chat input is too slow for client meetings
- Task-oriented > conversational for help-seeking
- Advisors need quick answers, not extended dialogues

The hybrid approach adds discovery without sacrificing speed.

### Key Insight

> FAQs are answers to questions people have already asked. Advisors need help **formulating questions** in the first place. Proactive suggestions + related questions create a "guided exploration" pattern that bridges "I know what I want" and "I don't know what I don't know" - without the latency penalty of full chat.

---

## Files Modified

| File | Changes |
|------|---------|
| `BACKGROUND_INFO.md` | Updated collection stats (2,656 docs), removed pending ingestion section |
| `data/fund_docs_staging/` | Created then deleted (cleanup) |
| `ingest_fund_docs.py` | Created then deleted (one-time script) |

---

## Outstanding Tasks

| Priority | Task | Status |
|----------|------|--------|
| High | Fund document ingestion | ✅ Complete |
| Medium | Add `COHERE_API_KEY` to production `.env` | Pending |
| Medium | Run eval baseline with new 2,656 doc set | Pending |
| Medium | Implement proactive suggestions UX | Pending (needs design) |
| Medium | Re-enable follow-up button with thread_id | Pending |
| Blocked | Snowflake IT confirmation | Waiting |

---

## Next Steps (UX Improvements)

If proceeding with hybrid discovery approach:

1. **Define proactive suggestions** - Curate 3-5 suggestions per pill context
2. **Implement related questions** - Either curated or LLM-generated
3. **Re-enable follow-ups** - Use existing `thread_id`, limit to 2-3
4. **Test with advisors** - Get feedback on discovery experience

---

*Session Date: 2026-01-14*
*Duration: ~45 minutes*
