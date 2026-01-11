"""State schema for Prism RAG workflow."""

from typing import Annotated, Literal, Optional, TypedDict
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages


class GradedDocument(TypedDict):
    """Document with relevance grade."""
    document: Document
    relevance: Literal["relevant", "not_relevant"]
    score: float


class PrismState(TypedDict):
    """
    State schema for the Prism RAG workflow.

    This state flows through all nodes in the LangGraph workflow,
    accumulating context and enabling multi-turn conversations.
    """

    # Conversation history (uses add_messages reducer for proper merging)
    messages: Annotated[list[BaseMessage], add_messages]

    # User context from Qualtrics or manual selection
    archetype: Optional[str]  # e.g., "Integrated Best Ideas", "Impact 100%"
    region: Literal["US", "INT"]
    domain: str  # Collection domain: investments, app_education, estate_planning

    # V1 context-aware features (for dashboard compatibility)
    prompt_name: Optional[str]  # Custom prompt template from prompts.py
    app_context: Optional[dict]  # User's computed results for interpretation

    # Intent classification for routing
    intent: Literal["archetype", "pipeline", "clarity", "general"]

    # Current query (extracted from latest message)
    query: str

    # Retrieval results
    retrieved_docs: list[Document]
    graded_docs: list[GradedDocument]

    # CRAG signals
    needs_web_search: bool
    retrieval_quality: Literal["good", "ambiguous", "poor"]

    # Self-RAG reflection
    hallucination_check: Optional[Literal["grounded", "not_grounded", "uncertain"]]
    answer_useful: Optional[Literal["yes", "no", "partial"]]

    # Response
    generation: str
    sources: list[dict]

    # Session tracking
    thread_id: str
    turn_count: int


# Default state for new conversations
def get_initial_state(
    thread_id: str,
    archetype: Optional[str] = None,
    region: str = "US",
    domain: str = "investments",
    prompt_name: Optional[str] = None,
    app_context: Optional[dict] = None,
) -> PrismState:
    """Create initial state for a new conversation."""
    return PrismState(
        messages=[],
        archetype=archetype,
        region=region,
        domain=domain,
        prompt_name=prompt_name,
        app_context=app_context,
        intent="general",
        query="",
        retrieved_docs=[],
        graded_docs=[],
        needs_web_search=False,
        retrieval_quality="good",
        hallucination_check=None,
        answer_useful=None,
        generation="",
        sources=[],
        thread_id=thread_id,
        turn_count=0,
    )


# Archetype mappings for normalization
ARCHETYPE_ALIASES = {
    # Integrated Best Ideas
    "ibi": "Integrated Best Ideas",
    "integrated": "Integrated Best Ideas",
    "integrated_best_ideas": "Integrated Best Ideas",
    "best ideas": "Integrated Best Ideas",

    # Impact 100%
    "impact": "Impact 100%",
    "impact_100": "Impact 100%",
    "impact 100": "Impact 100%",
    "100% impact": "Impact 100%",
    "100 percent": "Impact 100%",

    # Climate Sustainability
    "climate": "Climate Sustainability",
    "climate_sustainability": "Climate Sustainability",
    "sustainability": "Climate Sustainability",

    # Inclusive Innovation
    "inclusive": "Inclusive Innovation",
    "inclusive_innovation": "Inclusive Innovation",
    "innovation": "Inclusive Innovation",
    "social": "Inclusive Innovation",
}


def normalize_archetype(archetype: Optional[str]) -> Optional[str]:
    """Normalize archetype name to canonical form."""
    if not archetype:
        return None

    key = archetype.lower().strip()
    return ARCHETYPE_ALIASES.get(key, archetype)


# Asset class hierarchy
ASSET_CLASSES = {
    "Stability": ["Core Fixed Income", "Tax-Exempt Fixed Income"],
    "Diversified": ["Diversified Strategies"],
    "Growth-Public": ["Global Equity", "US Equity", "International Equity"],
    "Growth-Private": ["Private Equity", "Private Credit"],
    "Catalytic Debt": [],  # No sub-classes
    "Catalytic Equity": [],  # No sub-classes
}


# Risk levels
RISK_LEVELS = ["CON", "BAL", "MG", "GRO", "LTG"]
