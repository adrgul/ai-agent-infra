"""Integration tests for API endpoints."""

import pytest
from httpx import AsyncClient

from src.models.ticket import TicketInput


class TestAPIIntegration:
    """Test suite for API endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_health_endpoint(self, api_client: AsyncClient):
        """Test GET /health endpoint."""

        response = await api_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
        assert "environment" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ready_endpoint(self, api_client: AsyncClient):
        """Test GET /health/ready endpoint."""

        response = await api_client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_live_endpoint(self, api_client: AsyncClient):
        """Test GET /health/live endpoint."""

        response = await api_client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_root_endpoint(self, api_client: AsyncClient):
        """Test GET / endpoint."""

        response = await api_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "supportai"
        assert "version" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_ticket_validation(self, api_client: AsyncClient):
        """Test POST /api/v1/tickets/process with invalid data."""

        # Missing required fields
        invalid_ticket = {
            "ticket_id": "TKT-001"
            # Missing raw_message, customer_name, customer_email
        }

        response = await api_client.post(
            "/api/v1/tickets/process",
            json=invalid_ticket
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_ticket_invalid_email(self, api_client: AsyncClient):
        """Test POST /api/v1/tickets/process with invalid email."""

        ticket = {
            "ticket_id": "TKT-002",
            "raw_message": "I need help with my account",
            "customer_name": "John Doe",
            "customer_email": "not-an-email"  # Invalid email format
        }

        response = await api_client.post(
            "/api/v1/tickets/process",
            json=ticket
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_metrics_endpoint(self, api_client: AsyncClient):
        """Test GET /api/v1/tickets/metrics endpoint."""

        response = await api_client.get("/api/v1/tickets/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "counters" in data
        assert "timers" in data
        assert "gauges" in data
