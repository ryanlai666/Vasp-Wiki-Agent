#!/usr/bin/env python3
"""
Script to test the RAG agent with sample queries.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.rag.rag_agent import RAGAgent
from backend.utils.logger import logger


def main():
    """Test the RAG agent."""
    logger.info("Initializing RAG agent...")
    
    try:
        agent = RAGAgent()
    except Exception as e:
        logger.error(f"Could not initialize RAG agent: {e}")
        logger.error("Make sure GEMINI_API_KEY is set in .env file")
        return
    
    # Check if ready
    if not agent.is_ready():
        logger.error("RAG agent is not ready. Please run build_index.py first.")
        return
    
    stats = agent.vector_store.get_stats()
    logger.info(f"Vector store ready with {stats['num_documents']} documents")
    
    # Sample queries
    test_queries = [
        "What is VASP?",
        "How do I set up a VASP calculation?",
        "What are PAW potentials?",
        "How do I calculate band structure in VASP?",
        "What is the difference between LDA and GGA functionals?",
    ]
    
    print("\n" + "="*60)
    print("RAG Agent Test")
    print("="*60)
    print("\nChoose an option:")
    print("1. Run sample queries")
    print("2. Enter custom query")
    
    choice = input("\nEnter choice (1-2, default=1): ").strip() or "1"
    
    if choice == "1":
        print("\nRunning sample queries...\n")
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*60}")
            print(f"Query {i}: {query}")
            print("="*60)
            
            try:
                response = agent.query(query)
                
                print(f"\nAnswer:")
                print("-" * 60)
                print(response['answer'])
                print("-" * 60)
                
                print(f"\nSources ({response['num_sources']}):")
                for j, source in enumerate(response['sources'], 1):
                    print(f"\n  {j}. {source['title']}")
                    if source['heading']:
                        print(f"     Section: {source['heading']}")
                    print(f"     URL: {source['url']}")
                    print(f"     Similarity: {source['similarity']:.2%}")
                    print(f"     Snippet: {source['snippet'][:150]}...")
                
                if response.get('retrieval_time'):
                    print(f"\nTime: {response['retrieval_time']:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"Error: {e}")
    
    elif choice == "2":
        while True:
            query = input("\nEnter your query (or 'quit' to exit): ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print(f"\nProcessing query: {query}")
            print("-" * 60)
            
            try:
                response = agent.query(query)
                
                print(f"\nAnswer:")
                print("-" * 60)
                print(response['answer'])
                print("-" * 60)
                
                print(f"\nSources ({response['num_sources']}):")
                for j, source in enumerate(response['sources'], 1):
                    print(f"\n  {j}. {source['title']}")
                    if source['heading']:
                        print(f"     Section: {source['heading']}")
                    print(f"     URL: {source['url']}")
                    print(f"     Similarity: {source['similarity']:.2%}")
                
                if response.get('retrieval_time'):
                    print(f"\nTime: {response['retrieval_time']:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                print(f"Error: {e}")
    
    print("\n✓ Testing complete!")


if __name__ == "__main__":
    main()
