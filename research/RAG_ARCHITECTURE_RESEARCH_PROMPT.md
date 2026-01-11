# Deep Research Prompt: RAG Architecture for Enterprise Wealth Management

> Use this prompt with Perplexity Deep Research, Claude with web search, or similar research-capable AI to survey the market.

---

## Context

**Organization Profile:**
- Global wealth management firm
- ~$85B AUM (Assets Under Management)
- 400+ employees across multiple regions (US, INT)
- Currently using Azure cloud (flexibility TBD)
- Snowflake planned as centralized data source
- Regulatory environment: SEC, FINRA, potentially MiFID II

**Current State:**
- In-house RAG service built with Python/FastAPI
- LangGraph for agentic workflows (CRAG document grading, intent routing, reranking)
- ChromaDB for vector storage
- OpenAI GPT-4o-mini for LLM calls
- ~500 documents across investments and educational content
- Primary use case: Answering questions about portfolios, risk analytics, and investment education

**Key Metrics from Internal Testing:**
- v1 (basic RAG): 44% retrieval accuracy, ~4s latency
- v2 (LangGraph): 90% retrieval accuracy, ~24s latency (being optimized to ~4-6s)

---

## Research Questions

### 1. Build vs Buy Decision

For an 85B AUM wealth management firm, evaluate:

**Managed RAG Services:**
- Azure AI Search + Azure OpenAI (native integration story)
- Pinecone Serverless + Pinecone Assistants
- Cohere RAG (embed + rerank + command)
- Amazon Bedrock Knowledge Bases
- Google Vertex AI Search

**For each, research:**
- Pricing model and estimated cost for ~500-5,000 documents, ~1,000 queries/day
- Financial services compliance certifications (SOC 2, ISO 27001, FINRA requirements)
- Data residency options (US, EU)
- Integration complexity with existing Python/FastAPI stack
- Snowflake integration capabilities
- Production examples in financial services

### 2. Framework Comparison

Compare current LangGraph approach against alternatives:

**Frameworks to evaluate:**
- LangChain (current ecosystem) + LangGraph (current choice)
- LlamaIndex (agents, query pipelines, property graphs)
- Haystack 2.0 (pipelines, components)
- DSPy (programmatic prompting, optimization)
- Semantic Kernel (Microsoft, Azure-native)
- CrewAI / AutoGen (multi-agent frameworks)

**For each, assess:**
- Maturity for production financial services use
- CRAG/self-RAG pattern support
- Streaming response support
- Observability and tracing (LangSmith, Arize, etc.)
- Active maintenance and community (GitHub stars, release frequency, enterprise adoption)
- Azure + Snowflake integration stories
- Learning curve and team ramp-up time

### 3. Enterprise Considerations

**Compliance & Security:**
- What RAG architectures are peers (Fidelity, Schwab, BlackRock, wealth RIAs) using?
- How do firms handle client data in RAG systems under SEC Regulation S-P?
- What audit trail requirements exist for AI-generated investment advice?
- Are there emerging FINRA or SEC guidelines on RAG/LLM use in wealth management?

**Operational:**
- What's the typical team size to maintain an in-house RAG system at this scale?
- What's the TCO comparison: managed service vs 1-2 FTE maintaining in-house?
- What observability stack (LangSmith, Langfuse, Arize, Weights & Biases) do financial services firms prefer?

**Data Architecture:**
- Best practices for RAG + Snowflake integration (Snowflake Cortex, external vector stores)
- How to handle real-time portfolio data alongside static knowledge base?
- Multi-tenant RAG patterns for client-specific data isolation

### 4. Specific Technical Questions

**LangGraph Deep Dive:**
- What are known production issues with LangGraph at scale (>1000 concurrent users)?
- How does LangGraph compare to LlamaIndex Workflows for complex agentic patterns?
- Best practices for LangGraph checkpointing in financial services (audit trails)?

**Vector Database Selection:**
- ChromaDB (current) vs Qdrant vs Weaviate vs pgvector vs Pinecone for regulated industries
- Which vector DBs have FINRA/SEC compliance track records?
- Snowflake Arctic embeddings + Cortex Search vs external vector store

**Latency Optimization:**
- What techniques are peers using to achieve <2s RAG response times?
- Caching strategies for financial Q&A (stale data concerns)?
- Edge deployment patterns for global wealth management

---

## Desired Output Format

1. **Executive Summary** (1 page)
   - Recommendation: Build, Buy, or Hybrid
   - Top 3 risks with current approach
   - Top 3 opportunities

2. **Detailed Comparison Matrix**
   - Managed services with scores (1-5) for: Cost, Compliance, Integration, Features
   - Frameworks with scores for: Maturity, Features, Azure Fit, Team Ramp

3. **Peer Benchmarks**
   - What are 3-5 comparable wealth management firms doing?
   - Any public case studies or conference talks?

4. **Recommended Architecture**
   - If staying in-house: specific improvements
   - If going managed: migration path
   - If hybrid: which components to outsource

5. **Next Steps**
   - POC recommendations
   - Vendor evaluation criteria
   - Timeline estimate

---

## Research Sources to Prioritize

1. **Primary:**
   - Vendor documentation (LangChain, LlamaIndex, Azure, etc.)
   - Financial services case studies
   - Recent conference talks (AI Engineer Summit 2025, LangChain meetups)

2. **Community:**
   - r/LocalLLaMA, r/MachineLearning for real-world experiences
   - Hacker News discussions on RAG in production
   - LangChain Discord / GitHub discussions

3. **Analyst:**
   - Gartner/Forrester reports on enterprise RAG (if accessible)
   - a]6z, Sequoia, or Andreessen Horowitz AI infrastructure posts

4. **Regulatory:**
   - SEC.gov for AI/ML guidance in investment advisory
   - FINRA regulatory notices on AI use
   - Industry groups (SIFMA, Investment Adviser Association) AI guidelines

---

*Created: 2026-01-09*
*For: AlTi Global RAG Service Architecture Evaluation*
