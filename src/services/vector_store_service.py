from typing import List, Dict, Tuple
import numpy as np
import faiss
from src.services.simple_embedding_service import SimpleEmbeddingService


class VectorStoreService:
    """Handles vector storage and retrieval using FAISS."""
    
    def __init__(self, dimension: int = 384):
        """
        Initialize VectorStoreService.
        
        Args:
            dimension (int): Dimension of vectors (384 for all-MiniLM-L6-v2)
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance (Euclidean)
        self.stored_chunks: List[str] = []  # Store original chunks
        self.embedding_service = SimpleEmbeddingService()
        
        print(f"VectorStoreService initialized:")
        print(f"- Vector dimension: {dimension}")
        print(f"- Index type: {type(self.index).__name__}")
        print(f"- Distance metric: L2 (Euclidean)")
        print(f"- Storage: In-memory (cleared on server restart)")
    
    def add_chunks(self, chunks: List[str]) -> int:
        """
        Add chunks to vector store.
        
        Args:
            chunks (List[str]): List of text chunks
        
        Returns:
            int: Number of chunks added
        """
        print(f"Adding {len(chunks)} chunks to vector store...")
        
        # Generate embeddings for chunks
        embeddings = self.embedding_service.generate_embeddings(chunks)
        
        # Convert to numpy array
        embedding_array = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS index
        self.index.add(embedding_array)
        
        # Store original chunks
        self.stored_chunks.extend(chunks)
        
        total_stored = self.index.ntotal
        print(f"Successfully added {len(chunks)} chunks")
        print(f"Total chunks in store: {total_stored}")
        
        return len(chunks)
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dict: Store statistics
        """
        return {
            "total_chunks": self.index.ntotal,
            "vector_dimension": self.dimension,
            "index_type": type(self.index).__name__,
            "distance_metric": "L2 (Euclidean)",
            "memory_usage": f"{self.index.ntotal * self.dimension * 4 / 1024 / 1024:.2f} MB",
            "storage_type": "In-memory (lost on restart)",
            "faiss_index_size": f"{self.index.ntotal} vectors × {self.dimension} dimensions"
        }
    
    def get_all_chunks(self) -> List[Dict]:
        """
        Get all stored chunks with their info.
        
        Returns:
            List[Dict]: List of chunk information
        """
        return [
            {
                "chunk_id": i,
                "text": chunk,
                "length": len(chunk),
                "words": len(chunk.split()),
                "vector_preview": f"[{self.embedding_service.generate_embeddings([chunk])[0][:5]}...]" if chunk else "[]"
            }
            for i, chunk in enumerate(self.stored_chunks)
        ]
    
    def get_detailed_structure(self) -> Dict:
        """
        Get detailed structure of FAISS storage.
        
        Returns:
            Dict: Detailed storage information
        """
        return {
            "faiss_index": {
                "type": "IndexFlatL2",
                "description": "Flat L2 distance index - exact search",
                "vectors_stored": self.index.ntotal,
                "dimensions": self.dimension,
                "is_trained": self.index.is_trained,
                "memory_bytes": self.index.ntotal * self.dimension * 4
            },
            "chunks_storage": {
                "total_chunks": len(self.stored_chunks),
                "total_characters": sum(len(chunk) for chunk in self.stored_chunks),
                "total_words": sum(len(chunk.split()) for chunk in self.stored_chunks),
                "average_chunk_size": sum(len(chunk.split()) for chunk in self.stored_chunks) / len(self.stored_chunks) if self.stored_chunks else 0
            },
            "server_lifecycle": {
                "persistence": "In-memory only",
                "data_loss_on_restart": True,
                "recommendation": "Use file-based or database storage for production"
            }
        }
