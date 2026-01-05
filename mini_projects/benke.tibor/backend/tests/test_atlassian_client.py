"""
Unit tests for Atlassian client (Confluence + Jira).

NOTE: After IT domain refactoring:
- Confluence methods are only used during INDEXING (sync_confluence_it_policy.py)
- Runtime IT queries use QDRANT semantic search (not direct Confluence API calls)
- Jira ticket creation is still used at RUNTIME

Test categories:
1. Singleton pattern (infrastructure)
2. Jira integration (runtime) - CRITICAL
3. Confluence integration (indexing-time) - Optional, integration tests
"""
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from infrastructure.atlassian_client import AtlassianClient


class TestAtlassianClient(unittest.TestCase):
    """Test Atlassian client initialization and methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Reset singleton
        AtlassianClient._instance = None
        
        # Set environment variables for testing
        import os
        os.environ['CONFLUENCE_API_TOKEN'] = 'test-confluence-token'
        os.environ['JIRA_API_TOKEN'] = 'test-jira-token'
        os.environ['ATLASSIAN_EMAIL'] = 'test@example.com'
    
    def tearDown(self):
        """Clean up event loop."""
        self.loop.close()
    
    def test_singleton_pattern(self):
        """Test that AtlassianClient is a singleton."""
        client1 = AtlassianClient()
        client2 = AtlassianClient()
        
        self.assertIs(client1, client2)
    
    @patch('infrastructure.atlassian_client.httpx.AsyncClient')
    async def async_test_get_it_policy_content(self, mock_client_class):
        """Test retrieving IT Policy from Confluence."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "body": {
                "storage": {
                    "value": "<h1>VPN Issues</h1><p>Check client is running</p><h2>Email Problems</h2><p>Contact IT</p>"
                }
            }
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        client = AtlassianClient()
        
        # Act
        sections = await client.get_it_policy_content()
        
        # Assert
        self.assertIsInstance(sections, dict)
        self.assertGreater(len(sections), 0)
        mock_client.get.assert_called_once()
    
    def test_get_it_policy_content(self):
        """Sync wrapper for async test."""
        self.loop.run_until_complete(self.async_test_get_it_policy_content())
    
    async def async_test_find_relevant_section(self):
        """Test finding relevant section based on query."""
        # Arrange
        sections = {
            "1. VPN Problémák [IT-KB-234]": "VPN kapcsolódási hibák esetén ellenőrizd a kliens fut-e.",
            "2. Email Beállítások": "Outlook konfigurálása: SMTP port 587",
            "3. Jelszókezelés": "Jelszó változtatás 90 naponta kötelező."
        }
        
        client = AtlassianClient()
        
        # Act
        result = await client.find_relevant_section("VPN problémám van", sections)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["section_id"], "IT-KB-234")
        self.assertIn("VPN", result["section_title"])
    
    def test_find_relevant_section(self):
        """Sync wrapper for async test."""
        self.loop.run_until_complete(self.async_test_find_relevant_section())
    
    async def async_test_get_contact_info(self):
        """Test extracting contact information."""
        # Arrange
        sections = {
            "1. VPN": "VPN info",
            "14. Kapcsolattartás és támogatás": "IT Helpdesk: it@example.com, Tel: +36 1 234 5678"
        }
        
        client = AtlassianClient()
        
        # Act
        contact_info = await client.get_contact_info(sections)
        
        # Assert
        self.assertIsNotNone(contact_info)
        self.assertIn("Helpdesk", contact_info)
    
    def test_get_contact_info(self):
        """Sync wrapper for async test."""
        self.loop.run_until_complete(self.async_test_get_contact_info())
    
    @patch('infrastructure.atlassian_client.httpx.AsyncClient')
    async def async_test_create_jira_ticket(self, mock_client_class):
        """Test creating a Jira ticket."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "key": "SCRUM-123"
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        client = AtlassianClient()
        
        # Act
        result = await client.create_jira_ticket(
            summary="VPN issue",
            description="Cannot connect to VPN",
            issue_type="Task",
            priority="High"
        )
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["key"], "SCRUM-123")
        self.assertIn("SCRUM-123", result["url"])
        mock_client.post.assert_called_once()
    
    def test_create_jira_ticket(self):
        """Sync wrapper for async test."""
        self.loop.run_until_complete(self.async_test_create_jira_ticket())
    
    @patch('infrastructure.atlassian_client.httpx.AsyncClient')
    async def async_test_confluence_api_error(self, mock_client_class):
        """Test handling Confluence API errors."""
        # Arrange
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Network error")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        client = AtlassianClient()
        
        # Act
        sections = await client.get_it_policy_content()
        
        # Assert
        self.assertEqual(sections, {})  # Should return empty dict on error
    
    def test_confluence_api_error(self):
        """Sync wrapper for async test."""
        self.loop.run_until_complete(self.async_test_confluence_api_error())


if __name__ == '__main__':
    unittest.main()
