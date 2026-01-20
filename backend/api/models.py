"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Optional


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., description="User query about VASP")
    top_k: Optional[int] = Field(None, description="Number of context chunks to retrieve", ge=1, le=20)


class Source(BaseModel):
    """Source citation model."""
    title: str
    url: str
    heading: Optional[str] = None
    snippet: str
    similarity: float = Field(..., ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str
    sources: List[Source]
    num_sources: int
    retrieval_time: Optional[float] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str
    vector_store_stats: Optional[dict] = None


class RebuildIndexResponse(BaseModel):
    """Response model for rebuild index endpoint."""
    status: str
    message: str
    num_documents: Optional[int] = None
