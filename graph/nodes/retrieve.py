"""Hybrid retrieval node for Prism RAG workflow.

Implements BM25 + semantic hybrid retrieval for improved accuracy
on exact terms (fund names, tickers) while maintaining semantic understanding.
"""

import logging
from typing import Optional, Any, List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from rank_bm25 import BM25Okapi

from config import settings

# =============================================================================
# Query Expansion (LLM-based)
# =============================================================================

# Lazy-loaded LLM for query expansion (gpt-4o-mini is fast and cheap)
_expander_llm = None


def get_expander_llm() -> ChatOpenAI:
    """Get or create the query expansion LLM."""
    global _expander_llm
    if _expander_llm is None:
        _expander_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=100,
        )
    return _expander_llm


def expand_query_with_llm(query: str, intent: str) -> str:
    """
    Use LLM to expand query with domain-specific terms for better recall.

    This is backend-agnostic - works with ChromaDB or Snowflake.
    Adds synonyms, related terms, and domain vocabulary.
    """
    # Intent-specific domain hints
    intent_hints = {
        "archetype": "investment model portfolios, fund allocations, IBI, Impact 100%, Enhanced Balance",
        "clarity": "ESG metrics, Clarity AI, sustainability scores, carbon intensity, SFDR",
        "pipeline": "fund pipeline, 2025 2026 strategy, new investments",
        "general": "investments, portfolios, risk, returns",
    }

    hint = intent_hints.get(intent, intent_hints["general"])

    prompt = f"""Add 3-5 relevant search terms to improve this investment query.
Output ONLY the expanded query (original + new terms), nothing else.
Keep under 40 words total.

Domain context: {hint}
Original query: {query}
Expanded query:"""

    try:
        llm = get_expander_llm()
        response = llm.invoke(prompt)
        expanded = response.content.strip()

        # Sanity check - if expansion is too different, fall back to original
        if len(expanded) > 200 or query.lower() not in expanded.lower():
            return query

        return expanded
    except Exception as e:
        logging.getLogger(__name__).warning(f"Query expansion failed: {e}, using original")
        return query


from ..state import PrismState, ARCHETYPE_ALIASES


# =============================================================================
# Custom BM25 Retriever (replaces langchain_community.retrievers.BM25Retriever)
# =============================================================================

class SimpleBM25Retriever(BaseRetriever):
    """
    Simple BM25 retriever using rank-bm25 library.

    Provides lexical matching for exact terms like fund names and tickers.
    """

    documents: List[Document] = []
    bm25: Any = None
    k: int = 10

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_documents(cls, documents: List[Document], k: int = 10) -> "SimpleBM25Retriever":
        """Build BM25 index from documents."""
        # Tokenize documents for BM25
        tokenized_corpus = [doc.page_content.lower().split() for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus)

        retriever = cls(documents=documents, bm25=bm25, k=k)
        return retriever

    def _get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """Retrieve documents using BM25 scoring."""
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:self.k]

        return [self.documents[i] for i in top_indices if scores[i] > 0]


# =============================================================================
# Custom Ensemble Retriever (replaces langchain.retrievers.EnsembleRetriever)
# =============================================================================

class SimpleEnsembleRetriever(BaseRetriever):
    """
    Ensemble retriever combining multiple retrievers with weighted RRF.

    Uses Reciprocal Rank Fusion to combine results from semantic and
    lexical retrievers, improving accuracy on both conceptual queries
    and exact term matches.
    """

    retrievers: List[BaseRetriever] = []
    weights: List[float] = []
    c: int = 60  # RRF constant (standard value)

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """Retrieve and fuse results from all retrievers."""
        # Collect results from each retriever
        all_results = []
        for retriever in self.retrievers:
            try:
                docs = retriever.invoke(query)
                all_results.append(docs)
            except Exception as e:
                logging.getLogger(__name__).warning(f"Retriever failed: {e}")
                all_results.append([])

        # Apply weighted Reciprocal Rank Fusion
        doc_scores = {}  # doc_id -> score
        doc_map = {}     # doc_id -> Document

        for retriever_idx, docs in enumerate(all_results):
            weight = self.weights[retriever_idx] if retriever_idx < len(self.weights) else 1.0

            for rank, doc in enumerate(docs):
                # Use page_content as unique identifier
                doc_id = hash(doc.page_content)

                # RRF score: weight / (rank + c)
                rrf_score = weight / (rank + 1 + self.c)

                if doc_id in doc_scores:
                    doc_scores[doc_id] += rrf_score
                else:
                    doc_scores[doc_id] = rrf_score
                    doc_map[doc_id] = doc

        # Sort by fused score
        sorted_doc_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)

        return [doc_map[doc_id] for doc_id in sorted_doc_ids]

