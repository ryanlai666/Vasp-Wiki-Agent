"""API routes for the VASP Wiki RAG Agent."""
from fastapi import APIRouter, HTTPException
from typing import Optional

from backend.api.models import QueryRequest, QueryResponse, HealthResponse, RebuildIndexResponse
from backend.rag.rag_agent import RAGAgent
from backend.utils.logger import logger

# Global RAG agent instance (initialized in main.py)
rag_agent: Optional[RAGAgent] = None


def set_rag_agent(agent: RAGAgent):
    """Set the global RAG agent instance."""
    global rag_agent
    rag_agent = agent


router = APIRouter(prefix="/api", tags=["api"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        if rag_agent is None:
            return HealthResponse(
                status="error",
                message="RAG agent not initialized"
            )
        
        is_ready = rag_agent.is_ready()
        stats = rag_agent.vector_store.get_stats() if is_ready else None
        
        return HealthResponse(
            status="healthy" if is_ready else "not_ready",
            message="RAG agent is ready" if is_ready else "RAG agent is not ready (no documents indexed)",
            vector_store_stats=stats
        )
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query the RAG agent with a question about VASP.
    
    Args:
        request: Query request with user question
        
    Returns:
        Query response with answer and sources
    """
    if rag_agent is None:
        raise HTTPException(status_code=503, detail="RAG agent not initialized")
    
    if not rag_agent.is_ready():
        raise HTTPException(
            status_code=503,
            detail="RAG agent is not ready. Please rebuild the index first."
        )
    
    try:
        response = rag_agent.query(request.query, top_k=request.top_k)
        return QueryResponse(**response)
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.post("/rebuild-index", response_model=RebuildIndexResponse)
async def rebuild_index():
    """
    Rebuild the vector index from processed documents.
    This is an admin endpoint that should be called after downloading/processing the wiki.
    """
    try:
        from scripts.build_index import build_index
        
        num_documents = build_index()
        
        return RebuildIndexResponse(
            status="success",
            message=f"Index rebuilt successfully with {num_documents} documents",
            num_documents=num_documents
        )
    except Exception as e:
        logger.error(f"Rebuild index error: {e}")
        raise HTTPException(status_code=500, detail=f"Error rebuilding index: {str(e)}")
