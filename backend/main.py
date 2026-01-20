"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.api.routes import router, set_rag_agent
from backend.rag.rag_agent import RAGAgent
from backend.utils.logger import logger
from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting VASP Wiki RAG Agent backend...")
    
    try:
        # Initialize RAG agent
        agent = RAGAgent()
        set_rag_agent(agent)
        logger.info("RAG agent initialized")
        
        # Check if ready
        if agent.is_ready():
            stats = agent.vector_store.get_stats()
            logger.info(f"Vector store ready with {stats['num_documents']} documents")
        else:
            logger.warning("Vector store is empty. Run build_index.py to index documents.")
        
    except Exception as e:
        logger.error(f"Error initializing RAG agent: {e}")
        logger.warning("RAG agent will not be available until properly configured")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="VASP Wiki RAG Agent",
    description="RAG agent for querying VASP Wiki using Gemini 2.5 Flash API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and React default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "VASP Wiki RAG Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True
    )
