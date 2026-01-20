"""FAISS vector store for RAG."""
import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pickle

from backend.config import settings
from backend.utils.logger import logger


class FAISSVectorStore:
    """FAISS-based vector store for document embeddings."""
    
    def __init__(self, index_path: str = None):
        """
        Initialize the vector store.
        
        Args:
            index_path: Path to store/load the FAISS index
        """
        self.index_path = Path(index_path or settings.faiss_index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict] = []
        self.metadata_file = self.index_path / "metadata.json"
        self.index_file = self.index_path / "index.faiss"
        self.dimension: Optional[int] = None
        
        self._load_index()
    
    def _load_index(self):
        """Load existing index and metadata if available."""
        if self.index_file.exists() and self.metadata_file.exists():
            try:
                # Load FAISS index
                self.index = faiss.read_index(str(self.index_file))
                
                # Load metadata
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                
                self.dimension = self.index.d
                logger.info(f"Loaded existing index with {len(self.metadata)} documents")
            except Exception as e:
                logger.warning(f"Could not load existing index: {e}")
                logger.info("Starting with empty index")
    
    def _create_index(self, dimension: int):
        """
        Create a new FAISS index.
        
        Args:
            dimension: Dimension of embeddings
        """
        # Use IndexFlatL2 for exact search (good for <100K vectors)
        # For larger datasets, consider IndexIVFFlat
        self.index = faiss.IndexFlatL2(dimension)
        self.dimension = dimension
        logger.info(f"Created new FAISS index with dimension {dimension}")
    
    def add_documents(self, embeddings: np.ndarray, documents: List[Dict]):
        """
        Add documents to the vector store.
        
        Args:
            embeddings: Numpy array of embeddings (n_docs, embedding_dim)
            documents: List of document metadata dictionaries
        """
        if len(embeddings) != len(documents):
            raise ValueError("Number of embeddings must match number of documents")
        
        if embeddings.shape[0] == 0:
            logger.warning("No embeddings to add")
            return
        
        dimension = embeddings.shape[1]
        
        # Normalize embeddings for cosine similarity (L2 normalization)
        faiss.normalize_L2(embeddings)
        
        # Create index if it doesn't exist
        if self.index is None:
            self._create_index(dimension)
        elif self.dimension != dimension:
            raise ValueError(f"Embedding dimension mismatch: {self.dimension} != {dimension}")
        
        # Add to index
        self.index.add(embeddings.astype('float32'))
        
        # Add metadata
        self.metadata.extend(documents)
        
        logger.info(f"Added {len(documents)} documents to vector store (total: {len(self.metadata)})")
    
    def search(self, query_embedding: np.ndarray, top_k: int = None) -> List[Tuple[Dict, float]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of tuples (document_metadata, similarity_score)
        """
        if self.index is None or len(self.metadata) == 0:
            logger.warning("Index is empty")
            return []
        
        top_k = top_k or settings.top_k
        
        # Ensure query is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize query embedding
        faiss.normalize_L2(query_embedding)
        
        # Search
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Convert distances to similarities (1 - normalized distance for L2)
        # For normalized vectors, L2 distance relates to cosine distance
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.metadata):
                # Convert L2 distance to similarity (higher is better)
                # For normalized vectors: similarity = 1 - (distance / 2)
                similarity = 1 - (dist / 2.0)
                results.append((self.metadata[int(idx)], float(similarity)))
        
        return results
    
    def save_index(self):
        """Save the index and metadata to disk."""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_file))
            
            # Save metadata
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved index with {len(self.metadata)} documents to {self.index_path}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'num_documents': len(self.metadata),
            'dimension': self.dimension,
            'index_type': type(self.index).__name__ if self.index else None
        }
    
    def clear(self):
        """Clear the index and metadata."""
        self.index = None
        self.metadata = []
        self.dimension = None
        
        # Remove files
        if self.index_file.exists():
            self.index_file.unlink()
        if self.metadata_file.exists():
            self.metadata_file.unlink()
        
        logger.info("Cleared vector store")
