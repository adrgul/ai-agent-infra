"""
Task extraction agent using LangChain and LLM.

This module contains the TaskExtractorAgent class that extracts
action items and tasks from meeting transcripts.
"""

import logging
from typing import Dict, Any, Optional, List

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..utils.config import Config
from ..utils.logger import get_logger
from ..models.task import Task, TaskList

logger = get_logger(__name__)


class TaskExtractorAgent:
    """Agent responsible for extracting action items and tasks."""

    def __init__(self, config: Config):
        """
        Initialize the task extractor agent.

        Args:
            config: Application configuration object
        """
        self.config = config
        self.llm = self._initialize_llm()
        self.prompt_template = self._create_prompt_template()
        logger.info("TaskExtractorAgent initialized successfully")

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
        """Create the prompt template for task extraction."""
        template = """
You are an expert at extracting action items and tasks from meeting transcripts.

Meeting Transcript:
{transcript}

Participants: {participants}

Extract all action items, tasks, and follow-ups mentioned in the meeting.
For each task, identify:
1. Task description/title
2. Person assigned (assignee)
3. Due date (if mentioned)
4. Priority level (High, Medium, Low)

Return the tasks in JSON format with the following structure:
{{
  "tasks": [
    {{
      "title": "Task description",
      "assignee": "Person name",
      "due_date": "YYYY-MM-DD",
      "priority": "High|Medium|Low"
    }}
  ]
}}

Only return valid JSON. If no tasks are found, return {{"tasks": []}}.
"""
        return ChatPromptTemplate.from_template(template)

    async def extract_tasks(
        self,
        transcript: str,
        participants: Optional[List[str]] = None,
        meeting_id: Optional[str] = None
    ) -> TaskList:
        """
        Extract tasks from a meeting transcript.

        Args:
            transcript: The meeting transcript text
            participants: List of meeting participants
            meeting_id: Meeting reference ID

        Returns:
            TaskList: Structured list of tasks

        Raises:
            ValueError: If transcript is empty
            RuntimeError: If LLM call fails
        """
        if not transcript or not transcript.strip():
            raise ValueError("Transcript cannot be empty")

        try:
            logger.info("Starting task extraction process")

            # Prepare participants string
            participants_str = ", ".join(participants) if participants else "Not specified"

            # Generate tasks using LLM
            prompt = self.prompt_template.format(
                transcript=transcript,
                participants=participants_str
            )
            response = await self.llm.ainvoke(prompt)

            # Parse and validate response
            tasks = self._parse_response(response.content, meeting_id)

            logger.info(f"Task extraction completed successfully. Found {len(tasks.tasks)} tasks")
            return tasks

        except Exception as e:
            logger.error(f"Task extraction failed: {str(e)}")
            raise RuntimeError(f"Failed to extract tasks: {str(e)}")

    def _parse_response(
        self,
        response: str,
        meeting_id: Optional[str]
    ) -> TaskList:
        """Parse LLM response into structured tasks."""
        import json
        from datetime import datetime
        import uuid

        try:
            # Parse JSON response
            data = json.loads(response.strip())

            tasks = []
            for task_data in data.get("tasks", []):
                # Generate task ID
                task_id = f"TASK-{str(uuid.uuid4())[:8].upper()}"

                # Create task object
                task = Task(
                    task_id=task_id,
                    title=task_data.get("title", ""),
                    assignee=task_data.get("assignee", ""),
                    due_date=task_data.get("due_date"),
                    priority=task_data.get("priority", "Medium"),
                    meeting_reference=meeting_id or ""
                )
                tasks.append(task)

            return TaskList(tasks=tasks)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            # Return empty task list if parsing fails
            return TaskList(tasks=[])
        except Exception as e:
            logger.error(f"Error parsing task response: {str(e)}")
            return TaskList(tasks=[])