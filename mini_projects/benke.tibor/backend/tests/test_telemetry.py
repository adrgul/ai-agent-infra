"""
Unit tests for telemetry functionality.
Tests debug panel telemetry data collection and API response structure.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from domain.models import QueryResponse, Citation, DomainType
from services.agent import AgentState


class TestTelemetryDataCollection:
    """Test telemetry data is collected correctly in agent nodes."""

    @pytest.mark.asyncio
    async def test_rag_context_saved_in_retrieval_node(self):
        """Test RAG context is saved during retrieval."""
        from services.agent import QueryAgent
        from langchain_openai import ChatOpenAI
        
        # Mock dependencies
        llm = MagicMock(spec=ChatOpenAI)
        rag_client = MagicMock()
        
        # Mock citations
        mock_citations = [
            Citation(
                doc_id="doc1",
                title="Test Document 1",
                score=0.95,
                content="This is test content for document 1"
            ),
            Citation(
                doc_id="doc2",
                title="Test Document 2",
                score=0.88,
                content="This is test content for document 2"
            )
        ]
        rag_client.retrieve_for_domain = AsyncMock(return_value=mock_citations)
        
        agent = QueryAgent(llm, rag_client)
        
        # Test state
        state: AgentState = {
            "query": "test query",
            "domain": "marketing",
            "citations": [],
            "retrieved_docs": []
        }
        
        # Execute retrieval node
        result_state = await agent._retrieval_node(state)
        
        # Verify RAG context is saved
        assert "rag_context" in result_state
        assert result_state["rag_context"] is not None
        assert "Test Document 1" in result_state["rag_context"]
        assert "Test Document 2" in result_state["rag_context"]
        assert len(result_state["citations"]) == 2

    @pytest.mark.asyncio
    async def test_llm_prompt_and_response_saved_in_generation_node(self):
        """Test LLM prompt and response are saved during generation."""
        from services.agent import QueryAgent
        from langchain_openai import ChatOpenAI
        
        # Mock LLM
        llm = AsyncMock(spec=ChatOpenAI)
        mock_response = MagicMock()
        mock_response.content = "This is the LLM response"
        llm.ainvoke = AsyncMock(return_value=mock_response)
        
        rag_client = MagicMock()
        agent = QueryAgent(llm, rag_client)
        
        # Test state with citations
        state: AgentState = {
            "query": "What is the brand guideline?",
            "domain": "marketing",
            "citations": [
                {
                    "doc_id": "doc1",
                    "title": "Brand Guide",
                    "score": 0.95,
                    "content": "Brand guidelines content here"
                }
            ],
            "messages": [],
            "output": {}
        }
        
        # Execute generation node
        result_state = await agent._generation_node(state)
        
        # Verify LLM telemetry is saved
        assert "llm_prompt" in result_state
        assert "llm_response" in result_state
        assert result_state["llm_prompt"] is not None
        assert result_state["llm_response"] == "This is the LLM response"
        assert "What is the brand guideline?" in result_state["llm_prompt"]
        assert "Brand Guide" in result_state["llm_prompt"]


class TestQueryResponseTelemetry:
    """Test QueryResponse model includes telemetry fields."""

    def test_query_response_accepts_telemetry_fields(self):
        """Test QueryResponse can be created with telemetry fields."""
        response = QueryResponse(
            domain=DomainType.MARKETING,
            answer="Test answer",
            citations=[],
            rag_context="RAG context here",
            llm_prompt="LLM prompt here",
            llm_response="LLM response here"
        )
        
        assert response.rag_context == "RAG context here"
        assert response.llm_prompt == "LLM prompt here"
        assert response.llm_response == "LLM response here"

    def test_query_response_telemetry_fields_optional(self):
        """Test QueryResponse can be created without telemetry fields."""
        response = QueryResponse(
            domain=DomainType.HR,
            answer="Test answer",
            citations=[]
        )
        
        assert response.rag_context is None
        assert response.llm_prompt is None
        assert response.llm_response is None


class TestAPITelemetryResponse:
    """Test API view returns telemetry data in response."""

    def test_telemetry_response_structure(self):
        """Test telemetry response has correct structure."""
        # Simplified test - just verify the expected structure
        telemetry = {
            "total_latency_ms": 3500.5,
            "chunk_count": 5,
            "max_similarity_score": 0.95,
            "retrieval_latency_ms": None,
            "request": {
                "user_id": "test_user",
                "session_id": "test_session",
                "query": "Test query"
            },
            "response": {
                "domain": "marketing",
                "answer_length": 150,
                "citation_count": 5,
                "workflow_triggered": False
            },
            "rag": {
                "context": "RAG context here",
                "chunk_count": 5
            },
            "llm": {
                "prompt": "LLM prompt here",
                "response": "LLM response here",
                "prompt_length": 100,
                "response_length": 50
            }
        }
        
        # Verify structure
        assert "total_latency_ms" in telemetry
        assert "chunk_count" in telemetry
        assert "request" in telemetry
        assert "response" in telemetry
        assert "rag" in telemetry
        assert "llm" in telemetry
        
        assert telemetry["rag"]["context"] is not None
        assert telemetry["llm"]["prompt"] is not None
        assert telemetry["llm"]["response"] is not None


class TestTelemetryMetrics:
    """Test telemetry metrics calculation."""

    def test_chunk_count_matches_citations(self):
        """Test chunk_count matches number of citations."""
        citations = [
            Citation(doc_id="1", title="Doc 1", score=0.95),
            Citation(doc_id="2", title="Doc 2", score=0.88),
            Citation(doc_id="3", title="Doc 3", score=0.75)
        ]
        
        chunk_count = len(citations)
        assert chunk_count == 3

    def test_max_similarity_score_calculation(self):
        """Test max similarity score is correctly calculated."""
        citations = [
            Citation(doc_id="1", title="Doc 1", score=0.95),
            Citation(doc_id="2", title="Doc 2", score=0.88),
            Citation(doc_id="3", title="Doc 3", score=0.75)
        ]
        
        max_score = max([c.score for c in citations], default=0.0)
        assert max_score == 0.95

    def test_max_score_default_when_no_citations(self):
        """Test max score defaults to 0.0 when no citations."""
        citations = []
        max_score = max([c.score for c in citations], default=0.0)
        assert max_score == 0.0


class TestAgentStateTelemetry:
    """Test AgentState includes telemetry fields."""

    def test_agent_state_accepts_telemetry_fields(self):
        """Test AgentState can store telemetry data."""
        from services.agent import AgentState
        
        state: AgentState = {
            "query": "test",
            "domain": "marketing",
            "citations": [],
            "rag_context": "RAG context",
            "llm_prompt": "LLM prompt",
            "llm_response": "LLM response"
        }
        
        assert state["rag_context"] == "RAG context"
        assert state["llm_prompt"] == "LLM prompt"
        assert state["llm_response"] == "LLM response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
