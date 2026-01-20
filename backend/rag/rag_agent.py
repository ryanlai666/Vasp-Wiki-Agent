"""RAG Agent using Gemini 2.5 Flash API."""
import google.generativeai as genai
from typing import List, Dict, Optional
import time

from backend.config import settings
from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.vector_store import FAISSVectorStore
from backend.utils.logger import logger


class RAGAgent:
    """RAG Agent that combines retrieval with Gemini generation."""
    
    def __init__(self):
        """Initialize the RAG agent."""
        # Initialize Gemini client for LLM inference
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required for LLM inference. "
                "Please set it in your .env file. "
                "Note: Embeddings use free sentence-transformers by default."
            )
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.llm_model)
            logger.info(f"Initialized Gemini LLM model for inference: {settings.llm_model}")
        except Exception as e:
            logger.error(f"Could not initialize Gemini LLM model: {e}")
            raise
        
        # Initialize embedding generator (uses free sentence-transformers by default)
        self.embedding_generator = EmbeddingGenerator()
        
        # Initialize vector store
        self.vector_store = FAISSVectorStore()
        
        # System prompt
        self.system_prompt = """You are a helpful assistant answering questions about VASP (Vienna Ab initio Simulation Package) based on the provided documentation from the VASP Wiki.

Instructions:
- Use the provided context from the VASP Manual to answer questions accurately
- Cite specific sections or pages when possible
- If the context doesn't contain enough information, say so clearly
- Be concise but thorough
- Use technical terminology correctly
- Format your response in a clear, readable way

When citing sources, mention the page title or section name."""
    
    def retrieve_context(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            
        Returns:
            List of relevant document chunks with metadata
        """
        top_k = top_k or settings.top_k
        
        # Generate query embedding
        query_embedding = self.embedding_generator.embed_text(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        # Format results
        context_chunks = []
        for metadata, similarity in results:
            context_chunks.append({
                'text': metadata.get('text', ''),
                'source_title': metadata.get('source_title', 'Unknown'),
                'source_url': metadata.get('source_url', ''),
                'heading': metadata.get('heading', ''),
                'similarity': similarity
            })
        
        logger.info(f"Retrieved {len(context_chunks)} context chunks for query")
        return context_chunks
    
    def format_context(self, context_chunks: List[Dict]) -> str:
        """
        Format context chunks into a prompt-friendly string.
        
        Args:
            context_chunks: List of context chunks
            
        Returns:
            Formatted context string
        """
        formatted_parts = []
        
        for i, chunk in enumerate(context_chunks, 1):
            source = chunk.get('source_title', 'Unknown')
            heading = chunk.get('heading', '')
            text = chunk.get('text', '')
            url = chunk.get('source_url', '')
            
            part = f"[Context {i}]\n"
            part += f"Source: {source}"
            if heading:
                part += f" - {heading}"
            part += f"\nURL: {url}\n"
            part += f"Content:\n{text}\n"
            
            formatted_parts.append(part)
        
        return "\n---\n\n".join(formatted_parts)
    
    def generate_response(self, query: str, context_chunks: List[Dict]) -> Dict:
        """
        Generate a response using Gemini API.
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks
            
        Returns:
            Dictionary with answer and metadata
        """
        # Format context
        context_text = self.format_context(context_chunks)
        
        # Construct prompt
        prompt = f"{self.system_prompt}\n\n"
        prompt += f"Context from VASP Manual:\n\n{context_text}\n\n"
        prompt += f"User Question: {query}\n\n"
        prompt += "Please provide a comprehensive answer based on the context above. Cite your sources when possible."
        
        try:
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=2048,
                )
            )
            
            answer = response.text
            
            # Extract sources
            sources = []
            for chunk in context_chunks:
                sources.append({
                    'title': chunk.get('source_title', 'Unknown'),
                    'url': chunk.get('source_url', ''),
                    'heading': chunk.get('heading', ''),
                    'snippet': chunk.get('text', '')[:200] + '...' if len(chunk.get('text', '')) > 200 else chunk.get('text', ''),
                    'similarity': chunk.get('similarity', 0.0)
                })
            
            return {
                'answer': answer,
                'sources': sources,
                'num_sources': len(sources)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def query(self, query: str, top_k: int = None) -> Dict:
        """
        Process a query end-to-end: retrieve context and generate response.
        
        Args:
            query: User query
            top_k: Number of context chunks to retrieve
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Processing query: {query[:100]}...")
        
        start_time = time.time()
        
        # Retrieve context
        context_chunks = self.retrieve_context(query, top_k=top_k)
        
        if not context_chunks:
            return {
                'answer': "I couldn't find any relevant information in the VASP Manual for your query. Please try rephrasing your question or check if the topic is covered in the documentation.",
                'sources': [],
                'num_sources': 0,
                'retrieval_time': time.time() - start_time
            }
        
        # Generate response
        response = self.generate_response(query, context_chunks)
        response['retrieval_time'] = time.time() - start_time
        
        logger.info(f"Generated response in {response['retrieval_time']:.2f} seconds")
        
        return response
    
    def is_ready(self) -> bool:
        """
        Check if the RAG agent is ready (has indexed documents).
        
        Returns:
            True if ready, False otherwise
        """
        stats = self.vector_store.get_stats()
        return stats['num_documents'] > 0
