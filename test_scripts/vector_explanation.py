"""
Demonstration of how vector embeddings work
"""

from src.services.embedding_service import EmbeddingService

def demonstrate_vectors():
    """Show how vectors work with different inputs."""
    
    embedding_service = EmbeddingService()
    
    # Test 1: Single word
    print("=== SINGLE WORD ===")
    text1 = "Happy"
    chunks1 = embedding_service.generate_embeddings([text1])
    print(f"Text: '{text1}'")
    print(f"Vector dimensions: {len(chunks1[0])}")
    print(f"First 5 dimensions: {chunks1[0][:5]}")
    print()
    
    # Test 2: Two words
    print("=== TWO WORDS ===")
    text2 = "Happy sad"
    chunks2 = embedding_service.generate_embeddings([text2])
    print(f"Text: '{text2}'")
    print(f"Vector dimensions: {len(chunks2[0])}")
    print(f"First 5 dimensions: {chunks2[0][:5]}")
    print()
    
    # Test 3: Long text (multiple chunks)
    print("=== LONG TEXT ===")
    text3 = "This is a very long text that will be split into multiple chunks because it contains more than fifty words. " * 3
    chunks3 = embedding_service.generate_embeddings([text3])
    print(f"Text length: {len(text3)} characters")
    print(f"Words: {len(text3.split())}")
    print(f"Chunks: {len(chunks3)}")
    print(f"Total dimensions: {len(chunks3)} × {len(chunks3[0])} = {len(chunks3) * len(chunks3[0])}")
    print()
    
    # Compare vectors
    print("=== VECTOR COMPARISON ===")
    import numpy as np
    
    # Calculate similarity between happy and happy+sad
    vec1 = np.array(chunks1[0])
    vec2 = np.array(chunks2[0])
    
    # Simple cosine similarity
    similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    print(f"Similarity between 'Happy' and 'Happy sad': {similarity:.4f}")
    print("Higher similarity = more similar meaning")

if __name__ == "__main__":
    demonstrate_vectors()
