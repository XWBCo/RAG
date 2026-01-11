"""CRAG document grading node for Prism RAG workflow."""

import asyncio
import logging
import time
from typing import Literal, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..state import PrismState, GradedDocument

logger = logging.getLogger(__name__)


class DocumentGrade(BaseModel):
    """Structured output for document relevance grading."""

    relevance: Literal["relevant", "not_relevant"] = Field(
        description="Whether the document is relevant to the query"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for the relevance grade"
    )
    reasoning: str = Field(
        description="Brief explanation for the grade"
    )


GRADE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a document relevance grader for an investment research assistant.

Your task is to assess whether a retrieved document is relevant to answering the user's query.

Consider:
1. Does the document contain information that directly answers the query?
2. Is the document about the same topic/entity mentioned in the query?
3. Does the document provide useful context even if not a direct answer?

Be strict but fair:
- "relevant" = document clearly helps answer the query
- "not_relevant" = document is off-topic or doesn't help

User context:
- Archetype focus: {archetype}
- Region: {region}
- Intent: {intent}
"""),
    ("human", """Query: {query}

Document content:
{document}

Document metadata:
- Type: {doc_type}
- Source: {source}

Is this document relevant to the query?""")
])


async def _grade_single_document(
    chain,
    doc: Document,
    query: str,
    archetype: Optional[str],
    region: str,
    intent: str,
) -> Tuple[Document, GradedDocument]:
    """
    Grade a single document asynchronously.

    Returns tuple of (original_doc, graded_result) for ordering preservation.
    """
    try:
        result: DocumentGrade = await chain.ainvoke({
            "query": query,
            "document": doc.page_content[:2000],
            "doc_type": doc.metadata.get("document_type", "unknown"),
            "source": doc.metadata.get("file_name", "unknown"),
            "archetype": archetype or "Not specified",
            "region": region,
            "intent": intent,
        })

        graded = GradedDocument(
            document=doc,
            relevance=result.relevance,
            score=result.confidence,
        )
        logger.debug(f"Graded doc as {result.relevance}: {result.reasoning[:50]}...")
        return (doc, graded)

    except Exception as e:
        logger.error(f"Failed to grade document: {e}")
        # Default to relevant on error to avoid losing documents
        return (doc, GradedDocument(
            document=doc,
            relevance="relevant",
            score=0.5,
        ))


async def grade_documents_async(state: PrismState) -> PrismState:
    """
    Grade retrieved documents for relevance using CRAG methodology.

    PARALLEL VERSION: All documents graded concurrently via asyncio.gather().
    Expected speedup: 10 docs × 2s sequential = 20s → ~2-4s parallel.

    Updates state with:
    - graded_docs: list of documents with relevance grades
    - retrieval_quality: overall quality assessment
    - needs_web_search: whether to fall back to web search
    """
    docs = state.get("retrieved_docs", [])
    query = state.get("query", "")

    if not docs:
        logger.warning("No documents to grade")
        state["graded_docs"] = []
        state["retrieval_quality"] = "poor"
        state["needs_web_search"] = True
        return state

    start_time = time.perf_counter()

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(DocumentGrade)
    chain = GRADE_PROMPT | structured_llm

    # Extract context once for all documents
    archetype = state.get("archetype")
    region = state.get("region", "US")
    intent = state.get("intent", "general")

    # Create all grading tasks
    tasks = [
        _grade_single_document(chain, doc, query, archetype, region, intent)
        for doc in docs
    ]

    # Run all grading calls in parallel
    results = await asyncio.gather(*tasks)

    # Process results (order preserved by gather)
    graded_docs: list[GradedDocument] = []
    relevant_count = 0

    for _, graded in results:
        graded_docs.append(graded)
        if graded["relevance"] == "relevant":
            relevant_count += 1

    state["graded_docs"] = graded_docs

    # Assess overall retrieval quality
    if relevant_count == 0:
        state["retrieval_quality"] = "poor"
        state["needs_web_search"] = True
    elif relevant_count < len(docs) // 2:
        state["retrieval_quality"] = "ambiguous"
        state["needs_web_search"] = False
    else:
        state["retrieval_quality"] = "good"
        state["needs_web_search"] = False

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        f"Graded {len(docs)} docs in {elapsed_ms:.0f}ms (parallel): "
        f"{relevant_count} relevant, quality={state['retrieval_quality']}"
    )

    return state


def grade_documents(state: PrismState) -> PrismState:
    """
    Grade retrieved documents for relevance using CRAG methodology.

    Synchronous wrapper that runs the async parallel version.
    For direct async usage, call grade_documents_async() instead.

    Updates state with:
    - graded_docs: list of documents with relevance grades
    - retrieval_quality: overall quality assessment
    - needs_web_search: whether to fall back to web search
    """
    # Check if we're already in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context - this shouldn't happen in LangGraph
        # but handle it gracefully
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, grade_documents_async(state))
            return future.result()
    except RuntimeError:
        # No running loop - we can use asyncio.run()
        return asyncio.run(grade_documents_async(state))


def get_relevant_docs(state: PrismState) -> list[Document]:
    """Extract only relevant documents from graded docs."""
    graded_docs = state.get("graded_docs", [])
    return [
        gd["document"] for gd in graded_docs
        if gd["relevance"] == "relevant"
    ]


def should_web_search(state: PrismState) -> Literal["web_search", "generate"]:
    """
    Conditional edge: determine if web search is needed.

    Triggers web search when:
    - No relevant documents found
    - Retrieval quality is poor
    - Query seems to be about recent/external information
    """
    if state.get("needs_web_search", False):
        return "web_search"
    return "generate"


def rerank_documents(state: PrismState) -> PrismState:
    """
    Rerank documents using Cohere cross-encoder for improved precision.

    Falls back to confidence-based sorting if Cohere is unavailable.
    """
    import os

    start_time = time.perf_counter()
    graded_docs = state.get("graded_docs", [])
    relevant_docs = [gd for gd in graded_docs if gd["relevance"] == "relevant"]

    if not relevant_docs:
        state["retrieved_docs"] = []
        return state

    query = state.get("query", "")

    # Try Cohere reranking
    cohere_key = os.getenv("COHERE_API_KEY")
    if cohere_key and len(relevant_docs) > 1:
        try:
            from langchain_cohere import CohereRerank
            from langchain.retrievers.document_compressors import DocumentCompressorPipeline

            reranker = CohereRerank(
                model="rerank-english-v3.0",
                top_n=min(5, len(relevant_docs)),
                cohere_api_key=cohere_key,
            )

            # Extract documents for reranking
            docs_to_rerank = [gd["document"] for gd in relevant_docs]

            # Rerank
            reranked = reranker.compress_documents(docs_to_rerank, query)

            state["retrieved_docs"] = list(reranked)[:5]
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.info(f"Cohere reranked {len(docs_to_rerank)} -> {len(state['retrieved_docs'])} docs in {elapsed_ms:.0f}ms")
            return state

        except ImportError:
            logger.warning("langchain-cohere not installed, using fallback reranking")
        except Exception as e:
            logger.warning(f"Cohere reranking failed: {e}, using fallback")

    # Fallback: sort by grade confidence
    relevant_docs.sort(key=lambda x: x["score"], reverse=True)
    state["retrieved_docs"] = [gd["document"] for gd in relevant_docs[:5]]

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    logger.info(f"Reranked {len(relevant_docs)} docs in {elapsed_ms:.0f}ms (fallback sort)")

    return state


def rerank_with_bge(state: PrismState) -> PrismState:
    """
    Alternative reranking using BGE cross-encoder (local, no API key needed).

    Requires: pip install sentence-transformers
    Model: BAAI/bge-reranker-v2-m3
    """
    graded_docs = state.get("graded_docs", [])
    relevant_docs = [gd for gd in graded_docs if gd["relevance"] == "relevant"]

    if len(relevant_docs) <= 1:
        state["retrieved_docs"] = [gd["document"] for gd in relevant_docs]
        return state

    query = state.get("query", "")

    try:
        from sentence_transformers import CrossEncoder

        model = CrossEncoder("BAAI/bge-reranker-v2-m3", max_length=512)

        # Prepare pairs for scoring
        pairs = [(query, gd["document"].page_content[:1000]) for gd in relevant_docs]

        # Get scores
        scores = model.predict(pairs)

        # Sort by score
        scored_docs = list(zip(relevant_docs, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)

        state["retrieved_docs"] = [gd["document"] for gd, _ in scored_docs[:5]]
        logger.info(f"BGE reranked {len(relevant_docs)} docs")

    except ImportError:
        logger.warning("sentence-transformers not installed, using confidence-based sorting")
        relevant_docs.sort(key=lambda x: x["score"], reverse=True)
        state["retrieved_docs"] = [gd["document"] for gd in relevant_docs[:5]]

    return state