logger = logging.getLogger(__name__)

# Global retriever instances keyed by collection name
_retrievers: dict[str, BaseRetriever] = {}
_bm25_retrievers: dict[str, SimpleBM25Retriever] = {}
_hybrid_retrievers: dict[str, SimpleEnsembleRetriever] = {}


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


def get_bm25_retriever(
    persist_directory: str = "./chroma_db",
    collection_name: str = "alti_investments",
    k: int = 10,
) -> Optional[SimpleBM25Retriever]:
    """
    Get or build BM25 retriever from ChromaDB documents.

    Loads all documents from the collection and builds a BM25 index
    for lexical matching. Results are cached globally.
    """
    global _bm25_retrievers

    cache_key = f"{collection_name}_{k}"
    if cache_key in _bm25_retrievers:
        return _bm25_retrievers[cache_key]

    try:
        # Load documents from ChromaDB for BM25 indexing
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )

        # Get all documents for BM25 index
        all_data = vectorstore.get()
        documents_list = all_data.get("documents", [])
        metadatas_list = all_data.get("metadatas", [])

        if not documents_list:
            logger.warning(f"No documents found for BM25 index in {collection_name}")
            return None

        # Convert to LangChain Documents
        documents = [
            Document(page_content=text, metadata=meta or {})
            for text, meta in zip(documents_list, metadatas_list)
        ]

        # Build BM25 retriever
        bm25_retriever = SimpleBM25Retriever.from_documents(documents, k=k)
        _bm25_retrievers[cache_key] = bm25_retriever

        logger.info(f"Built BM25 index for {collection_name} with {len(documents)} docs")
        return bm25_retriever

    except Exception as e:
        logger.error(f"Failed to build BM25 index: {e}")
        return None


def get_hybrid_retriever(
    persist_directory: str = "./chroma_db",
    collection_name: str = "alti_investments",
    k: int = 10,
    bm25_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> BaseRetriever:
    """
    Get hybrid retriever combining BM25 (lexical) and semantic search.

    Hybrid retrieval improves accuracy 15-20% for exact terms like
    fund names, tickers, and specific financial terminology while
    maintaining semantic understanding for concept-based queries.

    Args:
        persist_directory: ChromaDB storage location
        collection_name: Target collection
        k: Number of documents to retrieve per retriever
        bm25_weight: Weight for lexical matching (default 0.4)
        semantic_weight: Weight for semantic similarity (default 0.6)

    Returns:
        EnsembleRetriever combining both approaches, or semantic-only fallback
    """
    global _hybrid_retrievers

    cache_key = f"{collection_name}_{k}_{bm25_weight}_{semantic_weight}"
    if cache_key in _hybrid_retrievers:
        return _hybrid_retrievers[cache_key]

    # Get semantic retriever
    semantic_retriever = get_chroma_retriever(persist_directory, collection_name, k)

    # Get BM25 retriever
    bm25_retriever = get_bm25_retriever(persist_directory, collection_name, k)

    if bm25_retriever is None:
        logger.warning("BM25 index unavailable, using semantic-only retrieval")
        return semantic_retriever

    # Combine with SimpleEnsembleRetriever using reciprocal rank fusion
    hybrid = SimpleEnsembleRetriever(
        retrievers=[semantic_retriever, bm25_retriever],
        weights=[semantic_weight, bm25_weight],
    )

    _hybrid_retrievers[cache_key] = hybrid
    logger.info(f"Created hybrid retriever: semantic={semantic_weight}, bm25={bm25_weight}")

    return hybrid


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
    Enhance query with context and LLM-based expansion for better retrieval.

    Combines:
    1. Static context (archetype, region)
    2. LLM-based query expansion (synonyms, related terms)
    """
    intent = state.get("intent", "general")

    # Step 1: LLM-based expansion (adds domain-specific terms)
    expanded_query = expand_query_with_llm(query, intent)
    logger.info(f"Query expansion: '{query}' → '{expanded_query}'")

    enhanced_parts = [expanded_query]

    # Step 2: Add explicit archetype context if provided
    archetype = state.get("archetype")
    if archetype:
        enhanced_parts.append(archetype)

    # Step 3: Add region context
    region = state.get("region", "US")
    if region == "INT":
        enhanced_parts.append("International")

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
