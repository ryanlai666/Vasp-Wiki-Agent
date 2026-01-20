"""Embedding generation for RAG."""
import google.generativeai as genai
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import settings
from backend.utils.logger import logger


class EmbeddingGenerator:
    """Generates embeddings for text chunks."""
    
    def __init__(self, model_name: str = None, use_gemini: bool = None):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: Name of the embedding model
            use_gemini: Whether to use Gemini embeddings (if available). 
                       If None, uses settings.use_gemini_embeddings
        """
        self.model_name = model_name or settings.embedding_model
        # Ensure Gemini model name has proper prefix
        if self.model_name and not self.model_name.startswith('models/') and not self.model_name.startswith('tunedModels/'):
            self.model_name = f"models/{self.model_name}"
        
        # Use config setting if not explicitly provided
        if use_gemini is None:
            use_gemini = getattr(settings, 'use_gemini_embeddings', True)
        self.use_gemini = use_gemini
        self.gemini_client = None
        self.fallback_model = None
        self.gemini_quota_exceeded = False  # Track if we've hit quota limits
        
        # Always initialize fallback model as backup
        try:
            self.fallback_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Initialized sentence-transformers fallback model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Could not initialize fallback embedding model: {e}")
            raise
        
        if use_gemini:
            # Check if API key is available
            if not settings.gemini_api_key:
                logger.info("No Gemini API key found. Using sentence-transformers (free, no API key required)")
                self.use_gemini = False
            else:
                try:
                    genai.configure(api_key=settings.gemini_api_key)
                    # Try to use Gemini embeddings
                    try:
                        # Check if embedding model is available
                        self.gemini_client = genai
                        logger.info(f"Initialized Gemini embedding model: {self.model_name}")
                    except Exception as e:
                        logger.warning(f"Could not initialize Gemini embeddings: {e}")
                        logger.info("Falling back to sentence-transformers")
                        self.use_gemini = False
                except Exception as e:
                    logger.warning(f"Could not configure Gemini API: {e}")
                    logger.info("Falling back to sentence-transformers")
                    self.use_gemini = False
        else:
            logger.info("Gemini embeddings disabled. Using sentence-transformers (free, no API key required)")
    
    def _get_gemini_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding from Gemini API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        # If we've already hit quota limits, don't try again
        if self.gemini_quota_exceeded:
            return None
            
        try:
            # Try to use Gemini embedding API
            # Note: The API might vary, this is a common pattern
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            # Handle different response formats
            if hasattr(result, 'embedding'):
                return np.array(result.embedding)
            elif isinstance(result, dict) and 'embedding' in result:
                return np.array(result['embedding'])
            else:
                logger.warning("Unexpected embedding response format")
                return None
        except AttributeError:
            # If embed_content doesn't exist, try alternative method
            try:
                # Alternative: use the model directly if available
                model = genai.GenerativeModel(self.model_name)
                # This might not work for embedding models, fallback
                return None
            except Exception:
                return None
        except Exception as e:
            error_str = str(e)
            # Check for quota/rate limit errors (429 status code or quota messages)
            if '429' in error_str or 'quota' in error_str.lower() or 'rate limit' in error_str.lower():
                self.gemini_quota_exceeded = True
                self.use_gemini = False
                logger.warning("Gemini API quota exceeded. Switching to sentence-transformers for all remaining embeddings.")
                logger.info("Tip: For free tier users, consider setting USE_GEMINI=false in your .env file")
            else:
                logger.error(f"Error getting Gemini embedding: {e}")
            return None
    
    def _get_fallback_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding from sentence-transformers.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self.fallback_model is None:
            raise RuntimeError("Fallback model not initialized")
        embedding = self.fallback_model.encode(text, convert_to_numpy=True)
        return embedding
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        if self.use_gemini and self.gemini_client:
            embedding = self._get_gemini_embedding(text)
            if embedding is not None:
                return embedding
        
        # Fallback to sentence-transformers
        return self._get_fallback_embedding(text)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        embeddings = []
        
        if self.use_gemini and self.gemini_client and not self.gemini_quota_exceeded:
            # Process with Gemini (might need to be one at a time)
            # But if we hit quota limits, switch to batch processing with fallback
            consecutive_failures = 0
            max_failures = 3  # Switch to fallback after 3 consecutive failures
            
            for i, text in enumerate(texts):
                embedding = self._get_gemini_embedding(text)
                if embedding is not None:
                    embeddings.append(embedding)
                    consecutive_failures = 0  # Reset counter on success
                else:
                    # Fallback for this text
                    embeddings.append(self._get_fallback_embedding(text))
                    consecutive_failures += 1
                    
                    # If we hit quota or too many failures, switch to batch processing
                    if self.gemini_quota_exceeded or consecutive_failures >= max_failures:
                        logger.info(f"Switching to sentence-transformers batch processing after {i + 1} texts")
                        # Process remaining texts with batch processing
                        remaining_texts = texts[i + 1:]
                        if remaining_texts:
                            remaining_embeddings = self.fallback_model.encode(
                                remaining_texts,
                                batch_size=batch_size,
                                convert_to_numpy=True,
                                show_progress_bar=True
                            )
                            embeddings.extend(remaining_embeddings)
                        break
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Embedded {i + 1}/{len(texts)} texts")
        else:
            # Use sentence-transformers batch processing
            embeddings = self.fallback_model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            return embeddings
        
        return np.array(embeddings)
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings.
        
        Returns:
            Embedding dimension
        """
        # Test with a small text
        test_embedding = self.embed_text("test")
        return len(test_embedding)
