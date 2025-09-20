"""
Enhanced RAG (Retrieval-Augmented Generation) Engine
Handles document indexing, chunking, and context retrieval using TF-IDF
"""

import os
import pickle
from typing import List, Dict, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """Enhanced RAG engine with persistent storage and multiple document support"""
    
    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = cache_dir
        self.vectorizer = None
        self.chunk_vectors = None
        self.documents = {}  # doc_id -> {filename, chunks, chunk_count}
        self.chunk_to_doc = {}  # chunk_index -> doc_id
        self.is_indexed = False
        
        # TF-IDF parameters
        self.vectorizer_params = {
            'stop_words': 'english',
            'max_features': 10000,
            'ngram_range': (1, 2),
            'min_df': 1,
            'max_df': 0.95,
            'sublinear_tf': True
        }
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Try to load existing index
        self._load_index()
    
    def add_document(self, doc_id: str, text: str, filename: str) -> None:
        """
        Add a document to the RAG index
        
        Args:
            doc_id (str): Unique document identifier
            text (str): Document text content
            filename (str): Original filename
        """
        try:
            # Chunk the document
            chunks = self._chunk_text(text)
            
            if not chunks:
                raise ValueError("No valid chunks extracted from document")
            
            # Store document metadata
            self.documents[doc_id] = {
                'filename': filename,
                'chunks': chunks,
                'chunk_count': len(chunks),
                'text_length': len(text)
            }
            
            logger.info(f"Added document {filename} with {len(chunks)} chunks")
            
            # Rebuild the index
            self._rebuild_index()
            
        except Exception as e:
            logger.error(f"Error adding document {filename}: {e}")
            raise
    
    def remove_document(self, doc_id: str) -> None:
        """
        Remove a document from the RAG index
        
        Args:
            doc_id (str): Document identifier to remove
        """
        if doc_id in self.documents:
            filename = self.documents[doc_id]['filename']
            del self.documents[doc_id]
            logger.info(f"Removed document {filename}")
            
            # Rebuild index if there are remaining documents
            if self.documents:
                self._rebuild_index()
            else:
                self._clear_index()
    
    def retrieve_context(self, query: str, top_k: int = 3, min_similarity: float = 0.1) -> Dict:
        """
        Retrieve relevant context for a query
        
        Args:
            query (str): User query
            top_k (int): Number of top chunks to retrieve
            min_similarity (float): Minimum similarity threshold
            
        Returns:
            Dict: Retrieved context information
        """
        if not self.is_indexed:
            return {
                'context': '',
                'sources': [],
                'similarities': [],
                'avg_similarity': 0.0
            }
        
        try:
            # Vectorize the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.chunk_vectors)[0]
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            # Filter by minimum similarity
            relevant_indices = [
                idx for idx in top_indices 
                if similarities[idx] >= min_similarity
            ]
            
            if not relevant_indices:
                return {
                    'context': '',
                    'sources': [],
                    'similarities': [],
                    'avg_similarity': 0.0
                }
            
            # Collect context and sources
            context_chunks = []
            sources = []
            sim_scores = []
            
            for idx in relevant_indices:
                doc_id = self.chunk_to_doc[idx]
                doc_info = self.documents[doc_id]
                chunk_idx_in_doc = idx - sum(
                    self.documents[did]['chunk_count'] 
                    for did in self.documents 
                    if list(self.documents.keys()).index(did) < list(self.documents.keys()).index(doc_id)
                )
                
                chunk_text = doc_info['chunks'][chunk_idx_in_doc]
                context_chunks.append(chunk_text)
                
                sources.append({
                    'filename': doc_info['filename'],
                    'doc_id': doc_id,
                    'chunk_index': chunk_idx_in_doc,
                    'similarity': float(similarities[idx])
                })
                
                sim_scores.append(similarities[idx])
            
            # Combine context
            context = '\n\n'.join(context_chunks)
            avg_similarity = float(np.mean(sim_scores)) if sim_scores else 0.0
            
            logger.info(f"Retrieved {len(relevant_indices)} chunks with avg similarity {avg_similarity:.3f}")
            
            return {
                'context': context,
                'sources': sources,
                'similarities': sim_scores,
                'avg_similarity': avg_similarity
            }
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise
    
    def get_full_context(self, max_chunks: int = 20) -> str:
        """
        Get a sample of content from all documents for general material generation
        
        Args:
            max_chunks (int): Maximum number of chunks to include
            
        Returns:
            str: Combined context from all documents
        """
        if not self.documents:
            return ""
        
        all_chunks = []
        for doc_id, doc_info in self.documents.items():
            # Take first few chunks from each document
            chunks_per_doc = max(1, max_chunks // len(self.documents))
            all_chunks.extend(doc_info['chunks'][:chunks_per_doc])
        
        # Limit total chunks
        return '\n\n'.join(all_chunks[:max_chunks])
    
    def has_documents(self) -> bool:
        """Check if any documents are indexed"""
        return len(self.documents) > 0 and self.is_indexed
    
    def get_document_count(self) -> int:
        """Get number of indexed documents"""
        return len(self.documents)
    
    def get_chunk_count(self) -> int:
        """Get total number of chunks across all documents"""
        return sum(doc['chunk_count'] for doc in self.documents.values())
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for processing
        
        Args:
            text (str): Input text
            
        Returns:
            List[str]: Text chunks
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Further split very long paragraphs
        chunks = []
        max_chunk_length = 1000
        
        for paragraph in paragraphs:
            if len(paragraph) <= max_chunk_length:
                chunks.append(paragraph)
            else:
                # Split long paragraphs by sentences
                sentences = paragraph.split('. ')
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= max_chunk_length:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
        
        # Filter out very short chunks - use more lenient threshold
        min_chunk_length = 20
        filtered_chunks = [chunk for chunk in chunks if len(chunk.strip()) >= min_chunk_length]
        
        # If no chunks meet the criteria, return the original chunks anyway (except empty ones)
        if not filtered_chunks:
            filtered_chunks = [chunk for chunk in chunks if len(chunk.strip()) > 5]
        
        return filtered_chunks
    
    def _rebuild_index(self) -> None:
        """Rebuild the TF-IDF index with all documents"""
        if not self.documents:
            self._clear_index()
            return
        
        try:
            # Collect all chunks
            all_chunks = []
            self.chunk_to_doc = {}
            chunk_idx = 0
            
            for doc_id, doc_info in self.documents.items():
                for chunk in doc_info['chunks']:
                    all_chunks.append(chunk)
                    self.chunk_to_doc[chunk_idx] = doc_id
                    chunk_idx += 1
            
            # Initialize or fit vectorizer
            if self.vectorizer is None:
                self.vectorizer = TfidfVectorizer(**self.vectorizer_params)
                self.chunk_vectors = self.vectorizer.fit_transform(all_chunks)
            else:
                # Refit with new data
                self.vectorizer = TfidfVectorizer(**self.vectorizer_params)
                self.chunk_vectors = self.vectorizer.fit_transform(all_chunks)
            
            self.is_indexed = True
            
            # Save to cache
            self._save_index()
            
            logger.info(f"Rebuilt index with {len(all_chunks)} chunks from {len(self.documents)} documents")
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
            raise
    
    def _clear_index(self) -> None:
        """Clear the index when no documents remain"""
        self.vectorizer = None
        self.chunk_vectors = None
        self.chunk_to_doc = {}
        self.is_indexed = False
        
        # Clear cache files
        index_file = os.path.join(self.cache_dir, 'rag_index.pkl')
        if os.path.exists(index_file):
            os.remove(index_file)
    
    def _save_index(self) -> None:
        """Save index to cache"""
        try:
            index_file = os.path.join(self.cache_dir, 'rag_index.pkl')
            with open(index_file, 'wb') as f:
                pickle.dump({
                    'vectorizer': self.vectorizer,
                    'chunk_vectors': self.chunk_vectors,
                    'documents': self.documents,
                    'chunk_to_doc': self.chunk_to_doc,
                    'is_indexed': self.is_indexed
                }, f)
            logger.info("Index saved to cache")
        except Exception as e:
            logger.warning(f"Could not save index to cache: {e}")
    
    def _load_index(self) -> None:
        """Load index from cache"""
        try:
            index_file = os.path.join(self.cache_dir, 'rag_index.pkl')
            if os.path.exists(index_file):
                with open(index_file, 'rb') as f:
                    data = pickle.load(f)
                
                self.vectorizer = data['vectorizer']
                self.chunk_vectors = data['chunk_vectors']
                self.documents = data['documents']
                self.chunk_to_doc = data['chunk_to_doc']
                self.is_indexed = data['is_indexed']
                
                logger.info(f"Loaded index from cache: {len(self.documents)} documents")
        except Exception as e:
            logger.warning(f"Could not load index from cache: {e}")
            # Start fresh if cache is corrupted