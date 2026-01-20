"""Text chunking strategies for RAG."""
import re
from typing import List, Dict, Optional
from pathlib import Path
import json
import tiktoken

from backend.config import settings
from backend.utils.logger import logger


class TextChunker:
    """Chunks text documents for RAG with semantic awareness."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None, min_chunk_size: int = None):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            min_chunk_size: Minimum chunk size in tokens
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.min_chunk_size = min_chunk_size or settings.min_chunk_size
        
        # Initialize tokenizer (using cl100k_base which is used by GPT models)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            logger.warning("Could not load tiktoken, using character-based chunking")
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Fallback: approximate 1 token = 4 characters
            return len(text) // 4
    
    def split_by_sections(self, document: Dict) -> List[Dict]:
        """
        Split document by sections (semantic chunking).
        
        Args:
            document: Document with sections
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        sections = document.get('sections', [])
        
        if not sections:
            # Fallback to plain text if no sections
            return self.split_by_size(document)
        
        current_chunk = []
        current_tokens = 0
        current_heading = None
        
        for section in sections:
            heading = section.get('heading', '')
            content = section.get('content', '')
            section_tokens = self.count_tokens(content)
            
            # If section fits in current chunk, add it
            if current_tokens + section_tokens <= self.chunk_size:
                if not current_heading:
                    current_heading = heading
                current_chunk.append(content)
                current_tokens += section_tokens
            else:
                # Save current chunk if it meets minimum size
                if current_chunk and current_tokens >= self.min_chunk_size:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'metadata': {
                            'source_title': document['title'],
                            'source_url': document['url'],
                            'heading': current_heading,
                            'chunk_type': 'section',
                            'tokens': current_tokens
                        }
                    })
                
                # Start new chunk
                if section_tokens > self.chunk_size:
                    # Section is too large, split it further
                    sub_chunks = self._split_large_section(content, heading, document)
                    chunks.extend(sub_chunks)
                    current_chunk = []
                    current_tokens = 0
                    current_heading = None
                else:
                    current_chunk = [content]
                    current_tokens = section_tokens
                    current_heading = heading
        
        # Add final chunk
        if current_chunk and current_tokens >= self.min_chunk_size:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'source_title': document['title'],
                    'source_url': document['url'],
                    'heading': current_heading,
                    'chunk_type': 'section',
                    'tokens': current_tokens
                }
            })
        
        return chunks
    
    def _split_large_section(self, content: str, heading: str, document: Dict) -> List[Dict]:
        """
        Split a large section into smaller chunks.
        
        Args:
            content: Section content
            heading: Section heading
            document: Parent document
            
        Returns:
            List of chunks
        """
        # Split by paragraphs first
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            if current_tokens + para_tokens <= self.chunk_size:
                current_chunk.append(para)
                current_tokens += para_tokens
            else:
                # Save current chunk
                if current_chunk and current_tokens >= self.min_chunk_size:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'metadata': {
                            'source_title': document['title'],
                            'source_url': document['url'],
                            'heading': heading,
                            'chunk_type': 'paragraph',
                            'tokens': current_tokens
                        }
                    })
                
                # Start new chunk
                if para_tokens > self.chunk_size:
                    # Paragraph is too large, split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    for sentence in sentences:
                        sent_tokens = self.count_tokens(sentence)
                        if current_tokens + sent_tokens <= self.chunk_size:
                            current_chunk.append(sentence)
                            current_tokens += sent_tokens
                        else:
                            if current_chunk and current_tokens >= self.min_chunk_size:
                                chunk_text = '\n\n'.join(current_chunk)
                                chunks.append({
                                    'text': chunk_text,
                                    'metadata': {
                                        'source_title': document['title'],
                                        'source_url': document['url'],
                                        'heading': heading,
                                        'chunk_type': 'sentence',
                                        'tokens': current_tokens
                                    }
                                })
                            current_chunk = [sentence]
                            current_tokens = sent_tokens
                else:
                    current_chunk = [para]
                    current_tokens = para_tokens
        
        # Add final chunk
        if current_chunk and current_tokens >= self.min_chunk_size:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'source_title': document['title'],
                    'source_url': document['url'],
                    'heading': heading,
                    'chunk_type': 'paragraph',
                    'tokens': current_tokens
                }
            })
        
        return chunks
    
    def split_by_size(self, document: Dict) -> List[Dict]:
        """
        Split document by fixed size with overlap (fallback method).
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunks with metadata
        """
        text = document.get('plain_text', document.get('markdown', ''))
        if not text:
            return []
        
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sent_tokens = self.count_tokens(sentence)
            
            if current_tokens + sent_tokens > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                if self.count_tokens(chunk_text) >= self.min_chunk_size:
                    chunks.append({
                        'text': chunk_text,
                        'metadata': {
                            'source_title': document['title'],
                            'source_url': document['url'],
                            'chunk_type': 'fixed_size',
                            'tokens': self.count_tokens(chunk_text)
                        }
                    })
                
                # Start new chunk with overlap
                overlap_sentences = []
                overlap_tokens = 0
                for sent in reversed(current_chunk):
                    sent_toks = self.count_tokens(sent)
                    if overlap_tokens + sent_toks <= self.chunk_overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_tokens += sent_toks
                    else:
                        break
                
                current_chunk = overlap_sentences + [sentence]
                current_tokens = overlap_tokens + sent_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sent_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            if self.count_tokens(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        'source_title': document['title'],
                        'source_url': document['url'],
                        'chunk_type': 'fixed_size',
                        'tokens': self.count_tokens(chunk_text)
                    }
                })
        
        return chunks
    
    def chunk_document(self, document: Dict) -> List[Dict]:
        """
        Chunk a document using the best available strategy.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunks with metadata
        """
        # Try semantic chunking first (by sections)
        if document.get('sections'):
            chunks = self.split_by_sections(document)
        else:
            # Fallback to size-based chunking
            chunks = self.split_by_size(document)
        
        logger.info(f"Chunked document '{document['title']}' into {len(chunks)} chunks")
        return chunks
    
    def chunk_all_documents(self) -> List[Dict]:
        """
        Chunk all processed documents.
        
        Returns:
            List of all chunks
        """
        processed_dir = Path(settings.data_processed_path)
        all_chunks = []
        
        json_files = list(processed_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} documents to chunk")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    document = json.load(f)
                
                chunks = self.chunk_document(document)
                
                # Save chunks
                safe_title = document['title'].replace('/', '_').replace('\\', '_')
                chunks_file = Path(settings.data_chunks_path) / f"{safe_title}_chunks.json"
                with open(chunks_file, 'w', encoding='utf-8') as f:
                    json.dump(chunks, f, indent=2, ensure_ascii=False)
                
                all_chunks.extend(chunks)
                
            except Exception as e:
                logger.error(f"Error chunking {json_file}: {e}")
        
        logger.info(f"Created {len(all_chunks)} total chunks")
        return all_chunks
