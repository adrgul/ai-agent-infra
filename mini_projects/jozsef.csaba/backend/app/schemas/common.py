"""
Common Pydantic schemas shared across API endpoints.

Why this module exists:
- Shared response models avoid duplication
- Common base classes ensure consistency
- Type-safe API contracts

Design decisions:
- Use Pydantic v2 for validation and serialization
- ConfigDict for JSON schema customization
"""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """
    Health check response schema.

    Why simple: Health checks should be fast and lightweight;
    just confirm the service is responding.
    """

    # Assert: status must be "ok" for successful health check
    # (Validation enforced by Pydantic when constructing response)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok"
            }
        }
    )

    status: str
