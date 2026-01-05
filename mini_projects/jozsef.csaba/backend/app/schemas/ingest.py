"""
Pydantic schemas for the /ingest endpoint.

Why this module exists:
- Type-safe request/response contracts for document ingestion
- Validation of ingest parameters
- Clear API documentation via Pydantic models

Design decisions:
- force_rebuild flag allows re-indexing without restarting service
- Response includes detailed stats for debugging and UI feedback
"""

from typing import List

from pydantic import BaseModel, ConfigDict, Field


class IngestRequest(BaseModel):
    """
    Request schema for POST /ingest.

    Why force_rebuild: Allows caller to decide whether to skip indexing
    if vector store already exists. Default False to avoid expensive rebuilds.
    """

    # Assert: force_rebuild must be a boolean
    # (Pydantic enforces type validation)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "force_rebuild": False
            }
        }
    )

    force_rebuild: bool = Field(
        default=False,
        description="If true, rebuild index even if it already exists"
    )


class IngestResponse(BaseModel):
    """
    Response schema for POST /ingest.

    Why these fields:
    - indexed_files: Count of distinct files processed
    - chunk_count: Total chunks created (indicates index size)
    - vectorstore_dir: Confirms persistence location for debugging
    - filenames: Shows exactly which files were indexed (useful for verification)
    """

    # Assert: indexed_files and chunk_count must be non-negative
    # (Business logic validates this before constructing response)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "indexed_files": 3,
                "chunk_count": 42,
                "vectorstore_dir": "../.vectorstore/faiss_index",
                "filenames": ["a.md", "notes/b.md", "notes/c.md"]
            }
        }
    )

    indexed_files: int = Field(
        ...,
        description="Number of markdown files indexed",
        ge=0  # Greater than or equal to 0
    )

    chunk_count: int = Field(
        ...,
        description="Total number of chunks created from documents",
        ge=0
    )

    vectorstore_dir: str = Field(
        ...,
        description="Directory where FAISS index is persisted"
    )

    filenames: List[str] = Field(
        ...,
        description="List of indexed filenames (relative paths from DOCS_PATH)"
    )
