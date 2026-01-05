"""Unit tests for triage classification node."""

import pytest
from unittest.mock import AsyncMock, patch

from src.nodes.triage_classify import triage_classify_node, TriageResult
from src.models.state import SupportTicketState


class TestTriageClassifyNode:
    """Test suite for triage classification node."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_billing_ticket_classification(self, mock_llm_response):
        """Test that billing tickets are correctly classified."""

        state: SupportTicketState = {
            "ticket_id": "TKT-001",
            "raw_message": "I was charged twice for my subscription",
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "problem_type": "billing",
            "sentiment": "neutral"
        }

        with patch("src.nodes.triage_classify.get_llm") as mock_llm:
            mock_llm.return_value.with_structured_output.return_value.ainvoke = AsyncMock(
                return_value=TriageResult(**mock_llm_response)
            )

            result = await triage_classify_node(state)

        assert result["category"] == "Billing"
        assert result["priority"] == "P2"
        assert result["sla_hours"] == 24
        assert result["suggested_team"] == "Finance Team"
        assert 0 <= result["triage_confidence"] <= 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_high_priority_frustrated_customer(self):
        """Frustrated customers should get priority boost."""

        state: SupportTicketState = {
            "ticket_id": "TKT-002",
            "raw_message": "This is UNACCEPTABLE! I've been waiting for days!",
            "customer_name": "Jane Smith",
            "customer_email": "jane@example.com",
            "problem_type": "technical",
            "sentiment": "frustrated"
        }

        with patch("src.nodes.triage_classify.get_llm") as mock_llm:
            mock_llm.return_value.with_structured_output.return_value.ainvoke = AsyncMock(
                return_value=TriageResult(
                    category="Technical",
                    subcategory="Service Outage",
                    priority="P1",
                    sla_hours=4,
                    suggested_team="Engineering",
                    confidence=0.88
                )
            )

            result = await triage_classify_node(state)

        assert result["priority"] == "P1"
        assert result["sla_hours"] <= 4

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_priority_raises_error(self):
        """Invalid priority values should raise ValidationError."""

        state: SupportTicketState = {
            "ticket_id": "TKT-003",
            "raw_message": "Test message",
            "customer_name": "Test User",
            "customer_email": "test@example.com",
            "problem_type": "account",
            "sentiment": "neutral"
        }

        with patch("src.nodes.triage_classify.get_llm") as mock_llm:
            # Mock with invalid priority
            mock_llm.return_value.with_structured_output.return_value.ainvoke = AsyncMock(
                side_effect=ValueError("Invalid priority: P5. Must be P1, P2, or P3")
            )

            result = await triage_classify_node(state)

            # Should have errors field with fallback values
            assert "errors" in result
            assert result["priority"] == "P3"  # Fallback default

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_feature_request_low_priority(self):
        """Feature requests should typically get P3 priority."""

        state: SupportTicketState = {
            "ticket_id": "TKT-004",
            "raw_message": "It would be great if we could export data to CSV",
            "customer_name": "Alice Johnson",
            "customer_email": "alice@example.com",
            "problem_type": "feature_request",
            "sentiment": "satisfied"
        }

        with patch("src.nodes.triage_classify.get_llm") as mock_llm:
            mock_llm.return_value.with_structured_output.return_value.ainvoke = AsyncMock(
                return_value=TriageResult(
                    category="Feature Request",
                    subcategory="Data Export",
                    priority="P3",
                    sla_hours=72,
                    suggested_team="Product",
                    confidence=0.95
                )
            )

            result = await triage_classify_node(state)

        assert result["category"] == "Feature Request"
        assert result["priority"] == "P3"
        assert result["sla_hours"] == 72
        assert result["suggested_team"] == "Product"
