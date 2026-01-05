"""
Debug CLI utilities for RAG system testing and development.

Provides pretty-printed output for search results, citations, and feedback data.
Inspired by vector_embeddings/app/cli.py formatting patterns.
"""

import asyncio
from typing import List, Dict, Optional
from domain.models import Citation


class DebugCLI:
    """
    Command-line utilities for debugging RAG operations.
    
    Provides formatted output for:
    - Search results with scores
    - Citation details
    - Feedback statistics
    - Vector similarity comparisons
    """
    
    @staticmethod
    def format_citations(
        citations: List[Citation],
        show_content: bool = True,
        max_content_length: int = 200
    ) -> str:
        """
        Format citations with pretty printing.
        
        Args:
            citations: List of Citation objects
            show_content: Whether to display content preview
            max_content_length: Maximum content length to display
            
        Returns:
            Formatted string
        """
        if not citations:
            return "📭 No citations found\n"
        
        output = f"\n📚 RETRIEVED {len(citations)} CITATIONS:\n"
        output += "=" * 80 + "\n\n"
        
        for i, citation in enumerate(citations, 1):
            # Header
            output += f"  [{i}] Score: {citation.score:.4f} | ID: {citation.doc_id}\n"
            output += f"      Title: {citation.title}\n"
            
            # URL if available
            if citation.url:
                output += f"      URL: {citation.url}\n"
            
            # Content preview
            if show_content and citation.content:
                content_preview = citation.content[:max_content_length]
                if len(citation.content) > max_content_length:
                    content_preview += "..."
                # Replace newlines for compact display
                content_preview = content_preview.replace('\n', ' ')
                output += f"      Content: \"{content_preview}\"\n"
            
            output += "\n"
        
        return output
    
    @staticmethod
    def format_feedback_stats(
        feedback_map: Dict[str, float],
        citation_ids: Optional[List[str]] = None
    ) -> str:
        """
        Format feedback statistics with visual indicators.
        
        Args:
            feedback_map: Dict mapping citation_id → like_percentage
            citation_ids: Optional list to show in specific order
            
        Returns:
            Formatted string
        """
        if not feedback_map:
            return "📊 No feedback data available\n"
        
        output = f"\n📊 FEEDBACK STATISTICS ({len(feedback_map)} citations):\n"
        output += "=" * 80 + "\n\n"
        
        # Sort by citation_id or use provided order
        if citation_ids:
            items = [(cid, feedback_map.get(cid, 0.0)) for cid in citation_ids if cid in feedback_map]
        else:
            items = sorted(feedback_map.items(), key=lambda x: x[1], reverse=True)
        
        for citation_id, like_pct in items:
            # Visual bar chart
            bar_length = int(like_pct / 5)  # 0-100 → 0-20 chars
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            # Color indicator
            if like_pct >= 70:
                indicator = "🟢"  # High
            elif like_pct >= 40:
                indicator = "🟡"  # Medium
            else:
                indicator = "🔴"  # Low
            
            output += f"  {indicator} {like_pct:5.1f}% [{bar}] {citation_id}\n"
        
        output += "\n"
        return output
    
    @staticmethod
    def format_search_comparison(
        original_results: List[Citation],
        reranked_results: List[Citation]
    ) -> str:
        """
        Compare original vs feedback-reranked results side-by-side.
        
        Args:
            original_results: Citations before feedback boost
            reranked_results: Citations after feedback boost
            
        Returns:
            Formatted comparison
        """
        output = "\n🔀 RANKING COMPARISON:\n"
        output += "=" * 80 + "\n\n"
        
        max_len = max(len(original_results), len(reranked_results))
        
        output += f"{'ORIGINAL (Semantic Only)':<40} | {'RERANKED (+ Feedback Boost)':<40}\n"
        output += "-" * 80 + "\n"
        
        for i in range(max_len):
            # Original
            if i < len(original_results):
                orig = original_results[i]
                orig_str = f"[{i+1}] {orig.score:.3f} - {orig.doc_id[:30]}"
            else:
                orig_str = ""
            
            # Reranked
            if i < len(reranked_results):
                rerank = reranked_results[i]
                rerank_str = f"[{i+1}] {rerank.score:.3f} - {rerank.doc_id[:30]}"
                
                # Check if order changed
                if i < len(original_results) and orig.doc_id != rerank.doc_id:
                    rerank_str += " ⬆️"
            else:
                rerank_str = ""
            
            output += f"{orig_str:<40} | {rerank_str:<40}\n"
        
        output += "\n"
        return output
    
    @staticmethod
    async def test_rag_search(
        query: str,
        domain: str = "marketing",
        top_k: int = 5,
        show_feedback: bool = True
    ) -> None:
        """
        Interactive RAG search test with formatted output.
        
        Args:
            query: Search query
            domain: Domain filter
            top_k: Number of results
            show_feedback: Whether to display feedback stats
        """
        import os
        from infrastructure.qdrant_rag_client import QdrantRAGClient
        from infrastructure.postgres_client import postgres_client
        
        # Create RAG client instance
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        rag_client = QdrantRAGClient(qdrant_url=qdrant_url)
        
        print("\n🔍 TESTING RAG SEARCH")
        print(f"Query: \"{query}\"")
        print(f"Domain: {domain}")
        print(f"Top-K: {top_k}\n")
        
        # Perform search
        try:
            citations = await rag_client.retrieve(
                query=query,
                domain=domain,
                top_k=top_k,
                apply_feedback_boost=show_feedback
            )
            
            # Display results
            print(DebugCLI.format_citations(citations))
            
            # Display feedback if available
            if show_feedback:
                citation_ids = [c.doc_id for c in citations]
                feedback_map = await postgres_client.get_citation_feedback_batch(
                    citation_ids, domain
                )
                if feedback_map:
                    print(DebugCLI.format_feedback_stats(feedback_map, citation_ids))
        
        except Exception as e:
            print(f"❌ Error during search: {e}\n")
    
    @staticmethod
    def print_startup_banner() -> None:
        """Print application startup banner."""
        banner = """
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║              🤖  KNOWLEDGE ROUTER - DEBUG CLI                        ║
║                                                                       ║
║  Feedback-Weighted RAG System with Multi-Domain Knowledge Base       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
        """
        print(banner)


# Convenience function for quick testing
async def quick_search(query: str, domain: str = "marketing", top_k: int = 5):
    """
    Quick search helper for REPL/debugging.
    
    Usage:
        >>> from utils.debug_cli import quick_search
        >>> import asyncio
        >>> asyncio.run(quick_search("brand guidelines"))
    """
    await DebugCLI.test_rag_search(query, domain, top_k)


# Example CLI script
if __name__ == "__main__":
    import sys
    
    DebugCLI.print_startup_banner()
    
    if len(sys.argv) < 2:
        print("Usage: python -m utils.debug_cli <query> [domain] [top_k]")
        print("\nExample:")
        print("  python -m utils.debug_cli 'brand colors' marketing 5")
        sys.exit(1)
    
    query = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else "marketing"
    top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    asyncio.run(quick_search(query, domain, top_k))
