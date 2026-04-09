from typing import List, Dict, Tuple
import numpy as np
import faiss
from src.services.embedding_service import EmbeddingService
from src.utils.observability import observability, track_operation


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
        self.embedding_service = EmbeddingService()
        
        print(f"VectorStoreService initialized:")
        print(f"- Vector dimension: {dimension}")
        print(f"- Index type: {type(self.index).__name__}")
        print(f"- Distance metric: L2 (Euclidean)")
        print(f"- Storage: In-memory (cleared on server restart)")
    
    @track_operation("embedding_generation")
    def add_chunks(self, chunks: List[str]) -> int:
        """
        Add chunks to vector store.
        
        Args:
            chunks (List[str]): List of text chunks
        
        Returns:
            int: Number of chunks added
        """
        print(f"Adding {len(chunks)} chunks to vector store...")
        
        with observability.track_latency("embedding_generation", {"chunks_count": len(chunks)}) as operation_id:
            # Generate embeddings for chunks
            embeddings = self.embedding_service.generate_embeddings(chunks)
            
            # Track embedding metrics
            observability.track_embedding_generation(
                chunks_count=len(chunks),
                dimensions=self.dimension,
                operation_id=operation_id
            )
        
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
    
    def search_similar(self, query_text: str, k: int = 3) -> List[Dict]:
        """
        Search for similar chunks using query text.
        
        Args:
            query_text (str): Query text to search for
            k (int): Number of similar chunks to return (default: 3)
        
        Returns:
            List[Dict]: List of similar chunks with distances
        """
        print(f"Searching for top {k} similar chunks to query: '{query_text[:50]}...'")
        
        with observability.track_latency("vector_search", {"query_length": len(query_text), "k": k}) as operation_id:
            # Generate embedding for query
            query_embeddings = self.embedding_service.generate_embeddings([query_text])
            query_vector = np.array([query_embeddings[0]], dtype=np.float32)
            
            # Search in FAISS index
            distances, indices = self.index.search(query_vector, k)
            
            # Prepare results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.stored_chunks):  # Valid index
                    chunk_text = self.stored_chunks[idx]
                    results.append({
                        "rank": i + 1,
                        "chunk_id": int(idx),  # Convert numpy.int64 to int
                        "chunk_text": chunk_text,
                        "similarity_score": float(distance),  # Convert numpy.float32 to float
                        "distance_type": "L2 (Euclidean)",
                        "words": len(chunk_text.split()),
                        "characters": len(chunk_text),
                        "lower_is_better": True  # Lower L2 distance = more similar
                    })
            
            # Track search metrics
            observability.track_vector_search(
                query_length=len(query_text),
                k=k,
                results_count=len(results),
                operation_id=operation_id
            )
        
        print(f"Found {len(results)} similar chunks")
        for result in results:
            print(f"  Rank {result['rank']}: Chunk {result['chunk_id']} (distance: {result['similarity_score']:.4f})")
        
        return results
    
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
