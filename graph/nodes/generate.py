"""Response generation node for Prism RAG workflow."""

import logging
import re
import time
from typing import Literal, Optional

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..state import PrismState
from .grade import get_relevant_docs

logger = logging.getLogger(__name__)


def load_v1_prompt(prompt_name: str) -> Optional[ChatPromptTemplate]:
    """
    Load a V1 prompt from the prompts registry and convert to LangChain format.

    V1 prompts use LlamaIndex placeholders: {context_str}, {query_str}
    V2 uses LangChain placeholders: {context}, {query}

    IMPORTANT: Injects brevity constraints to match V2's concise response style.
    """
    try:
        from retrieval.prompts import PROMPTS

        if prompt_name not in PROMPTS:
            logger.warning(f"Prompt '{prompt_name}' not found in registry")
            return None

        config = PROMPTS[prompt_name]
        template = config.template

        # Convert LlamaIndex placeholders to LangChain format
        template = template.replace("{context_str}", "{context}")
        template = template.replace("{query_str}", "{query}")

        # Extract system content (before "User Question:" if present)
        system_content = template.split("User Question:")[0] if "User Question:" in template else template

        # Inject brevity constraints to match V2 concise style
        brevity_suffix = """

RESPONSE LENGTH (STRICT):
- Maximum 80 words. No exceptions.
- Lead with the key insight or number.
- Skip preamble ("Based on...", "According to...", "The context shows...").
- Users can ask follow-up questions for more detail."""

        system_content = system_content.rstrip() + brevity_suffix

        # Build ChatPromptTemplate from the V1 template
        return ChatPromptTemplate.from_messages([
            ("system", system_content),
            ("human", "{query}")
        ])

    except ImportError as e:
        logger.error(f"Failed to import prompts module: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load prompt '{prompt_name}': {e}")
        return None


# Intent-specific prompts
# NOTE: All prompts enforce 80-word max for speed. Users can ask follow-ups.

ARCHETYPE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are Prism, AlTi's investment research assistant.

Archetype: {archetype} | Region: {region}

Rules:
- Maximum 80 words. No exceptions.
- Lead with the key number or insight.
- No preamble ("Based on...", "According to...").

Context:
{context}
"""),
    ("human", "{query}")
])

PIPELINE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are Prism, AlTi's investment research assistant.

Rules:
- Maximum 80 words. No exceptions.
- Lead with key details: minimums, dates, asset classes.
- No preamble ("Based on...", "According to...").

Context:
{context}
"""),
    ("human", "{query}")
])

CLARITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are Prism, AlTi's investment research assistant.

Rules:
- Maximum 80 words. No exceptions.
- Define the metric directly, include formula if simple.
- No preamble ("Based on...", "According to...").

Context:
{context}
"""),
    ("human", "{query}")
])

GENERAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are Prism, AlTi's investment research assistant.

Rules:
- Maximum 80 words. No exceptions.
- Lead with the key insight.
- No preamble ("Based on...", "According to...").
- Say "I don't have that information" if not in context.

Context:
{context}
"""),
    ("human", "{query}")
])


def get_prompt_for_intent(intent: str) -> ChatPromptTemplate:
    """Get the appropriate prompt template for the intent."""
    prompts = {
        "archetype": ARCHETYPE_PROMPT,
        "pipeline": PIPELINE_PROMPT,
        "clarity": CLARITY_PROMPT,
        "general": GENERAL_PROMPT,
    }
    return prompts.get(intent, GENERAL_PROMPT)


def format_context(docs: list) -> str:
    """Format retrieved documents as context string."""
    if not docs:
        return "No relevant documents found."

    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("file_name", "Unknown")
        doc_type = doc.metadata.get("document_type", "document")
        content = doc.page_content[:1500]  # Truncate long docs

        context_parts.append(f"[Source {i}: {source} ({doc_type})]\n{content}")

    return "\n\n---\n\n".join(context_parts)


