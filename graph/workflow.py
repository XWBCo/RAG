"""LangGraph workflow definition for Prism RAG."""

import logging
import os
from typing import Literal, Optional

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
# For production: from langgraph.checkpoint.postgres import PostgresSaver

from .state import PrismState, get_initial_state
from .nodes.route import route_intent, should_retrieve
from .nodes.retrieve import retrieve_documents
from .nodes.grade import grade_documents, should_web_search, rerank_documents
from .nodes.generate import generate_response, check_hallucination, respond_directly

logger = logging.getLogger(__name__)


def create_workflow() -> StateGraph:
    """
    Create the Prism RAG workflow graph.

    Flow:
    1. route_intent: Classify query intent
    2. [conditional] should_retrieve: Skip retrieval for simple queries
    3. retrieve_documents: Hybrid BM25 + semantic search
    4. grade_documents: CRAG relevance grading
    5. [conditional] should_web_search: Fall back to web if poor quality
    6. generate_response: Generate answer with context
    7. check_hallucination: Self-RAG reflection (optional)

    ```
    START
      |
      v
    route_intent
      |
      v
    [should_retrieve?]
      |         \
      v          v
    retrieve   respond_directly --> END
      |
      v
    grade_documents
      |
      v
    [should_web_search?]
      |         \
      v          v
    generate   web_search --> generate
      |
      v
    [enable_reflection?]
      |         \
      v          v
    END       check_hallucination --> END
    ```
    """
    workflow = StateGraph(PrismState)

    # Add nodes
    workflow.add_node("route_intent", route_intent)
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("grade", grade_documents)  # Parallel grading via sync wrapper
    workflow.add_node("rerank", rerank_documents)
    workflow.add_node("generate", generate_response)
    workflow.add_node("respond_directly", respond_directly)
    workflow.add_node("check_hallucination", check_hallucination)

    # Set entry point
    workflow.set_entry_point("route_intent")

    # Add edges
    workflow.add_conditional_edges(
        "route_intent",
        should_retrieve,
        {
            "retrieve": "retrieve",
            "respond_directly": "respond_directly",
        }
    )

    workflow.add_edge("retrieve", "grade")

    # After grading, rerank documents
    workflow.add_conditional_edges(
        "grade",
        should_web_search,
        {
            "generate": "rerank",  # Go to rerank first
            "web_search": "rerank",  # TODO: Implement web search node, then rerank
        }
    )

    # After reranking, generate response
    workflow.add_edge("rerank", "generate")

    # After generation, end (or optionally check hallucination)
    workflow.add_edge("generate", END)
    workflow.add_edge("respond_directly", END)
    workflow.add_edge("check_hallucination", END)

    return workflow


def create_workflow_with_reflection() -> StateGraph:
    """
    Create workflow with Self-RAG reflection enabled.

    Adds hallucination checking after generation.
    """
    workflow = create_workflow()

    # Remove the direct edge to END
    # Note: In newer LangGraph, you'd modify the graph differently
    # This is a simplified version

    # Add reflection step
    def should_reflect(state: PrismState) -> Literal["reflect", "end"]:
        # Only reflect on substantive answers
        if state.get("retrieval_quality") == "good" and len(state.get("sources", [])) > 0:
            return "reflect"
        return "end"

    # This would require restructuring the graph
    # For now, reflection is opt-in via check_hallucination node

    return workflow


def compile_app(
    checkpointer: Optional[object] = None,
    enable_memory: bool = True,
) -> object:
    """
    Compile the workflow into a runnable app.

    Args:
        checkpointer: Optional checkpointer for persistence (PostgresSaver for production)
        enable_memory: Whether to enable in-memory checkpointing

    Returns:
        Compiled LangGraph app
    """
    workflow = create_workflow()

    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    elif enable_memory:
        # Use in-memory checkpointer for development
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    else:
        return workflow.compile()


