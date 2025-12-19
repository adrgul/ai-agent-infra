"""
Parser node for cleaning and preprocessing meeting transcripts.

This node handles the initial processing of raw meeting transcripts,
including cleaning, formatting, and basic text normalization.
"""

import re
from typing import Dict, Any
from src.models.schemas import GraphState


def parse_transcript(state: GraphState) -> Dict[str, Any]:
    """
    Parse and clean the raw meeting transcript.

    This node performs basic text processing to prepare the transcript
    for analysis by the LLM nodes.

    Args:
        state: The current graph state containing the raw transcript

    Returns:
        Dict with updated state containing parsed_transcript
    """
    transcript = state.transcript

    try:
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', transcript)

        # Remove multiple newlines (keep paragraph structure)
        cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)

        # Remove timestamps if present (e.g., [00:12:34] or (12:34))
        cleaned = re.sub(r'\[?\d{1,2}:\d{2}(?::\d{2})?\]?', '', cleaned)
        cleaned = re.sub(r'\(\d{1,2}:\d{2}(?::\d{2})?\)', '', cleaned)

        # Remove common filler words and artifacts
        filler_words = [
            r'\buh+\b', r'\bum+\b', r'\ber+\b', r'\bah+\b',
            r'\bhm+\b', r'\bmm+\b'
        ]
        for filler in filler_words:
            cleaned = re.sub(filler, '', cleaned, flags=re.IGNORECASE)

        # Normalize speaker labels (e.g., "Speaker 1:", "John:", etc.)
        cleaned = re.sub(r'\n([A-Z][a-zA-Z\s]+):\s*', r'\n\1: ', cleaned)

        # Remove extra spaces
        cleaned = re.sub(r' +', ' ', cleaned)

        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()

        # Basic validation
        if not cleaned or len(cleaned) < 10:
            raise ValueError("Transcript is empty or too short after cleaning")

        return {
            "parsed_transcript": cleaned,
            "errors": state.errors
        }

    except Exception as e:
        error_msg = f"Parser error: {str(e)}"
        return {
            "parsed_transcript": transcript,  # Use original if parsing fails
            "errors": state.errors + [error_msg]
        }


def validate_transcript(state: GraphState) -> Dict[str, Any]:
    """
    Validate the transcript meets minimum requirements.

    This optional node can be used to check if the transcript
    has sufficient content for processing.

    Args:
        state: The current graph state

    Returns:
        Dict with validation status added to state
    """
    transcript = state.parsed_transcript or state.transcript
    errors = list(state.errors)

    # Check minimum length
    if len(transcript) < 50:
        errors.append("Transcript is too short (minimum 50 characters)")

    # Check if transcript has any meaningful content
    words = transcript.split()
    if len(words) < 10:
        errors.append("Transcript has too few words (minimum 10 words)")

    # Check for speaker information (optional)
    has_speakers = bool(re.search(r'[A-Z][a-zA-Z\s]+:', transcript))
    if not has_speakers:
        # This is a warning, not an error
        pass

    return {
        "errors": errors
    }
