"""
Tests for the /health endpoint.

Why this module exists:
- Validates health check endpoint returns correct status
- Ensures service monitoring endpoints work correctly
- Regression test for deployment health checks

Design decisions:
- Use TestClient for synchronous HTTP testing
- No external dependencies (fast, reliable test)
"""

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """
    Test that GET /health returns {"status": "ok"}.

    Why this test: Health checks are critical for load balancers and monitoring.
    This test ensures the endpoint works correctly and returns expected format.

    Why 200 status: Standard HTTP success code for health checks.

    Args:
        client: FastAPI TestClient fixture
    """
    # Assert: Response must have status 200 and correct body
    response = client.get("/health")

    assert response.status_code == 200, (
        f"Health endpoint must return 200 OK, got {response.status_code}"
    )

    # Verify response body structure
    data = response.json()
    assert "status" in data, "Response must contain 'status' field"
    assert data["status"] == "ok", "Health status must be 'ok'"
