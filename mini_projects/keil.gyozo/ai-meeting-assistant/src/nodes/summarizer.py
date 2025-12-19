"""
Summarizer node for generating executive summaries from meeting transcripts.

This node uses an LLM to create concise summaries and extract key points
from the parsed meeting transcript.
"""

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.models.schemas import GraphState, MeetingSummary


# System prompt for the summarizer
SUMMARIZER_SYSTEM_PROMPT = """You are an expert meeting analyst specializing in creating concise, actionable executive summaries.

Your task is to analyze meeting transcripts and extract:
1. A clear executive summary (2-4 sentences) that captures the essence of the meeting
2. Key discussion points and decisions made
3. Participants mentioned in the meeting (if identifiable)
4. Meeting date (if mentioned)

Focus on:
- Main topics discussed
- Important decisions made
- Key insights or conclusions
- Critical information stakeholders need to know

Be concise and professional. Avoid filler words and unnecessary details."""


# User prompt template
SUMMARIZER_USER_PROMPT = """Analyze the following meeting transcript and provide a structured summary.

Meeting Transcript:
{transcript}

Please provide your response in the following JSON format:
{{
    "summary": "2-4 sentence executive summary here",
    "key_points": ["key point 1", "key point 2", "key point 3"],
    "participants": ["participant 1", "participant 2"] (or null if not identifiable),
    "meeting_date": "date if mentioned" (or null if not mentioned)
}}

Ensure the summary is clear, concise, and captures the most important aspects of the meeting."""


def create_summarizer_chain(llm: ChatOpenAI):
    """
    Create the summarizer LangChain chain.

    Args:
        llm: The ChatOpenAI language model instance

    Returns:
        A LangChain chain for generating meeting summaries
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", SUMMARIZER_SYSTEM_PROMPT),
        ("user", SUMMARIZER_USER_PROMPT)
    ])

    output_parser = JsonOutputParser(pydantic_object=MeetingSummary)

    chain = prompt | llm | output_parser

    return chain


def summarize_meeting(state: GraphState, llm: ChatOpenAI) -> Dict[str, Any]:
    """
    Generate an executive summary from the meeting transcript.

    This node uses an LLM to create a structured summary including
    key points, participants, and the meeting date.

    Args:
        state: The current graph state with parsed transcript
        llm: The ChatOpenAI language model instance

    Returns:
        Dict with updated state containing the summary
    """
    transcript = state.parsed_transcript or state.transcript

    try:
        # Create the chain
        chain = create_summarizer_chain(llm)

        # Invoke the chain
        result = chain.invoke({"transcript": transcript})

        # Parse the result into MeetingSummary model
        summary = MeetingSummary(**result)

        return {
            "summary": summary,
            "errors": state.errors
        }

    except Exception as e:
        error_msg = f"Summarizer error: {str(e)}"
        return {
            "summary": None,
            "errors": state.errors + [error_msg]
        }