def generate_response(state: PrismState) -> PrismState:
    """
    Generate response using retrieved context.

    Uses custom prompts from prompt_name if provided (v1 compatibility),
    otherwise falls back to intent-specific prompts.
    """
    start_time = time.perf_counter()
    query = state.get("query", "")
    intent = state.get("intent", "general")
    prompt_name = state.get("prompt_name")

    # Get relevant documents
    relevant_docs = get_relevant_docs(state)
    if not relevant_docs:
        # Fall back to all retrieved docs if grading filtered everything
        relevant_docs = state.get("retrieved_docs", [])

    # Format context
    context = format_context(relevant_docs)

    # Get appropriate prompt - prefer custom prompt_name if provided
    prompt = None
    if prompt_name:
        prompt = load_v1_prompt(prompt_name)
        if prompt:
            logger.info(f"Using custom prompt: {prompt_name}")
        else:
            logger.warning(f"Failed to load prompt '{prompt_name}', falling back to intent-based")

    if prompt is None:
        prompt = get_prompt_for_intent(intent)
        logger.info(f"Using intent-based prompt for: {intent}")

    # Generate response
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    chain = prompt | llm

    try:
        response = chain.invoke({
            "query": query,
            "context": context,
            "archetype": state.get("archetype") or "Not specified",
            "region": state.get("region", "US"),
        })

        state["generation"] = response.content

        # Add AI message to conversation history
        state["messages"].append(AIMessage(content=response.content))

        # Extract sources for citation
        state["sources"] = [
            {
                "file_name": doc.metadata.get("file_name", "Unknown"),
                "document_type": doc.metadata.get("document_type", "unknown"),
                "relevance": next(
                    (gd["score"] for gd in state.get("graded_docs", [])
                     if gd["document"] == doc),
                    0.5
                )
            }
            for doc in relevant_docs[:5]
        ]

        state["turn_count"] = state.get("turn_count", 0) + 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        prompt_used = prompt_name if prompt_name else f"intent:{intent}"
        logger.info(f"Generated response in {elapsed_ms:.0f}ms using prompt={prompt_used}, sources={len(state['sources'])}")

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        state["generation"] = "I apologize, but I encountered an error generating a response. Please try rephrasing your question."
        state["sources"] = []

    return state


class HallucinationCheck(BaseModel):
    """Structured output for hallucination checking."""

    grounded: Literal["grounded", "not_grounded", "uncertain"] = Field(
        description="Whether the response is grounded in the context"
    )
    problematic_claims: list[str] = Field(
        default=[],
        description="List of claims that are not supported by context"
    )


HALLUCINATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a fact-checker for an investment research assistant.

Your task is to verify that the generated response is grounded in the provided context.

Check if:
1. All specific claims (numbers, percentages, fund names) are in the context
2. No information is made up or hallucinated
3. The response stays within the scope of the context

Be strict - if any claim cannot be verified from context, mark as uncertain.
"""),
    ("human", """Context provided:
{context}

Generated response:
{response}

Is this response grounded in the context?""")
])


def check_hallucination(state: PrismState) -> PrismState:
    """
    Self-RAG: Check if response is grounded in retrieved context.

    This is a Self-RAG reflection step to detect hallucinations.
    """
    generation = state.get("generation", "")
    relevant_docs = get_relevant_docs(state)
    context = format_context(relevant_docs)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(HallucinationCheck)
    chain = HALLUCINATION_PROMPT | structured_llm

    try:
        result: HallucinationCheck = chain.invoke({
            "context": context,
            "response": generation,
        })

        state["hallucination_check"] = result.grounded

        if result.grounded == "not_grounded":
            logger.warning(f"Hallucination detected: {result.problematic_claims}")
            # Could trigger regeneration or add disclaimer
            state["generation"] += "\n\n*Note: Some information in this response may need verification.*"

    except Exception as e:
        logger.error(f"Hallucination check failed: {e}")
        state["hallucination_check"] = "uncertain"

    return state


def respond_directly(state: PrismState) -> PrismState:
    """
    Generate a direct response without retrieval.

    Used for greetings, simple questions, off-topic queries.
    """
    query = state.get("query", "")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    response = llm.invoke(
        f"""You are Prism, AlTi's Impact investment research assistant.
The user said: "{query}"

Respond briefly and helpfully. If they're greeting you, greet them back and
offer to help with investment models, ESG metrics, or pipeline opportunities.
"""
    )

    state["generation"] = response.content
    state["messages"].append(AIMessage(content=response.content))
    state["sources"] = []
    state["turn_count"] = state.get("turn_count", 0) + 1

    return state
