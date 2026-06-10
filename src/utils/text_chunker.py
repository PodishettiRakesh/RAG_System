import re
from typing import List, Optional


class TextChunker:
    """Handles text chunking operations."""
    
    def __init__(self, max_words: int = 50, overlap_words: int = 5):
        """
        Initialize the TextChunker.
        
        Args:
            max_words (int): Maximum words per chunk (default: 50)
            overlap_words (int): Number of words to overlap between chunks (default: 5)
        """
        self.max_words = max_words
        self.overlap_words = min(overlap_words, max_words // 2)  # Prevent overlap > 50% of chunk
    
    def chunk_text(self, text: str, overlap_words: Optional[int] = None) -> List[str]:
        """
        Split text into overlapping chunks to preserve context and semantic continuity.
        
        # STRATEGY:
        # - Normalize newlines and whitespace while preserving text structure
        # - Use sliding window with overlap to maintain context across chunks
        # - Overlap prevents information loss at chunk boundaries
        #
        # EXAMPLE:
        # Text: "word1 word2 word3 word4 word5 word6 word7"
        # Max=4, Overlap=2:
        #   Chunk1: "word1 word2 word3 word4"
        #   Chunk2: "word3 word4 word5 word6"  (overlaps word3-word4)
        #   Chunk3: "word5 word6 word7"
        
        Args:
            text (str): Input text to chunk (supports multi-line content)
            overlap_words (int, optional): Override default overlap (max 50% of max_words)
        
        Returns:
            List[str]: List of overlapping text chunks
        """
        # Use provided overlap or fall back to instance default
        overlap = overlap_words if overlap_words is not None else self.overlap_words
        overlap = min(overlap, self.max_words // 2)  # Safety: prevent overlap > 50%
        
        # NEWLINE HANDLING: Normalize whitespace while preserving text integrity
        # Replace multiple consecutive newlines with space (paragraph breaks)
        text = re.sub(r'\n\s*\n+', ' ', text)
        # Replace single newlines with space (inline breaks)
        text = re.sub(r'\n', ' ', text)
        # Collapse multiple spaces into single space
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Extract words while preserving punctuation
        words = re.findall(r'\S+', text)
        
        if not words:
            return []
        
        chunks = []
        step = self.max_words - overlap  # Sliding window step size
        
        # SLIDING WINDOW with overlap: each chunk shares `overlap` words with previous
        for i in range(0, len(words), step):
            chunk_words = words[i:i + self.max_words]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            
            # Stop if we've reached the end (prevent creating tiny final chunk)
            if i + self.max_words >= len(words):
                break
        
        return chunks
    
    def print_chunks(self, chunks: List[str]) -> None:
        """Print chunks with numbering and details."""
        print(f"\n--- Text Chunks ({len(chunks)} chunks) ---")
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"Words: {len(chunk.split())}")
            print(f"Text: {chunk}")
            print("-" * 50)
