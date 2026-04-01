from typing import List
import numpy as np
import random

class SimpleEmbeddingService:
    """Simple embedding service for testing without heavy dependencies."""
    
    def __init__(self, dimension: int = 384):
        """
        Initialize SimpleEmbeddingService.
        
        Args:
            dimension (int): Dimension of vectors (384 to match real model)
        """
        self.dimension = dimension
        print(f"SimpleEmbeddingService initialized with {dimension} dimensions")
        print("Note: Using random embeddings for testing (replace with real model later)")
    
    def generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate mock embeddings for text chunks.
        
        Args:
            chunks (List[str]): List of text chunks to embed
        
        Returns:
            List[List[float]]: List of embedding vectors (384 dimensions each)
        """
        print(f"Generating mock embeddings for {len(chunks)} chunks...")
        
        embedding_lists = []
        
        for i, chunk in enumerate(chunks):
            # Generate deterministic but pseudo-random embeddings
            # In real implementation, this would be: model.encode(chunk)
            np.random.seed(hash(chunk) % 2**32)  # Deterministic based on content
            
            embedding = np.random.normal(0, 0.1, self.dimension).tolist()
            embedding_lists.append(embedding)
            
            print(f"Chunk {i+1}: {len(chunk.split())} words → {self.dimension} dimensions")
        
        print(f"Generated {len(embedding_lists)} embeddings")
        print(f"Each embedding has {self.dimension} dimensions")
        
        return embedding_lists
    
    def get_embedding_dimensions(self) -> int:
        """
        Get the dimension of embedding vectors.
        
        Returns:
            int: Number of dimensions (384)
        """
        return self.dimension
