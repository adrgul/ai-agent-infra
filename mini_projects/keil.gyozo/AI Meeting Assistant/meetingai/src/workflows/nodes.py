"""
Individual workflow nodes for LangGraph
"""

import logging
from typing import Dict, Any

from ..utils.logger import get_logger
from ..parsers import TextParser, MarkdownParser, DocxParser, SRTParser
from ..agents import SummarizerAgent, TaskExtractorAgent

logger = get_logger(__name__)


class ParseNode:
    """Node for parsing input documents"""

    def __init__(self, config):
        self.config = config
        self.parsers = {
            'txt': TextParser(),
            'md': MarkdownParser(),
            'docx': DocxParser(),
            'srt': SRTParser()
        }

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the input document"""
        logger.info("Executing parse node")

        document_path = state.get('document_path')
        if not document_path:
            raise ValueError("No document path provided")

        # Determine file type
        file_extension = document_path.split('.')[-1].lower()

        # Get appropriate parser
        parser = self.parsers.get(file_extension)
        if not parser:
            raise ValueError(f"No parser available for file type: {file_extension}")

        # Parse document
        document = parser.parse(document_path)

        state['parsed_text'] = document.page_content
        state['document_metadata'] = document.metadata

        logger.info(f"Successfully parsed document: {document_path}")
        return state


class SummarizeNode:
    """Node for generating meeting summaries"""

    def __init__(self, config):
        self.config = config
        self.summarizer = SummarizerAgent(config)

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meeting summary"""
        logger.info("Executing summarize node")

        transcript = state.get('parsed_text')
        participants = state.get('participants', [])

        if not transcript:
            raise ValueError("No transcript available for summarization")

        # Generate summary
        summary = await self.summarizer.summarize(transcript, participants)

        state['summary'] = summary.dict()

        logger.info("Summary generation completed")
        return state


class ExtractTasksNode:
    """Node for extracting action items"""

    def __init__(self, config):
        self.config = config
        self.task_extractor = TaskExtractorAgent(config)

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract action items and tasks"""
        logger.info("Executing task extraction node")

        transcript = state.get('parsed_text')
        participants = state.get('participants', [])
        meeting_id = state.get('summary', {}).get('meeting_id')

        if not transcript:
            raise ValueError("No transcript available for task extraction")

        # Extract tasks
        tasks = await self.task_extractor.extract_tasks(
            transcript, participants, meeting_id
        )

        state['tasks'] = [task.dict() for task in tasks.tasks]

        logger.info(f"Task extraction completed. Found {len(tasks.tasks)} tasks")
        return state


class ValidateNode:
    """Node for validating generated outputs"""

    def __init__(self, config):
        self.config = config

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated outputs"""
        logger.info("Executing validation node")

        errors = []

        # Validate summary
        summary = state.get('summary', {})
        if not summary.get('summary'):
            errors.append("Missing meeting summary")
        if not summary.get('meeting_id'):
            errors.append("Missing meeting ID")
        if not summary.get('participants'):
            errors.append("No participants specified")

        # Validate tasks
        tasks = state.get('tasks', [])
        for i, task in enumerate(tasks):
            if not task.get('title'):
                errors.append(f"Task {i+1} missing title")
            if not task.get('assignee'):
                errors.append(f"Task {i+1} missing assignee")

        state['errors'] = errors

        if errors:
            logger.warning(f"Validation found {len(errors)} errors: {errors}")
        else:
            logger.info("Validation passed")

        return state


class SaveNode:
    """Node for saving outputs"""

    def __init__(self, config):
        self.config = config

    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Save outputs to files and external systems"""
        logger.info("Executing save node")

        import json
        from pathlib import Path
        from datetime import datetime

        # Create output directory
        output_dir = Path(self.config.output.save_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp
        timestamp = datetime.now().strftime(self.config.output.timestamp_format)

        # Save JSON output
        meeting_data = {
            'summary': state.get('summary', {}),
            'tasks': state.get('tasks', []),
            'metadata': {
                'processed_at': datetime.now().isoformat(),
                'document_metadata': state.get('document_metadata', {})
            }
        }

        json_file = output_dir / f"meeting_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            if self.config.output.pretty_json:
                json.dump(meeting_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(meeting_data, f, ensure_ascii=False)

        # Save Markdown report
        md_file = output_dir / f"meeting_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_markdown_report(meeting_data))

        state['output_files'] = {
            'json': str(json_file),
            'markdown': str(md_file)
        }

        logger.info(f"Outputs saved to: {json_file}, {md_file}")
        return state

    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """Generate Markdown report from meeting data"""
        summary = data['summary']
        tasks = data['tasks']

        report = f"# {summary.get('title', 'Meeting Summary')}\n\n"
        report += f"**Date:** {summary.get('date', 'N/A')}\n\n"
        report += f"**Meeting ID:** {summary.get('meeting_id', 'N/A')}\n\n"

        # Participants
        participants = summary.get('participants', [])
        if participants:
            report += "## Participants\n\n"
            for participant in participants:
                report += f"- {participant}\n"
            report += "\n"

        # Summary
        if summary.get('summary'):
            report += "## Summary\n\n"
            report += f"{summary['summary']}\n\n"

        # Key Decisions
        decisions = summary.get('key_decisions', [])
        if decisions:
            report += "## Key Decisions\n\n"
            for decision in decisions:
                report += f"- {decision}\n"
            report += "\n"

        # Next Steps
        next_steps = summary.get('next_steps', [])
        if next_steps:
            report += "## Next Steps\n\n"
            for step in next_steps:
                report += f"- {step}\n"
            report += "\n"

        # Action Items
        if tasks:
            report += "## Action Items\n\n"
            report += "| Task | Assignee | Due Date | Priority | Status |\n"
            report += "|------|----------|----------|----------|--------|\n"
            for task in tasks:
                report += f"| {task.get('title', '')} | {task.get('assignee', '')} | {task.get('due_date', 'N/A')} | {task.get('priority', 'Medium')} | {task.get('status', 'to-do')} |\n"
            report += "\n"

        return report