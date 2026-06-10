from typing import List, Dict, Tuple, Optional
import numpy as np
import faiss
import json
import os
from datetime import datetime
from pathlib import Path
from src.services.embedding_service import EmbeddingService
from src.utils.observability import observability, track_operation


class VectorStoreService:
    """Handles vector storage and retrieval using FAISS with persistent disk storage."""
    
    def __init__(self, dimension: int = 384, storage_dir: str = "storage"):
        """
        Initialize VectorStoreService with disk-backed persistence.
        
        Args:
            dimension (int): Dimension of vectors (384 for all-MiniLM-L6-v2)
            storage_dir (str): Directory for persistent storage (default: "storage")
        """
        self.dimension = dimension
        self.storage_dir = Path(storage_dir)
        self.index_path = self.storage_dir / "faiss_index.bin"
        self.chunks_path = self.storage_dir / "chunks.json"
        self.metadata_path = self.storage_dir / "metadata.json"
        
        self.embedding_service = EmbeddingService()
        self.stored_chunks: List[str] = []
        
        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing storage or create new index
        if self.index_path.exists() and self.chunks_path.exists():
            self._load_from_disk()
            print(f"VectorStoreService initialized (loaded from disk):")
        else:
            self.index = faiss.IndexFlatL2(dimension)
            print(f"VectorStoreService initialized (new in-memory index):")
        
        print(f"- Vector dimension: {dimension}")
        print(f"- Index type: {type(self.index).__name__}")
        print(f"- Distance metric: L2 (Euclidean)")
        print(f"- Storage directory: {self.storage_dir.absolute()}")
        print(f"- Stored chunks: {self.index.ntotal}")
        print(f"- Persistent storage: Enabled")
    
    def _load_from_disk(self) -> None:
        """Load FAISS index and chunks from disk."""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load chunks
            with open(self.chunks_path, 'r') as f:
                self.stored_chunks = json.load(f)
            
            # Validate consistency
            if self.index.ntotal != len(self.stored_chunks):
                print(f"⚠️ Warning: FAISS index size ({self.index.ntotal}) != chunks count ({len(self.stored_chunks)})")
                print("Rebuilding FAISS index from chunks...")
                self._rebuild_index_from_chunks()
            
            print(f"✅ Loaded {self.index.ntotal} vectors and {len(self.stored_chunks)} chunks from disk")
        except Exception as e:
            print(f"❌ Error loading from disk: {str(e)}")
            print("Creating new index...")
            self.index = faiss.IndexFlatL2(self.dimension)
            self.stored_chunks = []
    
    def _rebuild_index_from_chunks(self) -> None:
        """Rebuild FAISS index from stored chunks (useful for recovery)."""
        if not self.stored_chunks:
            print("No chunks to rebuild index from")
            return
        
        print(f"Rebuilding FAISS index from {len(self.stored_chunks)} chunks...")
        embeddings = self.embedding_service.generate_embeddings(self.stored_chunks)
        embedding_array = np.array(embeddings, dtype=np.float32)
        
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embedding_array)
        
        print(f"✅ Rebuilt FAISS index with {self.index.ntotal} vectors")
        self._save_index()
    
    def _save_index(self) -> None:
        """Save FAISS index to disk."""
        try:
            faiss.write_index(self.index, str(self.index_path))
        except Exception as e:
            print(f"❌ Error saving FAISS index: {str(e)}")
    
    def _save_chunks(self) -> None:
        """Save chunks to disk."""
        try:
            with open(self.chunks_path, 'w') as f:
                json.dump(self.stored_chunks, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving chunks: {str(e)}")
    
    def _save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            metadata = {
                "embedding_model": self.embedding_service.model_name,
                "vector_dimension": self.dimension,
                "vector_count": self.index.ntotal,
                "index_type": type(self.index).__name__,
                "distance_metric": "L2 (Euclidean)",
                "created_at": self._get_metadata_field("created_at"),
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving metadata: {str(e)}")
    
    def _get_metadata_field(self, field: str) -> str:
        """Get a field from existing metadata or return current timestamp."""
        try:
            if self.metadata_path.exists():
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                    if field in metadata:
                        return metadata[field]
        except Exception:
            pass
        return datetime.utcnow().isoformat() + "Z"
    
    def persist_storage(self) -> None:
        """Persist all storage to disk (FAISS index, chunks, metadata)."""
        self._save_index()
        self._save_chunks()
        self._save_metadata()
    
    @track_operation("embedding_generation")
    def add_chunks(self, chunks: List[str]) -> int:
        """
        Add chunks to vector store and persist to disk.
        
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
        
        # Persist to disk
        self.persist_storage()
        
        total_stored = self.index.ntotal
        print(f"✅ Successfully added {len(chunks)} chunks")
        print(f"Total chunks in store: {total_stored}")
        print(f"Persisted to: {self.storage_dir.absolute()}")
        
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
            "storage_type": "Persistent (disk-backed)",
            "storage_directory": str(self.storage_dir.absolute()),
            "faiss_index_file": str(self.index_path),
            "chunks_file": str(self.chunks_path),
            "metadata_file": str(self.metadata_path),
            "files_exist": {
                "faiss_index.bin": self.index_path.exists(),
                "chunks.json": self.chunks_path.exists(),
                "metadata.json": self.metadata_path.exists()
            },
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
        # Load metadata if available
        metadata = {}
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
            except Exception:
                pass
        
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
            "disk_persistence": {
                "storage_directory": str(self.storage_dir.absolute()),
                "faiss_index_path": str(self.index_path),
                "chunks_path": str(self.chunks_path),
                "metadata_path": str(self.metadata_path),
                "files_exist": {
                    "faiss_index.bin": self.index_path.exists(),
                    "chunks.json": self.chunks_path.exists(),
                    "metadata.json": self.metadata_path.exists()
                },
                "file_sizes_bytes": {
                    "faiss_index.bin": self.index_path.stat().st_size if self.index_path.exists() else 0,
                    "chunks.json": self.chunks_path.stat().st_size if self.chunks_path.exists() else 0,
                    "metadata.json": self.metadata_path.stat().st_size if self.metadata_path.exists() else 0
                }
            },
            "metadata": metadata if metadata else {
                "embedding_model": self.embedding_service.model_name,
                "vector_dimension": self.dimension,
                "index_type": type(self.index).__name__
            },
            "server_lifecycle": {
                "persistence": "Disk-backed (saved to storage/)",
                "data_loss_on_restart": False,
                "recommendation": "Data persists across server restarts"
            }
        }
