"""
Test persistent FAISS storage functionality.

Tests:
1. New VectorStoreService creates storage files
2. Adding chunks persists to disk
3. Reloading VectorStoreService loads saved data
4. Vector IDs match chunk indexes after reload
"""

import json
import shutil
import tempfile
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.vector_store_service import VectorStoreService


def test_persistence_creates_files():
    """Test that adding chunks creates storage files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_storage"
        
        # Create new service
        service = VectorStoreService(storage_dir=str(storage_path))
        
        # Add sample chunks
        chunks = [
            "The quick brown fox jumps over the lazy dog.",
            "Machine learning is a subset of artificial intelligence.",
            "Python is a popular programming language."
        ]
        
        service.add_chunks(chunks)
        
        # Verify files were created
        assert (storage_path / "faiss_index.bin").exists(), "FAISS index file not created"
        assert (storage_path / "chunks.json").exists(), "Chunks file not created"
        assert (storage_path / "metadata.json").exists(), "Metadata file not created"
        
        print("✅ Test 1 passed: Storage files created")


def test_persistence_reload():
    """Test that a new VectorStoreService instance can reload saved data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_storage"
        
        # First service: add chunks
        chunks = [
            "The quick brown fox jumps over the lazy dog.",
            "Machine learning is a subset of artificial intelligence.",
            "Python is a popular programming language.",
            "Data science combines statistics and programming."
        ]
        
        service1 = VectorStoreService(storage_dir=str(storage_path))
        service1.add_chunks(chunks)
        
        total_chunks_1 = service1.index.ntotal
        stored_chunks_1 = len(service1.stored_chunks)
        
        # Second service: should load from disk
        service2 = VectorStoreService(storage_dir=str(storage_path))
        
        # Verify data is identical
        assert service2.index.ntotal == total_chunks_1, f"Loaded {service2.index.ntotal} vectors, expected {total_chunks_1}"
        assert len(service2.stored_chunks) == stored_chunks_1, f"Loaded {len(service2.stored_chunks)} chunks, expected {stored_chunks_1}"
        assert service2.stored_chunks == chunks, "Loaded chunks don't match original chunks"
        
        print(f"✅ Test 2 passed: Reloaded {service2.index.ntotal} vectors and {len(service2.stored_chunks)} chunks")


def test_consistency_after_reload():
    """Test that retrieval works after reload (vector IDs match chunk indexes)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_storage"
        
        chunks = [
            "The quick brown fox",
            "Machine learning algorithms",
            "Python programming tutorial",
        ]
        
        # Add chunks
        service1 = VectorStoreService(storage_dir=str(storage_path))
        service1.add_chunks(chunks)
        
        # Search before reload
        results_before = service1.search_similar("machine learning", k=2)
        
        # Reload service
        service2 = VectorStoreService(storage_dir=str(storage_path))
        
        # Search after reload
        results_after = service2.search_similar("machine learning", k=2)
        
        # Verify results are consistent
        assert len(results_before) == len(results_after), "Result count mismatch"
        
        for r1, r2 in zip(results_before, results_after):
            assert r1["chunk_id"] == r2["chunk_id"], "Chunk IDs don't match after reload"
            assert r1["chunk_text"] == r2["chunk_text"], "Chunk text doesn't match"
            # Similarity scores might differ slightly due to floating point, but should be close
            assert abs(r1["similarity_score"] - r2["similarity_score"]) < 0.001, "Similarity scores differ significantly"
        
        print("✅ Test 3 passed: Retrieval consistency verified after reload")


def test_metadata_persistence():
    """Test that metadata is correctly saved and loaded."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_storage"
        
        chunks = ["Sample text chunk"]
        
        service = VectorStoreService(storage_dir=str(storage_path))
        service.add_chunks(chunks)
        
        # Read metadata file
        metadata_path = Path(storage_path) / "metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Verify metadata fields
        assert "embedding_model" in metadata, "Missing embedding_model field"
        assert "vector_dimension" in metadata, "Missing vector_dimension field"
        assert "vector_count" in metadata, "Missing vector_count field"
        assert "created_at" in metadata, "Missing created_at field"
        assert "updated_at" in metadata, "Missing updated_at field"
        assert metadata["vector_count"] == 1, "Vector count mismatch"
        assert metadata["vector_dimension"] == 384, "Vector dimension mismatch"
        
        print(f"✅ Test 4 passed: Metadata persisted correctly")


def test_incremental_adds():
    """Test that multiple add_chunks calls accumulate correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_storage"
        
        service = VectorStoreService(storage_dir=str(storage_path))
        
        # First batch
        batch1 = ["Chunk one", "Chunk two"]
        service.add_chunks(batch1)
        assert service.index.ntotal == 2, "After first batch: expected 2 vectors"
        
        # Second batch
        batch2 = ["Chunk three", "Chunk four", "Chunk five"]
        service.add_chunks(batch2)
        assert service.index.ntotal == 5, "After second batch: expected 5 vectors"
        
        # Reload and verify
        service2 = VectorStoreService(storage_dir=str(storage_path))
        assert service2.index.ntotal == 5, "After reload: expected 5 vectors"
        assert len(service2.stored_chunks) == 5, "After reload: expected 5 chunks"
        assert service2.stored_chunks == batch1 + batch2, "Chunks order mismatch after reload"
        
        print("✅ Test 5 passed: Incremental adds work correctly")


if __name__ == "__main__":
    print("\n🧪 Running persistent storage tests...\n")
    
    try:
        test_persistence_creates_files()
        test_persistence_reload()
        test_consistency_after_reload()
        test_metadata_persistence()
        test_incremental_adds()
        
        print("\n✅ All tests passed!\n")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
