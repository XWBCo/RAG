"""Hybrid retrieval node for Prism RAG workflow."""

import logging
from typing import Optional, Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings

from config import settings
from ..state import PrismState, ARCHETYPE_ALIASES

logger = logging.getLogger(__name__)

# Global retriever instances keyed by collection name
_retrievers: dict[str, BaseRetriever] = {}


def get_collection_name(domain: str) -> str:
    """Get collection name for a domain."""
    return settings.domain_collections.get(domain, settings.collection_name)


def get_chroma_retriever(
    persist_directory: str = "./chroma_db",
    collection_name: str = "alti_investments",
    k: int = 10,
) -> BaseRetriever:
    """Get or create Chroma vector store retriever for a collection."""
    global _retrievers

    if collection_name not in _retrievers:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )
        _retrievers[collection_name] = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        logger.info(f"Created retriever for collection: {collection_name}")

    return _retrievers[collection_name]


def get_hybrid_retriever(
    persist_directory: str = "./chroma_db",
    collection_name: str = "alti_investments",
    k: int = 10,
    bm25_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> BaseRetriever:
    """
    Get retriever for document search.

    Currently uses semantic search only (via Chroma).
    TODO: Add hybrid BM25+semantic when langchain EnsembleRetriever is restored.
    """
    return get_chroma_retriever(persist_directory, collection_name, k)


def retrieve_documents(state: PrismState) -> PrismState:
    """
    Retrieve relevant documents using hybrid search.

    Routes to specialized retrieval based on intent:
    - archetype: Prioritize fund_model_allocation, fund_profile docs
    - pipeline: Prioritize pipeline_strategy docs
    - clarity: Prioritize metric documentation
    - general: Standard hybrid search
    """
    query = state.get("query", "")
    intent = state.get("intent", "general")
    domain = state.get("domain", "investments")

    if not query:
        logger.warning("Empty query, skipping retrieval")
        state["retrieved_docs"] = []
        return state

    # Get collection name for domain and create retriever
    collection_name = get_collection_name(domain)
    retriever = get_hybrid_retriever(collection_name=collection_name)
    logger.info(f"Retrieving from domain '{domain}' → collection '{collection_name}'")

    # Enhance query based on intent and context
    enhanced_query = enhance_query(query, state)

    try:
        # Retrieve documents
        docs = retriever.invoke(enhanced_query)

        # Filter and reorder based on intent
        filtered_docs = filter_by_intent(docs, intent, state)

        state["retrieved_docs"] = filtered_docs[:10]  # Top 10 after filtering
        logger.info(f"Retrieved {len(state['retrieved_docs'])} documents for intent: {intent}")

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        state["retrieved_docs"] = []

    return state


def enhance_query(query: str, state: PrismState) -> str:
    """
    Enhance query with context for better retrieval.

    Adds archetype name, region, and intent-specific terms.
    """
    enhanced_parts = [query]

    # Add archetype context
    archetype = state.get("archetype")
    if archetype:
        enhanced_parts.append(archetype)

    # Add region context
    region = state.get("region", "US")
    if region == "INT":
        enhanced_parts.append("International")

    # Add intent-specific terms
    intent = state.get("intent", "general")
    if intent == "archetype":
        enhanced_parts.append("model allocation fund")
    elif intent == "pipeline":
        enhanced_parts.append("pipeline strategy 2025")
    elif intent == "clarity":
        enhanced_parts.append("ESG metric Clarity AI")

    return " ".join(enhanced_parts)


def filter_by_intent(
    docs: list[Document],
    intent: str,
    state: PrismState
) -> list[Document]:
    """
    Filter and reorder documents based on intent.

    Prioritizes document types relevant to the intent.
    """
    # Define priority document types per intent
    priority_types = {
        "archetype": ["fund_model_allocation", "fund_profile", "model_overview"],
        "pipeline": ["pipeline_strategy", "fund_pipeline"],
        "clarity": ["esg_metric", "clarity_documentation", "metric_definition"],
        "general": [],  # No specific priority
    }

    priority_doc_types = set(priority_types.get(intent, []))

    # Separate priority and non-priority docs
    priority_docs = []
    other_docs = []

    archetype = state.get("archetype")
    region = state.get("region", "US")

    for doc in docs:
        doc_type = doc.metadata.get("document_type", "")
        doc_archetype = doc.metadata.get("model_name", "")
        doc_region = doc.metadata.get("model_region", "")

        # Check if priority document type
        is_priority = doc_type in priority_doc_types

        # Boost for archetype/region match
        archetype_match = not archetype or doc_archetype == archetype
        region_match = doc_region == region or doc_region == ""

        if is_priority and archetype_match and region_match:
            priority_docs.append(doc)
        elif is_priority:
            # Priority type but wrong archetype/region
            other_docs.insert(0, doc)  # Still prefer over non-priority
        else:
            other_docs.append(doc)

    return priority_docs + other_docs


def retrieve_with_metadata_filter(
    state: PrismState,
    metadata_filter: dict,
    k: int = 10
) -> list[Document]:
    """
    Retrieve with explicit metadata filtering.

    Used for precise queries like "funds in IBI model for US".
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name="alti_investments",
        embedding_function=embeddings,
        persist_directory="./chroma_db",
    )

    query = state.get("query", "")

    # Chroma supports where clauses for metadata filtering
    docs = vectorstore.similarity_search(
        query,
        k=k,
        filter=metadata_filter
    )

    return docs
