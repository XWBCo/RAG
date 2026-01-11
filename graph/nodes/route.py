"""Intent routing node for Prism RAG workflow."""

import logging
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..state import PrismState, normalize_archetype

logger = logging.getLogger(__name__)


class IntentClassification(BaseModel):
    """Structured output for intent classification."""

    intent: Literal["archetype", "pipeline", "clarity", "general"] = Field(
        description="The classified intent of the user query"
    )
    detected_archetype: str | None = Field(
        default=None,
        description="If archetype intent, the specific archetype mentioned"
    )
    detected_region: Literal["US", "INT"] | None = Field(
        default=None,
        description="If region is mentioned, US or International"
    )
    reasoning: str = Field(
        description="Brief explanation for the classification"
    )


ROUTE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an intent classifier for AlTi's Impact investment assistant.

Classify the user query into one of these intents:

1. **archetype** - Questions about investment models/archetypes:
   - Integrated Best Ideas (IBI), Impact 100%, Climate Sustainability, Inclusive Innovation
   - Fund allocations, holdings, performance, ESG outcomes within a model
   - Questions like "What's in IBI?", "Show me Climate funds", "Fund performance"

2. **pipeline** - Questions about upcoming investment opportunities:
   - New strategies, pipeline investments, upcoming closes
   - Minimum contributions, target dates, new fund launches
   - Questions like "What's in the pipeline?", "New opportunities", "2025 strategies"

3. **clarity** - Questions about Clarity AI metrics and ESG methodology:
   - ESG metrics definitions (carbon intensity, financed emissions, etc.)
   - Metric calculations, real-world examples
   - About Clarity AI as a company
   - Questions like "What is carbon intensity?", "How is ESG scored?"

4. **general** - Other questions or greetings
   - Generic questions, off-topic, unclear intent
   - Simple greetings or small talk

Also detect:
- Specific archetype mentioned (normalize to canonical name)
- Region mentioned (US or International/INT)

Current user context:
- Pre-selected archetype: {archetype}
- Pre-selected region: {region}
"""),
    ("human", "{query}")
])


def route_intent(state: PrismState) -> PrismState:
    """
    Classify user intent and route to appropriate retrieval strategy.

    Updates state with:
    - intent: classified intent
    - archetype: detected or pre-selected archetype
    - region: detected or pre-selected region
    - query: extracted query text
    """
    # Extract query from latest message
    latest_message = state["messages"][-1] if state["messages"] else None
    if not latest_message:
        logger.warning("No messages in state")
        state["intent"] = "general"
        state["query"] = ""
        return state

    query = latest_message.content if isinstance(latest_message, HumanMessage) else str(latest_message)
    state["query"] = query

    # Use LLM to classify intent
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(IntentClassification)

    chain = ROUTE_PROMPT | structured_llm

    try:
        result: IntentClassification = chain.invoke({
            "query": query,
            "archetype": state.get("archetype") or "Not specified",
            "region": state.get("region", "US"),
        })

        state["intent"] = result.intent

        # Update archetype if detected (and not already set)
        if result.detected_archetype:
            normalized = normalize_archetype(result.detected_archetype)
            if normalized:
                state["archetype"] = normalized

        # Update region if detected
        if result.detected_region:
            state["region"] = result.detected_region

        logger.info(f"Routed query to intent: {result.intent} (reasoning: {result.reasoning})")

    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        state["intent"] = "general"

    return state


def should_retrieve(state: PrismState) -> Literal["retrieve", "respond_directly"]:
    """
    Conditional edge: determine if retrieval is needed.

    Skip retrieval for simple greetings or when no real question is asked.
    """
    query = state.get("query", "").lower()

    # Simple patterns that don't need retrieval
    skip_patterns = [
        "hello", "hi", "hey", "good morning", "good afternoon",
        "thanks", "thank you", "bye", "goodbye",
    ]

    if any(pattern in query for pattern in skip_patterns) and len(query.split()) < 5:
        return "respond_directly"

    return "retrieve"


def get_retrieval_strategy(state: PrismState) -> str:
    """
    Determine which retrieval strategy to use based on intent.

    Returns the name of the retrieval node to route to.
    """
    intent = state.get("intent", "general")

    if intent == "archetype":
        return "retrieve_archetype"
    elif intent == "pipeline":
        return "retrieve_pipeline"
    elif intent == "clarity":
        return "retrieve_clarity"
    else:
        return "retrieve_general"
