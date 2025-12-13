"""
Main LangGraph workflow for meeting processing.

This module implements the complete meeting processing pipeline
as a LangGraph StateGraph.
"""

import logging
from typing import TypedDict, Annotated, Dict, Any
from datetime import datetime

from langgraph.graph import StateGraph, END

from ..utils.config import Config
from ..utils.logger import get_logger
from ..models.meeting import Meeting
from .nodes import ParseNode, SummarizeNode, ExtractTasksNode, ValidateNode, SaveNode

logger = get_logger(__name__)


class MeetingState(TypedDict):
    """State object for the meeting processing workflow."""

    document_path: str
    participants: list[str]
    parsed_text: str
    document_metadata: dict
    summary: dict
    tasks: list[dict]
    errors: list[str]
    output_files: dict


class MeetingProcessor:
    """Main workflow orchestrator using LangGraph."""

    def __init__(self, config: Config):
        """Initialize the meeting processor."""
        self.config = config
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(MeetingState)

        # Add nodes
        workflow.add_node("parse", ParseNode(self.config))
        workflow.add_node("summarize", SummarizeNode(self.config))
        workflow.add_node("extract_tasks", ExtractTasksNode(self.config))
        workflow.add_node("validate", ValidateNode(self.config))
        workflow.add_node("save", SaveNode(self.config))

        # Add edges
        workflow.add_edge("parse", "summarize")
        workflow.add_edge("summarize", "extract_tasks")
        workflow.add_edge("extract_tasks", "validate")
        workflow.add_conditional_edges(
            "validate",
            self._should_save,
            {
                "save": "save",
                "error": END
            }
        )
        workflow.add_edge("save", END)

        # Set entry point
        workflow.set_entry_point("parse")

        return workflow.compile()

    def _should_save(self, state: MeetingState) -> str:
        """Determine if outputs should be saved."""
        if state.get("errors"):
            logger.error(f"Workflow failed with errors: {state['errors']}")
            return "error"
        return "save"

    async def process(
        self,
        document_path: str,
        participants: list[str] = None,
        metadata: dict = None
    ) -> Meeting:
        """
        Process a meeting document through the complete workflow.

        Args:
            document_path: Path to the meeting document
            participants: List of meeting participants
            metadata: Additional metadata

        Returns:
            Meeting: Complete meeting object with summary and tasks
        """
        initial_state: MeetingState = {
            "document_path": document_path,
            "participants": participants or [],
            "parsed_text": "",
            "document_metadata": metadata or {},
            "summary": {},
            "tasks": [],
            "errors": [],
            "output_files": {}
        }

        final_state = await self.workflow.ainvoke(initial_state)

        # Check for errors
        if final_state.get("errors"):
            error_msg = f"Processing failed: {final_state['errors']}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return self._state_to_meeting(final_state)

    def _state_to_meeting(self, state: MeetingState) -> Meeting:
        """Convert workflow state to Meeting object."""
        from ..models.meeting import MeetingSummary
        from ..models.task import Task

        # Create summary object
        summary_data = state.get("summary", {})
        summary = MeetingSummary(**summary_data)

        # Create task objects
        tasks_data = state.get("tasks", [])
        tasks = [Task(**task_data) for task_data in tasks_data]

        # Create meeting object
        meeting = Meeting(
            summary=summary,
            tasks=tasks,
            metadata={
                "processed_at": datetime.now().isoformat(),
                "document_metadata": state.get("document_metadata", {}),
                "output_files": state.get("output_files", {})
            }
        )

        return meeting