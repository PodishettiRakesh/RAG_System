"""
Test improved text chunking with overlap and newline handling.

Demonstrates:
1. Multi-line text processing (newlines handled correctly)
2. Overlapping chunks (context preserved at boundaries)
3. Configurable overlap levels
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.text_chunker import TextChunker


def test_multiline_text():
    """Test that multi-line text is processed correctly."""
    print("\n" + "="*70)
    print("TEST 1: Multi-line Text Processing")
    print("="*70)
    
    multiline_text = """
    Machine learning is a subset of artificial intelligence.
    It focuses on training algorithms to learn from data.
    
    Deep learning uses neural networks with multiple layers.
    This allows models to learn complex patterns automatically.
    """
    
    chunker = TextChunker(max_words=10, overlap_words=2)
    chunks = chunker.chunk_text(multiline_text)
    
    print(f"\nInput text:\n{multiline_text}")
    print(f"\nGenerated {len(chunks)} chunks with 10-word max and 2-word overlap:\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i} ({len(chunk.split())} words):")
        print(f"  {chunk}\n")


def test_overlap_effect():
    """Test how overlap preserves context."""
    print("\n" + "="*70)
    print("TEST 2: Overlap Effect on Context Preservation")
    print("="*70)
    
    text = "The quick brown fox jumps over the lazy dog in the forest. The forest is very green and peaceful. Birds sing in the trees all day long."
    
    print(f"\nOriginal text:\n{text}\n")
    
    # Test WITHOUT overlap
    chunker_no_overlap = TextChunker(max_words=8, overlap_words=0)
    chunks_no_overlap = chunker_no_overlap.chunk_text(text)
    
    print(f"WITHOUT overlap (max=8, overlap=0) - {len(chunks_no_overlap)} chunks:")
    for i, chunk in enumerate(chunks_no_overlap, 1):
        print(f"  Chunk {i}: {chunk}")
    
    # Test WITH overlap
    chunker_with_overlap = TextChunker(max_words=8, overlap_words=3)
    chunks_with_overlap = chunker_with_overlap.chunk_text(text)
    
    print(f"\nWITH overlap (max=8, overlap=3) - {len(chunks_with_overlap)} chunks:")
    for i, chunk in enumerate(chunks_with_overlap, 1):
        print(f"  Chunk {i}: {chunk}")
    
    print("\n💡 Note: With overlap, chunk boundaries share context words")
    print("   This helps LLM understand connections between chunks")


def test_special_formatting():
    """Test handling of special formatting and whitespace."""
    print("\n" + "="*70)
    print("TEST 3: Special Formatting and Whitespace")
    print("="*70)
    
    # Text with multiple spaces, newlines, and mixed formatting
    text_with_formatting = """
    
    Line 1: First part of content.
    Line 2: Second part    with    extra    spaces.
    
    
    Line 3: After multiple newlines.
    Line 4: Final part.
    """
    
    chunker = TextChunker(max_words=6, overlap_words=1)
    chunks = chunker.chunk_text(text_with_formatting)
    
    print(f"\nInput (raw with extra spaces/newlines):")
    print(repr(text_with_formatting))
    
    print(f"\nProcessed into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        print(f"  Chunk {i}: {chunk}")


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "="*70)
    print("TEST 4: Edge Cases")
    print("="*70)
    
    # Empty text
    chunker = TextChunker(max_words=5, overlap_words=2)
    print("\n1. Empty text:")
    result = chunker.chunk_text("")
    print(f"   Result: {result} (empty list)")
    
    # Single short word
    print("\n2. Single word:")
    result = chunker.chunk_text("Hello")
    print(f"   Result: {result}")
    
    # Text shorter than max_words
    print("\n3. Text shorter than max_words:")
    result = chunker.chunk_text("This is a short text")
    print(f"   Result: {result}")
    
    # Override overlap at call time
    print("\n4. Override overlap at call time:")
    text = "one two three four five six seven eight"
    result1 = chunker.chunk_text(text, overlap_words=0)
    result2 = chunker.chunk_text(text, overlap_words=3)
    print(f"   With overlap=0: {result1}")
    print(f"   With overlap=3: {result2}")


def test_env_chunking_defaults():
    """Test environment variables override TextChunker defaults."""
    original_max = os.getenv("CHUNK_MAX_WORDS")
    original_overlap = os.getenv("CHUNK_OVERLAP_WORDS")
    original_sentence = os.getenv("CHUNK_SENTENCE_AWARE")

    try:
        os.environ["CHUNK_MAX_WORDS"] = "7"
        os.environ["CHUNK_OVERLAP_WORDS"] = "2"
        os.environ["CHUNK_SENTENCE_AWARE"] = "true"

        chunker = TextChunker()
        assert chunker.max_words == 7, "CHUNK_MAX_WORDS did not apply"
        assert chunker.overlap_words == 2, "CHUNK_OVERLAP_WORDS did not apply"
        assert chunker.default_sentence_aware is True, "CHUNK_SENTENCE_AWARE did not apply"

        text = "First sentence. Second sentence. Third sentence."
        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 2, "Sentence-aware chunking did not produce multiple chunks"

        print("✅ Test env default chunking passed")
    finally:
        if original_max is not None:
            os.environ["CHUNK_MAX_WORDS"] = original_max
        else:
            os.environ.pop("CHUNK_MAX_WORDS", None)
        if original_overlap is not None:
            os.environ["CHUNK_OVERLAP_WORDS"] = original_overlap
        else:
            os.environ.pop("CHUNK_OVERLAP_WORDS", None)
        if original_sentence is not None:
            os.environ["CHUNK_SENTENCE_AWARE"] = original_sentence
        else:
            os.environ.pop("CHUNK_SENTENCE_AWARE", None)


if __name__ == "__main__":
    print("\n🧪 Testing Improved Text Chunking Strategy\n")
    
    try:
        test_multiline_text()
        test_overlap_effect()
        test_special_formatting()
        test_edge_cases()
        
        print("\n" + "="*70)
        print("✅ All tests completed successfully!")
        print("="*70 + "\n")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
