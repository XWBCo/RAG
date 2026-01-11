"""Retrieval engine for AlTi RAG Service."""

import logging
from enum import Enum
from pathlib import Path
from typing import List, Optional

import chromadb
from llama_index.core import Settings, StorageContext, VectorStoreIndex, PromptTemplate
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import ResponseMode, get_response_synthesizer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.vector_stores.chroma import ChromaVectorStore
from pydantic import BaseModel

from .prompts import get_prompt, list_prompts, PROMPTS

logger = logging.getLogger(__name__)


def get_embed_model(provider: str, **kwargs):
    """Get embedding model based on provider."""
    if provider == "ollama":
        from llama_index.embeddings.ollama import OllamaEmbedding
        return OllamaEmbedding(
            model_name=kwargs.get("model", "nomic-embed-text"),
            base_url=kwargs.get("base_url", "http://localhost:11434"),
        )
    else:  # openai
        from llama_index.embeddings.openai import OpenAIEmbedding
        return OpenAIEmbedding(model=kwargs.get("model", "text-embedding-3-small"))


def get_llm(provider: str, **kwargs):
    """Get LLM based on provider."""
    if provider == "ollama":
        from llama_index.llms.ollama import Ollama
        return Ollama(
            model=kwargs.get("model", "llama3.2:3b"),
            base_url=kwargs.get("base_url", "http://localhost:11434"),
            request_timeout=120.0,
            temperature=0.0,  # Deterministic output
        )
    else:  # openai
        from llama_index.llms.openai import OpenAI
        return OpenAI(model=kwargs.get("model", "gpt-4o-mini"), temperature=0.0)  # Deterministic


class QueryMode(str, Enum):
    """Query response modes."""

    COMPACT = "compact"  # Concise answers
    TREE_SUMMARIZE = "tree_summarize"  # Hierarchical summarization
    REFINE = "refine"  # Iterative refinement
    SIMPLE = "simple_summarize"  # Direct answer


class Source(BaseModel):
    """Source document reference."""

    file_name: str
    document_type: str
    relevance_score: float
    page_number: Optional[int] = None
    chunk_text: str
    priority: Optional[str] = None
    priority_score: Optional[float] = None
    is_priority_document: bool = False


class QueryResult(BaseModel):
    """Query result with sources."""

    answer: str
    sources: List[Source]
    query: str


