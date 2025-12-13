"""
Meeting summarizer agent using LangChain and LLM.

This module contains the SummarizerAgent class that generates
executive summaries from meeting transcripts.
"""

import logging
from typing import Dict, Any, Optional, List

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage
from pydantic import BaseModel, Field

from ..utils.config import Config
from ..utils.logger import get_logger
from ..models.meeting import MeetingSummary

logger = get_logger(__name__)


class SummarizerAgent:
    """Agent responsible for generating meeting summaries."""

    def __init__(self, config: Config):
        """
        Initialize the summarizer agent.

        Args:
            config: Application configuration object
        """
        self.config = config
        self.llm = self._initialize_llm()
        self.prompt_template = self._create_prompt_template()
        logger.info("SummarizerAgent initialized successfully")

    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the language model."""
        if self.config.llm.provider.lower() == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=self.config.llm.model,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                api_key=self.config.llm.api_key.get_secret_value() if self.config.llm.api_key else None,
                timeout=self.config.llm.timeout
            )
        elif self.config.llm.provider.lower() == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=self.config.llm.model,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                api_key=self.config.llm.api_key.get_secret_value() if self.config.llm.api_key else None,
                timeout=self.config.llm.timeout
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.llm.provider}")

    def _create_prompt_template(self) -> ChatPromptTemplate:
        """Create the prompt template for summarization."""
        template = """
You are an expert meeting summarizer. Given the following meeting transcript,
create a concise executive summary.

Meeting Transcript:
{transcript}

Participants: {participants}

Generate a summary that includes:
1. Main topics discussed
2. Key decisions made
3. Next steps identified

Return the summary in a clear, professional format.
Keep the summary concise but comprehensive.
"""
        return ChatPromptTemplate.from_template(template)

    async def summarize(
        self,
        transcript: str,
        participants: Optional[List[str]] = None
    ) -> MeetingSummary:
        """
        Generate a summary from a meeting transcript.

        Args:
            transcript: The meeting transcript text
            participants: List of meeting participants

        Returns:
            MeetingSummary: Structured summary object

        Raises:
            ValueError: If transcript is empty
            RuntimeError: If LLM call fails
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")

        try:
            logger.info("Starting summarization process")

            # Prepare participants string
            participants_str = ", ".join(participants) if participants else "Not specified"

            # Generate summary using LLM
            prompt = self.prompt_template.format(
                transcript=transcript,
                participants=participants_str
            )
            response = await self.llm.ainvoke(prompt)

            # Parse and validate response
            summary = self._parse_response(response.content, participants)

            logger.info("Summarization completed successfully")
            return summary

        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            raise RuntimeError(f"Failed to generate summary: {str(e)}")

    def _parse_response(
        self,
        response: str,
        participants: Optional[List[str]]
    ) -> MeetingSummary:
        """Parse LLM response into structured summary."""
        # Extract key information from response
        lines = response.strip().split('\n')

        # Simple parsing - in a real implementation, you might use more sophisticated parsing
        summary_text = response.strip()
        key_decisions = []
        next_steps = []

        # Look for common patterns
        for line in lines:
            line_lower = line.lower()
            if "decis" in line_lower and ("made" in line_lower or "took" in line_lower):
                key_decisions.append(line.strip())
            elif "next" in line_lower and ("step" in line_lower or "action" in line_lower):
                next_steps.append(line.strip())

        # If no structured extraction, use the whole response as summary
        if not key_decisions and not next_steps:
            summary_text = response.strip()
        else:
            # Remove extracted lines from summary
            remaining_lines = []
            for line in lines:
                if line.strip() not in key_decisions and line.strip() not in next_steps:
                    remaining_lines.append(line)
            summary_text = '\n'.join(remaining_lines).strip()

        # Generate meeting ID
        from datetime import datetime
        import uuid
        meeting_id = f"MTG-{datetime.now().strftime('%Y-%m-%d')}-{str(uuid.uuid4())[:8].upper()}"

        return MeetingSummary(
            meeting_id=meeting_id,
            title="Meeting Summary",
            date=datetime.now().strftime('%Y-%m-%d'),
            participants=participants or [],
            summary=summary_text,
            key_decisions=key_decisions,
            next_steps=next_steps
        )