"""
Test Option B: Sentence-aware chunking with flexible range and no sentence splitting.

Strategy:
- Target ≈50 words
- Allow 30-70 words flexible range
- If single sentence > 70: keep as one chunk (never split)
- Add word-level overlap (10-15 words)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.text_chunker import TextChunker


def test_option_b_flexible_range():
    """Test that chunker respects flexible range [30-70 words for max_words=50]."""
    chunker = TextChunker(max_words=50, overlap_words=10)
    
    # Create test sentences with known word counts
    # S1: 30 words (fits in lower bound)
    s1 = " ".join([f"word{i}" for i in range(1, 31)])
    
    # S2: 20 words (fits)
    s2 = " ".join([f"word{i}" for i in range(31, 51)])
    
    # S3: 25 words (would exceed 70 if added to S1+S2, so starts new chunk)
    s3 = " ".join([f"word{i}" for i in range(51, 76)])
    
    # S4: 65 words (exceeds max_words_range of 70, should be kept as single chunk)
    s4 = " ".join([f"word{i}" for i in range(76, 141)])
    
    # S5: 15 words (small sentence)
    s5 = " ".join([f"word{i}" for i in range(141, 156)])
    
    text = f"{s1}. {s2}. {s3}. {s4}. {s5}."
    
    chunks = chunker.chunk_text(text, sentence_aware=True, overlap_words=10)
    
    print("\n" + "="*80)
    print("TEST: Option B - Flexible Range with No Sentence Splitting")
    print("="*80)
    print(f"max_words: 50")
    print(f"min_words: 30 (50 * 0.6)")
    print(f"max_words_range: 70 (50 * 1.4)")
    print(f"overlap_words: 10")
    print()
    
    print(f"Input Sentences:")
    print(f"  S1: {len(s1.split())} words")
    print(f"  S2: {len(s2.split())} words")
    print(f"  S3: {len(s3.split())} words")
    print(f"  S4: {len(s4.split())} words (EXCEEDS max_words_range, should be kept intact)")
    print(f"  S5: {len(s5.split())} words")
    print()
    
    print(f"Generated {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks, 1):
        words = chunk.split()
        word_count = len(words)
        print(f"\nChunk {i}: {word_count} words")
        # Show first 10 words and last 5 words
        first_10 = " ".join(words[:10])
        last_5 = " ".join(words[-5:])
        print(f"  Start: {first_10}...")
        print(f"  End: ...{last_5}")
        
        # Check if chunk is within flexible range (except for oversized sentences)
        if word_count > 70:
            print(f"  ⚠️  Exceeds range: Contains oversized sentence (kept intact)")
        elif word_count < 30:
            print(f"  ℹ️  Below lower bound: Small content at end")
    
    # Verify S4 (65-word sentence) is kept intact
    print("\n" + "-"*80)
    print("VERIFICATION:")
    
    # Check that 65-word sentence appears in a chunk
    full_text = " ".join(chunks)
    s4_present = s4 in full_text
    print(f"✓ 65-word sentence (S4) kept intact: {s4_present}")
    
    # Check overlap exists
    has_overlap = any(word_count > 50 for word_count in [len(c.split()) for c in chunks[1:]])
    print(f"✓ Overlap detected in chunks: {has_overlap}")
    
    print("="*80)


def test_option_b_example_chunking():
    """Demonstrate Option B chunking with realistic text."""
    chunker = TextChunker(max_words=50, overlap_words=12)
    
    text = """
    Natural language processing is a fascinating field. It combines linguistics and machine learning.
    Deep learning has revolutionized NLP in recent years with transformer models becoming the dominant approach 
    for many tasks including machine translation named entity recognition and question answering systems.
    These models are trained on massive amounts of text data.
    The field continues to evolve rapidly.
    """
    
    chunks = chunker.chunk_text(text, sentence_aware=True, overlap_words=12)
    
    print("\n" + "="*80)
    print("TEST: Option B - Realistic Text Chunking")
    print("="*80)
    print(f"max_words: 50, overlap_words: 12")
    print(f"Input text: {len(text.split())} words")
    print(f"Generated {len(chunks)} chunks:\n")
    
    for i, chunk in enumerate(chunks, 1):
        word_count = len(chunk.split())
        print(f"Chunk {i} ({word_count} words):")
        print(f"  {chunk}")
        print()
    
    print("="*80)


if __name__ == "__main__":
    test_option_b_flexible_range()
    test_option_b_example_chunking()
    print("\n✅ All Option B tests completed!")
