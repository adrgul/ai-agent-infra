"""
Slack integration client
"""

import logging
from typing import Dict, Any, Optional, List

from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SlackClient:
    """Client for Slack webhook integrations"""

    def __init__(self, config: Config):
        """
        Initialize Slack client

        Args:
            config: Application configuration
        """
        self.config = config
        self.webhook_url = config.integrations.slack.webhook_url

    async def send_meeting_notification(
        self,
        meeting_summary: Dict[str, Any],
        tasks: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Send meeting summary notification to Slack

        Args:
            meeting_summary: Meeting summary data
            tasks: List of task data

        Returns:
            True if successful
        """
        if not self.config.integrations.slack.enabled or not self.webhook_url:
            logger.info("Slack integration disabled or not configured")
            return False

        try:
            import requests

            # Build message
            message = self._build_meeting_message(meeting_summary, tasks)

            # Send webhook
            response = requests.post(
                self.webhook_url.get_secret_value(),
                json=message,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
                return True
            else:
                logger.error(f"Slack webhook failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False

    async def send_task_notification(self, task: Dict[str, Any]) -> bool:
        """
        Send task assignment notification

        Args:
            task: Task data

        Returns:
            True if successful
        """
        if not self.config.integrations.slack.enabled or not self.webhook_url:
            return False

        try:
            import requests

            message = self._build_task_message(task)

            response = requests.post(
                self.webhook_url.get_secret_value(),
                json=message,
                headers={'Content-Type': 'application/json'}
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Error sending task notification: {str(e)}")
            return False

    def _build_meeting_message(
        self,
        summary: Dict[str, Any],
        tasks: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build Slack message for meeting summary"""
        message = {
            "text": f"📋 Meeting Summary: {summary.get('title', 'Untitled')}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"📋 {summary.get('title', 'Meeting Summary')}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Date:* {summary.get('date', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Meeting ID:* {summary.get('meeting_id', 'N/A')}"
                        }
                    ]
                }
            ]
        }

        # Add participants
        participants = summary.get('participants', [])
        if participants:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Participants:* {', '.join(participants)}"
                }
            })

        # Add summary
        if summary.get('summary'):
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{summary['summary']}"
                }
            })

        # Add tasks
        if tasks:
            task_lines = []
            for task in tasks[:5]:  # Limit to 5 tasks
                assignee = task.get('assignee', 'Unassigned')
                title = task.get('title', 'Untitled')
                if self.config.integrations.slack.mention_assignees:
                    task_lines.append(f"• <@{assignee}> {title}")
                else:
                    task_lines.append(f"• {assignee}: {title}")

            if len(tasks) > 5:
                task_lines.append(f"• ... and {len(tasks) - 5} more tasks")

            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Action Items:*\n" + "\n".join(task_lines)
                }
            })

        return message

    def _build_task_message(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Build Slack message for task assignment"""
        title = task.get('title', 'Untitled Task')
        assignee = task.get('assignee', 'Unassigned')

        message = {
            "text": f"📝 New Task Assigned: {title}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📝 New Task Assigned"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Task:* {title}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Assignee:* {assignee}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Due Date:* {task.get('due_date', 'N/A')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Priority:* {task.get('priority', 'Medium')}"
                        }
                    ]
                }
            ]
        }

        # Add description if available
        if task.get('description'):
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{task['description']}"
                }
            })

        return message