class RetrievalEngine:
    """
    RAG retrieval engine for investment documents.

    Supports semantic search with optional metadata filtering
    and multiple response synthesis modes.
    """

    def __init__(
        self,
        chroma_persist_dir: str = "./chroma_db",
        collection_name: str = "alti_investments",
        provider: str = "openai",
        embedding_model: str = None,  # Auto-select based on provider
        llm_model: str = None,  # Auto-select based on provider
        base_url: str = "http://localhost:11434",
        similarity_top_k: int = 5,
    ):
        # Auto-select models based on provider
        if embedding_model is None:
            embedding_model = "text-embedding-3-small" if provider == "openai" else "nomic-embed-text"
        if llm_model is None:
            llm_model = "gpt-4o-mini" if provider == "openai" else "llama3.2:3b"
        self.chroma_persist_dir = Path(chroma_persist_dir)
        self.collection_name = collection_name
        self.similarity_top_k = similarity_top_k
        self.provider = provider

        # Initialize models based on provider
        Settings.embed_model = get_embed_model(
            provider, model=embedding_model, base_url=base_url
        )
        Settings.llm = get_llm(
            provider, model=llm_model, base_url=base_url
        )

        # Initialize vector store
        self._init_vector_store()

    def _init_vector_store(self):
        """Initialize connection to Chroma vector store."""
        if not self.chroma_persist_dir.exists():
            raise ValueError(
                f"Chroma directory not found: {self.chroma_persist_dir}. "
                "Run ingestion first."
            )

        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_persist_dir)
        )

        try:
            self.chroma_collection = self.chroma_client.get_collection(
                name=self.collection_name
            )
        except Exception:
            # Collection doesn't exist yet
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name
            )

        self.vector_store = ChromaVectorStore(
            chroma_collection=self.chroma_collection
        )

        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        # Build index from vector store
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            storage_context=self.storage_context,
        )

    def query(
        self,
        query_text: str,
        mode: QueryMode = QueryMode.COMPACT,
        top_k: Optional[int] = None,
        filters: Optional[dict] = None,
        min_similarity: float = 0.5,
    ) -> QueryResult:
        """
        Query the investment knowledge base.

        Args:
            query_text: Natural language query
            mode: Response synthesis mode
            top_k: Number of documents to retrieve
            filters: Metadata filters (e.g., {"document_type": "portfolio_summary"})
            min_similarity: Minimum similarity score threshold

        Returns:
            QueryResult with answer and source documents
        """
        top_k = top_k or self.similarity_top_k

        # Build retriever with optional filters
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k,
        )

        # Add similarity threshold postprocessor
        postprocessors = [
            SimilarityPostprocessor(similarity_cutoff=min_similarity)
        ]

        # Build response synthesizer
        response_synthesizer = get_response_synthesizer(
            response_mode=ResponseMode(mode.value),
        )

        # Create query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=postprocessors,
        )

        # Execute query
        response = query_engine.query(query_text)

        # Extract sources with priority information
        sources = []
        for node in response.source_nodes:
            metadata = node.node.metadata
            sources.append(Source(
                file_name=metadata.get("file_name", "Unknown"),
                document_type=metadata.get("document_type", "Unknown"),
                relevance_score=node.score if node.score else 0.0,
                page_number=metadata.get("page_number"),
                chunk_text=node.node.text[:500] + "..." if len(node.node.text) > 500 else node.node.text,
                priority=metadata.get("priority"),
                priority_score=metadata.get("priority_score"),
                is_priority_document=metadata.get("is_priority_document", False),
            ))

        return QueryResult(
            answer=str(response),
            sources=sources,
            query=query_text,
        )

    def query_with_prompt(
        self,
        query_text: str,
        prompt_name: str = "standard_qa",
        custom_prompt: Optional[str] = None,
        mode: QueryMode = QueryMode.COMPACT,
        top_k: Optional[int] = None,
        min_similarity: float = 0.3,
    ) -> QueryResult:
        """
        Query with a specific prompt template.

        Args:
            query_text: Natural language query
            prompt_name: Name of registered prompt template
            custom_prompt: Optional custom prompt string (overrides prompt_name)
            mode: Response synthesis mode
            top_k: Number of documents to retrieve
            min_similarity: Minimum similarity score threshold

        Returns:
            QueryResult with answer and source documents
        """
        top_k = top_k or self.similarity_top_k

        # Get prompt template
        if custom_prompt:
            qa_template = PromptTemplate(custom_prompt)
        else:
            qa_template = get_prompt(prompt_name)

        # Build retriever
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k,
        )

        # Add similarity threshold postprocessor
        postprocessors = [
            SimilarityPostprocessor(similarity_cutoff=min_similarity)
        ]

        # Build response synthesizer with custom prompt
        response_synthesizer = get_response_synthesizer(
            response_mode=ResponseMode(mode.value),
            text_qa_template=qa_template,
        )

        # Create query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=postprocessors,
        )

        # Execute query
        response = query_engine.query(query_text)

        # Extract sources
        sources = []
        for node in response.source_nodes:
            metadata = node.node.metadata
            sources.append(Source(
                file_name=metadata.get("file_name", "Unknown"),
                document_type=metadata.get("document_type", "Unknown"),
                relevance_score=node.score if node.score else 0.0,
                page_number=metadata.get("page_number"),
                chunk_text=node.node.text[:500] + "..." if len(node.node.text) > 500 else node.node.text,
                priority=metadata.get("priority"),
                priority_score=metadata.get("priority_score"),
                is_priority_document=metadata.get("is_priority_document", False),
            ))

        return QueryResult(
            answer=str(response),
            sources=sources,
            query=query_text,
        )

    def get_available_prompts(self) -> list:
        """Get list of available prompt templates."""
        return list_prompts()

    def search(
        self,
        query_text: str,
        top_k: int = 10,
        filters: Optional[dict] = None,
        boost_priority: bool = True,
    ) -> List[Source]:
        """
        Semantic search without LLM synthesis.

        Args:
            query_text: Natural language query
            top_k: Number of results to return
            filters: Metadata filters
            boost_priority: Whether to boost priority documents in ranking

        Returns raw document chunks matching the query.
        """
        # Fetch more results if boosting to allow re-ranking
        fetch_k = top_k * 2 if boost_priority else top_k

        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=fetch_k,
        )

        nodes = retriever.retrieve(query_text)

        sources = []
        for node in nodes:
            metadata = node.node.metadata
            base_score = node.score if node.score else 0.0

            # Apply priority boost if enabled
            if boost_priority:
                priority_score = metadata.get("priority_score", 0.5)
                # Boost formula: 70% semantic similarity + 30% priority
                boosted_score = (0.7 * base_score) + (0.3 * priority_score)
            else:
                boosted_score = base_score

            sources.append(Source(
                file_name=metadata.get("file_name", "Unknown"),
                document_type=metadata.get("document_type", "Unknown"),
                relevance_score=boosted_score,
                page_number=metadata.get("page_number"),
                chunk_text=node.node.text,
                priority=metadata.get("priority"),
                priority_score=metadata.get("priority_score"),
                is_priority_document=metadata.get("is_priority_document", False),
            ))

        # Re-sort by boosted score and return top_k
        sources.sort(key=lambda x: x.relevance_score, reverse=True)
        return sources[:top_k]

    def search_priority_first(
        self,
        query_text: str,
        top_k: int = 10,
    ) -> List[Source]:
        """
        Search with priority documents always ranked first.

        Priority documents (Model Archetypes, etc.) are returned first,
        followed by semantically relevant non-priority documents.
        """
        # Get more results to ensure we capture priority docs
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k * 3,
        )

        nodes = retriever.retrieve(query_text)

        priority_sources = []
        regular_sources = []

        for node in nodes:
            metadata = node.node.metadata
            source = Source(
                file_name=metadata.get("file_name", "Unknown"),
                document_type=metadata.get("document_type", "Unknown"),
                relevance_score=node.score if node.score else 0.0,
                page_number=metadata.get("page_number"),
                chunk_text=node.node.text,
                priority=metadata.get("priority"),
                priority_score=metadata.get("priority_score"),
                is_priority_document=metadata.get("is_priority_document", False),
            )

            if source.is_priority_document:
                priority_sources.append(source)
            else:
                regular_sources.append(source)

        # Sort each group by relevance
        priority_sources.sort(key=lambda x: x.relevance_score, reverse=True)
        regular_sources.sort(key=lambda x: x.relevance_score, reverse=True)

        # Return priority first, then fill with regular
        combined = priority_sources + regular_sources
        return combined[:top_k]

    def search_model_allocations(
        self,
        query_text: str,
        model: Optional[str] = None,
        region: str = "US",
        top_k: int = 5,
    ) -> List[Source]:
        """
        Smart search for Model Archetypes allocations.

        Detects model names, defaults to US region, and prioritizes
        fund_model_allocation documents over fund_profile documents.

        Args:
            query_text: Natural language query
            model: Specific model (IBI, Impact 100%, Climate, Inclusive Innovation)
            region: US or International (default: US)
            top_k: Number of results
        """
        # Normalize model aliases
        model_aliases = {
            "ibi": "Integrated Best Ideas",
            "integrated": "Integrated Best Ideas",
            "integrated best ideas": "Integrated Best Ideas",
            "impact": "Impact 100%",
            "impact 100": "Impact 100%",
            "impact 100%": "Impact 100%",
            "climate": "Climate Sustainability",
            "climate sustainability": "Climate Sustainability",
            "social": "Inclusive Innovation",
            "inclusive": "Inclusive Innovation",
            "inclusive innovation": "Inclusive Innovation",
        }

        # Detect model from query if not specified
        query_lower = query_text.lower()
        detected_model = model

        if not detected_model:
            for alias, full_name in model_aliases.items():
                if alias in query_lower:
                    detected_model = full_name
                    break

        # Detect region from query
        detected_region = region
        if "international" in query_lower or "intl" in query_lower:
            detected_region = "International"

        # Enhance query with detected model name for better matching
        enhanced_query = query_text
        if detected_model:
            enhanced_query = f"{detected_model} {query_text}"

        # Get more results for filtering
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k * 5,
        )

        nodes = retriever.retrieve(enhanced_query)

        # Filter and score results
        allocation_docs = []
        profile_docs = []

        for node in nodes:
            metadata = node.node.metadata
            doc_type = metadata.get("document_type", "")
            doc_model = metadata.get("model_name", "")
            doc_region = metadata.get("model_region", "")

            source = Source(
                file_name=metadata.get("file_name", "Unknown"),
                document_type=doc_type,
                relevance_score=node.score if node.score else 0.0,
                page_number=metadata.get("page_number"),
                chunk_text=node.node.text,
                priority=metadata.get("priority"),
                priority_score=metadata.get("priority_score"),
                is_priority_document=metadata.get("is_priority_document", False),
            )

            # Categorize by document type
            if doc_type == "fund_model_allocation":
                # Apply model and region filters
                model_match = (not detected_model) or (doc_model == detected_model)
                region_match = (doc_region == detected_region)

                if model_match and region_match:
                    # Boost score for exact matches
                    source.relevance_score *= 1.5
                    allocation_docs.append(source)
                elif model_match:
                    # Partial match (wrong region)
                    allocation_docs.append(source)
            elif doc_type == "fund_profile":
                profile_docs.append(source)

        # Sort allocation docs first, then profiles
        allocation_docs.sort(key=lambda x: x.relevance_score, reverse=True)
        profile_docs.sort(key=lambda x: x.relevance_score, reverse=True)

        # Return allocations first
        combined = allocation_docs + profile_docs
        return combined[:top_k]

    def get_document_types(self) -> List[str]:
        """Get all unique document types in the collection."""
        # Query Chroma for unique metadata values
        results = self.chroma_collection.get(include=["metadatas"])

        doc_types = set()
        for metadata in results.get("metadatas", []):
            if metadata and "document_type" in metadata:
                doc_types.add(metadata["document_type"])

        return sorted(list(doc_types))

    def get_stats(self) -> dict:
        """Get retrieval engine statistics."""
        embed_model = getattr(Settings.embed_model, "model_name", "unknown")
        llm_model = getattr(Settings.llm, "model", "unknown")
        return {
            "collection_name": self.collection_name,
            "document_count": self.chroma_collection.count(),
            "document_types": self.get_document_types(),
            "provider": self.provider,
            "embedding_model": str(embed_model),
            "llm_model": str(llm_model),
        }
