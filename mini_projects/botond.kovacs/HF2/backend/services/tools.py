"""
Service layer - LangGraph agent tools implementation.
Following SOLID: Single Responsibility - each tool wrapper has one clear purpose.
"""
from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
import logging

from domain.interfaces import (
    IRegulationRAGClient
)

logger = logging.getLogger(__name__)


class RegulationTool:
    """
    Regulation Q&A tool using RAG (Retrieval-Augmented Generation) pipeline.
    
    This tool allows users to ask questions about the content of a regulation (PDF).
    It uses vector similarity search to find relevant passages and generates
    answers based on the retrieved context.
    """
    
    def __init__(self, client: IRegulationRAGClient):
        self.client = client
        self.name = "regulation"
        self.description = """Ask questions about the regulation '2008. évi LX. Gáztörvény'.
This tool uses RAG (Retrieval-Augmented Generation) to search through the regulation content and provide answers.
Useful when user asks about:
- Sections in the regulation (e.g. 1. §, 2. §, etc.)
- Legal requirements and obligations
- Definitions and terms
- Specific paragraphs or chapters
- Quotes or passages from the regulation
Actions: 'query' (ask a question), 'info' (get regulation information)"""
    async def execute(
        self,
        action: str = "query",
        question: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Execute regulation-related actions.
        
        Args:
            action: 'query' to ask questions, 'info' to get regulation information
            question: The question to ask about the regulation (required for 'query' action)
            top_k: Number of relevant passages to retrieve (default: 5)
        
        Returns:
            Dict with answer, sources, and metadata
        """
        logger.info(f"Regulation tool called: action={action}, question={question[:50] if question else 'None'}...")
        
        try:
            if action == "query":
                if not question:
                    return {
                        "success": False,
                        "error": "Question is required for query action",
                        "system_message": "Regulation query failed: no question provided"
                    }
                
                result = await self.client.query(question, top_k)
                
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"],
                        "system_message": f"Regulation query failed: {result['error']}"
                    }
                
                # Format the response
                answer = result.get("answer", "No answer found")
                sources = result.get("sources", [])
                regulation_title = result.get("regulation_title", "Unknown")
                
                # Build source references
                source_refs = []
                for i, src in enumerate(sources[:3], 1):
                    page = src.get("page", "?")
                    preview = src.get("content_preview", "")[:100]
                    source_refs.append(f"[Page {page}]: {preview}...")
                
                summary = f"📚 **Answer from '{regulation_title}':**\n\n{answer}"
                if source_refs:
                    summary += f"\n\n**Sources:**\n" + "\n".join(source_refs)
                
                return {
                    "success": True,
                    "message": summary,
                    "data": result,
                    "system_message": f"Found answer from regulation '{regulation_title}' using {len(sources)} source passages"
                }
            
            elif action == "info":
                result = await self.client.get_regulation_info()
                
                if "error" in result:
                    return {
                        "success": False,
                        "error": result["error"],
                        "system_message": f"Failed to get regulation info: {result['error']}"
                    }
                
                title = result.get("title", "Unknown")
                chunks = result.get("chunks_count", 0)
                pages = result.get("pages_count", "N/A")
                status = result.get("status", "unknown")
                
                summary = f"📖 **Regulation Information:**\n"
                summary += f"- **Title:** {title}\n"
                summary += f"- **Pages:** {pages}\n"
                summary += f"- **Indexed chunks:** {chunks}\n"
                summary += f"- **Status:** {status}"
                return {
                    "success": True,
                    "message": summary,
                    "data": result,
                    "system_message": f"Regulation '{title}' is loaded with {chunks} indexed chunks"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "system_message": f"Unknown regulation action: {action}. Use: query, info"
                }
        
        except Exception as e:
            logger.error(f"Regulation tool exception: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "system_message": f"Regulation tool failed: {e}"
            }
