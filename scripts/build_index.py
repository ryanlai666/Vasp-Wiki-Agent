#!/usr/bin/env python3
"""
Script to process scraped wiki pages and build the FAISS vector index.
"""
import sys
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scraper.content_processor import ContentProcessor
from backend.rag.chunker import TextChunker
from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.vector_store import FAISSVectorStore
from backend.utils.logger import logger


def build_index():
    """Build the vector index from processed documents."""
    logger.info("Starting index building process...")
    
    # Step 1: Process raw HTML files
    logger.info("Step 1: Processing raw HTML files...")
    processor = ContentProcessor()
    processed_pages = processor.process_all_pages()
    
    if not processed_pages:
        logger.error("No processed pages found. Please run download_wiki.py first.")
        return 0
    
    logger.info(f"Processed {len(processed_pages)} pages")
    
    # Step 2: Chunk documents
    logger.info("Step 2: Chunking documents...")
    chunker = TextChunker()
    all_chunks = chunker.chunk_all_documents()
    
    if not all_chunks:
        logger.error("No chunks created. Check chunking configuration.")
        return 0
    
    logger.info(f"Created {len(all_chunks)} chunks")
    
    # Step 3: Generate embeddings
    logger.info("Step 3: Generating embeddings...")
    embedding_generator = EmbeddingGenerator()
    
    # Extract texts for embedding
    texts = [chunk['text'] for chunk in all_chunks]
    
    logger.info(f"Generating embeddings for {len(texts)} chunks...")
    embeddings = embedding_generator.embed_batch(texts, batch_size=32)
    
    logger.info(f"Generated embeddings with shape: {embeddings.shape}")
    
    # Step 4: Build vector store
    logger.info("Step 4: Building vector store...")
    vector_store = FAISSVectorStore()
    
    # Prepare metadata for vector store
    documents_metadata = []
    for chunk in all_chunks:
        documents_metadata.append({
            'text': chunk['text'],
            'source_title': chunk['metadata']['source_title'],
            'source_url': chunk['metadata']['source_url'],
            'heading': chunk['metadata'].get('heading', ''),
            'chunk_type': chunk['metadata'].get('chunk_type', 'unknown'),
            'tokens': chunk['metadata'].get('tokens', 0)
        })
    
    # Add to vector store
    vector_store.add_documents(embeddings, documents_metadata)
    
    # Save index
    vector_store.save_index()
    
    # Print statistics
    stats = vector_store.get_stats()
    logger.info("="*60)
    logger.info("Index building complete!")
    logger.info(f"  Documents indexed: {stats['num_documents']}")
    logger.info(f"  Embedding dimension: {stats['dimension']}")
    logger.info(f"  Index type: {stats['index_type']}")
    logger.info("="*60)
    
    return stats['num_documents']


def main():
    """Main function."""
    print("\n" + "="*60)
    print("VASP Wiki Index Builder")
    print("="*60)
    print("\nThis script will:")
    print("1. Process raw HTML files into clean text")
    print("2. Chunk documents for RAG")
    print("3. Generate embeddings")
    print("4. Build FAISS vector index")
    print()
    
    response = input("Continue? (y/N): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    try:
        num_documents = build_index()
        print(f"\n✓ Success! Indexed {num_documents} document chunks")
        print("\nYou can now start the backend server:")
        print("  cd backend")
        print("  uvicorn main:app --reload")
    except Exception as e:
        logger.error(f"Error building index: {e}")
        raise


if __name__ == "__main__":
    main()
