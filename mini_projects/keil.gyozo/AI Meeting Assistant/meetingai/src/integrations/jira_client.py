"""
Jira API integration client
"""

import logging
from typing import Dict, Any, Optional, List

from ..utils.config import Config
from ..utils.logger import get_logger
from ..models.task import Task

logger = get_logger(__name__)


class JiraClient:
    """Client for interacting with Jira REST API"""

    def __init__(self, config: Config):
        """
        Initialize Jira client

        Args:
            config: Application configuration
        """
        self.config = config
        self.base_url = config.integrations.jira.url.rstrip('/')
        self.auth = None

        if config.integrations.jira.enabled:
            self._setup_auth()

    def _setup_auth(self):
        """Setup authentication"""
        if not self.config.integrations.jira.api_token:
            raise ValueError("Jira API token not configured")

        self.auth = (
            self.config.integrations.jira.user_email,
            self.config.integrations.jira.api_token.get_secret_value()
        )

    async def create_issue(self, task: Task) -> Optional[str]:
        """
        Create a Jira issue from a task

        Args:
            task: Task object to create issue from

        Returns:
            Issue key if successful, None otherwise
        """
        if not self.config.integrations.jira.enabled:
            logger.info("Jira integration disabled, skipping issue creation")
            return None

        try:
            import requests

            # Prepare issue data
            issue_data = {
                "fields": {
                    "project": {
                        "key": self.config.integrations.jira.project_key
                    },
                    "summary": task.title,
                    "description": task.description or task.title,
                    "issuetype": {
                        "name": self.config.integrations.jira.issue_type
                    },
                    "assignee": {
                        "name": self._get_jira_username(task.assignee)
                    },
                    "priority": {
                        "name": self._map_priority(task.priority)
                    }
                }
            }

            # Add due date if available
            if task.due_date:
                issue_data["fields"]["duedate"] = task.due_date

            # Create issue
            url = f"{self.base_url}/rest/api/2/issue"
            response = requests.post(
                url,
                json=issue_data,
                auth=self.auth,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 201:
                issue_key = response.json()["key"]
                logger.info(f"Created Jira issue: {issue_key}")
                return issue_key
            else:
                logger.error(f"Failed to create Jira issue: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error creating Jira issue: {str(e)}")
            return None

    async def create_issues_batch(self, tasks: List[Task]) -> Dict[str, str]:
        """
        Create multiple Jira issues

        Args:
            tasks: List of tasks to create issues for

        Returns:
            Dictionary mapping task IDs to issue keys
        """
        results = {}
        for task in tasks:
            issue_key = await self.create_issue(task)
            if issue_key:
                results[task.task_id] = issue_key

        return results

    def _get_jira_username(self, assignee: str) -> str:
        """
        Map assignee name to Jira username

        Args:
            assignee: Assignee name from task

        Returns:
            Jira username
        """
        # Simple mapping - in production, you might have a user mapping table
        # For now, assume assignee names are Jira usernames
        return assignee.lower().replace(' ', '.')

    def _map_priority(self, priority: str) -> str:
        """
        Map task priority to Jira priority

        Args:
            priority: Task priority

        Returns:
            Jira priority name
        """
        priority_mapping = {
            "P1": "Highest",
            "High": "High",
            "P2": "High",
            "Medium": "Medium",
            "P3": "Medium",
            "Low": "Low"
        }

        return priority_mapping.get(priority, "Medium")

    async def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """
        Get issue details from Jira

        Args:
            issue_key: Jira issue key

        Returns:
            Issue data if found
        """
        if not self.config.integrations.jira.enabled:
            return None

        try:
            import requests

            url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
            response = requests.get(url, auth=self.auth)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get Jira issue {issue_key}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting Jira issue: {str(e)}")
            return None