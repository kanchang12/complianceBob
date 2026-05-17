"""
Vector Store Module
SQLite-based vector storage with similarity search
"""

import sqlite3
import numpy as np
from typing import List, Dict, Tuple
import json
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """Handles vector storage and similarity search using SQLite"""
    
    def __init__(self, db_path: str = "database/compliance.db"):
        """
        Initialize vector store
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection"""
        try:
            # Allow connection to be used across threads (Flask uses multiple threads)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            cursor = self.conn.cursor()
            
            # Create embeddings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    chunk_text TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_id 
                ON embeddings(document_id)
            """)
            
            self.conn.commit()
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise
    
    def store_embedding(self, document_id: str, chunk_text: str, 
                       embedding: np.ndarray, metadata: Dict = None):
        """
        Store an embedding in the database
        
        Args:
            document_id: Unique identifier for the document
            chunk_text: The text chunk
            embedding: The embedding vector
            metadata: Additional metadata as dictionary
        """
        try:
            cursor = self.conn.cursor()
            
            # Convert embedding to bytes
            embedding_bytes = embedding.tobytes()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO embeddings (document_id, chunk_text, embedding, metadata)
                VALUES (?, ?, ?, ?)
            """, (document_id, chunk_text, embedding_bytes, metadata_json))
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            raise
    
    def store_embeddings_batch(self, embeddings_data: List[Tuple]):
        """
        Store multiple embeddings at once
        
        Args:
            embeddings_data: List of tuples (document_id, chunk_text, embedding, metadata)
        """
        try:
            cursor = self.conn.cursor()
            
            processed_data = []
            for doc_id, text, embedding, metadata in embeddings_data:
                embedding_bytes = embedding.tobytes()
                metadata_json = json.dumps(metadata) if metadata else None
                processed_data.append((doc_id, text, embedding_bytes, metadata_json))
            
            cursor.executemany("""
                INSERT INTO embeddings (document_id, chunk_text, embedding, metadata)
                VALUES (?, ?, ?, ?)
            """, processed_data)
            
            self.conn.commit()
            logger.info(f"Stored {len(embeddings_data)} embeddings")
        except Exception as e:
            logger.error(f"Error storing batch embeddings: {str(e)}")
            raise
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        return dot_product / (norm1 * norm2)
    
    def search_similar(self, query_embedding: np.ndarray, 
                      top_k: int = 5, document_id: str = None) -> List[Dict]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            document_id: Optional filter by document ID
            
        Returns:
            List of similar chunks with scores
        """
        try:
            cursor = self.conn.cursor()
            
            # Fetch embeddings
            if document_id:
                cursor.execute("""
                    SELECT id, document_id, chunk_text, embedding, metadata
                    FROM embeddings
                    WHERE document_id = ?
                """, (document_id,))
            else:
                cursor.execute("""
                    SELECT id, document_id, chunk_text, embedding, metadata
                    FROM embeddings
                """)
            
            results = []
            for row in cursor.fetchall():
                # Convert bytes back to numpy array
                stored_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                
                # Calculate similarity
                similarity = self.cosine_similarity(query_embedding, stored_embedding)
                
                results.append({
                    'id': row['id'],
                    'document_id': row['document_id'],
                    'chunk_text': row['chunk_text'],
                    'similarity': float(similarity),
                    'metadata': json.loads(row['metadata']) if row['metadata'] else None
                })
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
        
        except Exception as e:
            logger.error(f"Error searching similar embeddings: {str(e)}")
            raise
    
    def delete_document_embeddings(self, document_id: str):
        """
        Delete all embeddings for a document
        
        Args:
            document_id: Document identifier
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))
            self.conn.commit()
            logger.info(f"Deleted embeddings for document: {document_id}")
        except Exception as e:
            logger.error(f"Error deleting embeddings: {str(e)}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

# Made with Bob
