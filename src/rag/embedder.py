"""
Embedder Module
Creates embeddings using OpenAI API
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import List
import numpy as np
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class Embedder:
    """Handles text embedding generation using OpenAI"""
    
    def __init__(self, model_name: str = 'text-embedding-3-small'):
        """
        Initialize embedder with OpenAI API
        
        Args:
            model_name: OpenAI embedding model to use
        """
        self.model_name = model_name
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        
        # Set embedding dimension based on model
        if 'text-embedding-3-small' in model_name:
            self.embedding_dimension = 1536
        elif 'text-embedding-3-large' in model_name:
            self.embedding_dimension = 3072
        else:
            self.embedding_dimension = 1536  # default
        
        logger.info(f"Initialized OpenAI embedder: {model_name}")
        logger.info(f"Embedding dimension: {self.embedding_dimension}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Create embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embeddings
        """
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            return embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 100) -> np.ndarray:
        """
        Create embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once (OpenAI supports up to 2048)
            
        Returns:
            Numpy array of embeddings
        """
        try:
            logger.info(f"Creating embeddings for {len(texts)} texts using OpenAI")
            
            all_embeddings = []
            
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch
                )
                
                batch_embeddings = [np.array(item.embedding, dtype=np.float32) 
                                   for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return np.array(all_embeddings)
        
        except Exception as e:
            logger.error(f"Error creating batch embeddings: {str(e)}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model
        
        Returns:
            Embedding dimension
        """
        return self.embedding_dimension

# Made with Bob