def get_production_app():
    """
    Get production app with PostgreSQL checkpointer.

    Requires DATABASE_URL environment variable.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.warning("DATABASE_URL not set, using in-memory checkpointer")
        return compile_app(enable_memory=True)

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        checkpointer = PostgresSaver.from_conn_string(db_url)
        return compile_app(checkpointer=checkpointer)
    except ImportError:
        logger.warning("langgraph[postgres] not installed, using in-memory checkpointer")
        return compile_app(enable_memory=True)
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return compile_app(enable_memory=True)


# Singleton app instance
_app = None


def get_app():
    """Get or create the singleton app instance."""
    global _app
    if _app is None:
        _app = compile_app(enable_memory=True)
    return _app


async def invoke_prism(
    query: str,
    thread_id: str,
    archetype: Optional[str] = None,
    region: str = "US",
    domain: str = "investments",
    prompt_name: Optional[str] = None,
    app_context: Optional[dict] = None,
) -> dict:
    """
    Invoke the Prism RAG workflow.

    Args:
        query: User query
        thread_id: Conversation thread ID for memory
        archetype: Pre-selected archetype (e.g., from Qualtrics)
        region: US or INT
        domain: Collection domain (investments, app_education, etc.)
        prompt_name: Custom prompt template for generation
        app_context: User's computed results for interpretation

    Returns:
        dict with answer, sources, and metadata
    """
    from langchain_core.messages import HumanMessage

    app = get_app()

    # Create initial state
    initial_state = get_initial_state(
        thread_id=thread_id,
        archetype=archetype,
        region=region,
        domain=domain,
        prompt_name=prompt_name,
        app_context=app_context,
    )

    # Add query as message
    initial_state["messages"] = [HumanMessage(content=query)]

    # Run workflow
    config = {"configurable": {"thread_id": thread_id}}
    result = await app.ainvoke(initial_state, config)

    return {
        "answer": result.get("generation", ""),
        "sources": result.get("sources", []),
        "intent": result.get("intent", "general"),
        "retrieval_quality": result.get("retrieval_quality", "unknown"),
        "turn_count": result.get("turn_count", 1),
    }


def invoke_prism_sync(
    query: str,
    thread_id: str,
    archetype: Optional[str] = None,
    region: str = "US",
    domain: str = "investments",
    prompt_name: Optional[str] = None,
    app_context: Optional[dict] = None,
) -> dict:
    """Synchronous version of invoke_prism."""
    from langchain_core.messages import HumanMessage

    app = get_app()

    initial_state = get_initial_state(
        thread_id=thread_id,
        archetype=archetype,
        region=region,
        domain=domain,
        prompt_name=prompt_name,
        app_context=app_context,
    )
    initial_state["messages"] = [HumanMessage(content=query)]

    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(initial_state, config)

    return {
        "answer": result.get("generation", ""),
        "sources": result.get("sources", []),
        "intent": result.get("intent", "general"),
        "retrieval_quality": result.get("retrieval_quality", "unknown"),
        "turn_count": result.get("turn_count", 1),
    }


async def stream_prism(
    query: str,
    thread_id: str,
    archetype: Optional[str] = None,
    region: str = "US",
):
    """
    Stream Prism RAG workflow events.

    Yields events as they occur for real-time UI updates.
    """
    from langchain_core.messages import HumanMessage

    app = get_app()

    initial_state = get_initial_state(
        thread_id=thread_id,
        archetype=archetype,
        region=region,
    )
    initial_state["messages"] = [HumanMessage(content=query)]

    config = {"configurable": {"thread_id": thread_id}}

    async for event in app.astream_events(initial_state, config, version="v2"):
        event_type = event.get("event", "")

        if event_type == "on_chat_model_stream":
            # Stream generation tokens
            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content"):
                yield {
                    "type": "token",
                    "content": chunk.content,
                }

        elif event_type == "on_chain_end":
            # Workflow completed
            output = event.get("data", {}).get("output", {})
            if isinstance(output, dict) and "generation" in output:
                yield {
                    "type": "complete",
                    "answer": output.get("generation", ""),
                    "sources": output.get("sources", []),
                    "intent": output.get("intent", "general"),
                }
