from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Handles text embedding generation using sentence transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the EmbeddingService.
        
        Args:
            model_name (str): Name of the sentence transformer model
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        print(f"EmbeddingService initialized with model: {model_name}")
        print(f"Model dimensions: {self.model.get_sentence_embedding_dimension()}")
    
    def generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for text chunks.
        
        Args:
            chunks (List[str]): List of text chunks to embed
        
        Returns:
            List[List[float]]: List of embedding vectors (384 dimensions each)
        """
        print(f"Generating embeddings for {len(chunks)} chunks...")
        
        # Generate embeddings
        embeddings = self.model.encode(chunks)
        
        # Convert numpy arrays to lists for JSON serialization
        embedding_lists = [embedding.tolist() for embedding in embeddings]
        
        print(f"Generated {len(embedding_lists)} embeddings")
        print(f"Each embedding has {len(embedding_lists[0])} dimensions" if embedding_lists else "No embeddings generated")
        
        return embedding_lists
    
    def get_embedding_dimensions(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            int: Number of dimensions (384 for all-MiniLM-L6-v2)
        """
        return self.model.get_sentence_embedding_dimension()
