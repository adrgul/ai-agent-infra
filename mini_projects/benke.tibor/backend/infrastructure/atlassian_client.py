"""
Atlassian API client for Confluence and Jira integration.
Handles IT policy retrieval from Confluence and ticket creation in Jira.
"""
import os
import logging
from typing import Dict, Optional, List
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AtlassianClient:
    """
    Singleton client for Atlassian Cloud (Confluence + Jira) API.
    Used for IT domain: retrieve IT policies and create support tickets.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.base_url = os.getenv("ATLASSIAN_BASE_URL", "https://benketibor.atlassian.net")
        self.confluence_token = os.getenv("CONFLUENCE_API_TOKEN")
        self.confluence_email = os.getenv("CONFLUENCE_EMAIL", "")
        self.jira_token = os.getenv("JIRA_API_TOKEN")
        self.jira_email = os.getenv("JIRA_EMAIL", "")
        
        # IT Policy Confluence page
        self.it_policy_page_id = "6324226"
        
        # Jira project
        self.jira_project_key = "SCRUM"
        
        self._initialized = True
        logger.info(f"✅ AtlassianClient initialized (base: {self.base_url})")
    
    async def get_it_policy_content(self) -> Dict[str, str]:
        """
        Retrieve IT Policy page content from Confluence.
        
        Returns:
            Dict with sections: {section_id: content}
        """
        if not self.confluence_token:
            logger.error("CONFLUENCE_API_TOKEN not set")
            return {}
        
        url = f"{self.base_url}/wiki/api/v2/pages/{self.it_policy_page_id}?body-format=storage"
        
        # Confluence Cloud uses Basic Auth: email:api_token (base64 encoded)
        import base64
        auth_string = f"{self.confluence_email}:{self.confluence_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                body_storage = data.get("body", {}).get("storage", {}).get("value", "")
                
                # Parse HTML content
                sections = self._parse_it_policy_sections(body_storage)
                
                logger.info(f"✅ Retrieved IT Policy page (sections: {len(sections)})")
                return sections
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrieving Confluence page: {e.response.status_code} {e.response.text}")
            return {}
        except Exception as e:
            logger.error(f"Failed to retrieve IT Policy: {e}")
            return {}
    
    def _parse_it_policy_sections(self, html_content: str) -> Dict[str, str]:
        """
        Parse Confluence HTML storage format into sections.
        Extract headings and their content, including section IDs.
        
        Returns:
            Dict of {section_title: section_content}
        """
        import re
        
        soup = BeautifulSoup(html_content, 'html.parser')
        sections = {}
        
        # Find all headings (h1, h2, h3)
        headings = soup.find_all(['h1', 'h2', 'h3'])
        
        last_section_id = None
        for i, heading in enumerate(headings):
            section_title = heading.get_text(strip=True)
            
            # Extract section ID if present (e.g., [IT-KB-234])
            section_id_match = re.search(r'\[([A-Z]+-[A-Z]+-\d+)\]', section_title)
            section_id = section_id_match.group(1) if section_id_match else None

            # Inherit last seen section ID for subheadings without explicit ID
            if not section_id:
                section_id = last_section_id
            else:
                last_section_id = section_id
            
            # Get content until next heading
            content_parts = []
            for sibling in heading.find_next_siblings():
                if sibling.name in ['h1', 'h2', 'h3']:
                    break
                content_parts.append(sibling.get_text(strip=True))
            
            section_content = '\n'.join(content_parts)
            
            # Store content WITH section_id prepended for RAG context
            if section_id and not section_content.startswith(f"[{section_id}]"):
                section_content = f"[{section_id}] {section_content}"
            
            sections[section_title] = section_content
        
        return sections
    
    async def find_relevant_section(self, query: str, sections: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Find the most relevant section based on query keywords.
        
        Args:
            query: User's question
            sections: IT policy sections
            
        Returns:
            Dict with section_title, content, section_id (if identifiable)
        """
        query_lower = query.lower()
        
        # Keyword mapping for common IT issues
        keyword_map = {
            "vpn": ["vpn", "virtual private network", "távoli hozzáférés"],
            "jelszó": ["jelszó", "password", "bejelentkezés"],
            "email": ["email", "e-mail", "levelezés", "outlook"],
            "laptop": ["laptop", "számítógép", "eszköz", "hardver"],
            "szoftver": ["szoftver", "software", "alkalmazás", "program"],
            "hálózat": ["hálózat", "network", "wifi", "internet"],
        }
        
        # Score sections based on keyword matches
        scored_sections = []
        for title, content in sections.items():
            title_lower = title.lower()
            content_lower = content.lower()
            score = 0
            
            # Direct query word matching
            for word in query_lower.split():
                if len(word) > 3:  # Skip short words
                    if word in title_lower:
                        score += 10
                    if word in content_lower:
                        score += 1
            
            # Category matching
            for category, keywords in keyword_map.items():
                if any(kw in query_lower for kw in keywords):
                    if any(kw in title_lower or kw in content_lower for kw in keywords):
                        score += 5
            
            if score > 0:
                scored_sections.append((title, content, score))
        
        if not scored_sections:
            return None
        
        # Get best match
        scored_sections.sort(key=lambda x: x[2], reverse=True)
        best_title, best_content, best_score = scored_sections[0]
        
        # Try to extract section ID from title (e.g., "[IT-KB-234]")
        section_id = None
        if "[" in best_title and "]" in best_title:
            section_id = best_title[best_title.find("[")+1:best_title.find("]")]
        
        logger.info(f"📍 Best match: '{best_title}' (score: {best_score})")
        
        return {
            "section_title": best_title,
            "content": best_content,
            "section_id": section_id or f"IT-SEC-{hash(best_title) % 1000:03d}"
        }
    
    async def get_contact_info(self, sections: Dict[str, str]) -> Optional[str]:
        """
        Extract contact information from IT Policy (usually section 14).
        
        Returns:
            Contact information string or None
        """
        # Look for contact/support section
        for title, content in sections.items():
            if any(kw in title.lower() for kw in ["kapcsolat", "contact", "elérhetőség", "support"]):
                return content
        
        return None
    
    async def create_jira_ticket(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium"
    ) -> Optional[Dict[str, str]]:
        """
        Create a Jira ticket in the SCRUM project.
        
        Args:
            summary: Ticket summary/title
            description: Detailed description
            issue_type: Task, Bug, Story, etc.
            priority: Highest, High, Medium, Low, Lowest
            
        Returns:
            Dict with ticket info {key, url} or None on failure
        """
        if not self.jira_token:
            logger.error("JIRA_API_TOKEN not set")
            return None
        
        url = f"{self.base_url}/rest/api/3/issue"
        
        # Jira Cloud uses Basic Auth: email:api_token (base64 encoded)
        import base64
        auth_string = f"{self.jira_email}:{self.jira_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        logger.info(f"🔐 Jira Auth - Email: {self.jira_email[:30]}... Token: {self.jira_token[:20]}...")
        
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "fields": {
                "project": {
                    "key": self.jira_project_key
                },
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {
                    "name": issue_type
                },
                "priority": {
                    "name": priority
                }
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                
                data = response.json()
                ticket_key = data.get("key")
                ticket_url = f"{self.base_url}/browse/{ticket_key}"
                
                logger.info(f"✅ Jira ticket created: {ticket_key}")
                
                return {
                    "key": ticket_key,
                    "url": ticket_url
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating Jira ticket: {e.response.status_code} {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")
            return None


# Singleton instance
atlassian_client = AtlassianClient()
