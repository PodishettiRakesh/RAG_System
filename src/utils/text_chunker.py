import re
from typing import List


class TextChunker:
    """Handles text chunking operations."""
    
    def __init__(self, max_words: int = 100):
        """
        Initialize the TextChunker.
        
        Args:
            max_words (int): Maximum words per chunk (default: 100)
        """
        self.max_words = max_words
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks of maximum specified words.
        
        Args:
            text (str): Input text to chunk
        
        Returns:
            List[str]: List of text chunks
        """
        # Split into words preserving punctuation
        words = re.findall(r'\S+', text)
        chunks = []
        
        for i in range(0, len(words), self.max_words):
            chunk_words = words[i:i + self.max_words]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
        
        return chunks
    
    def print_chunks(self, chunks: List[str]) -> None:
        """Print chunks with numbering and details."""
        print(f"\n--- Text Chunks ({len(chunks)} chunks) ---")
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"Words: {len(chunk.split())}")
            print(f"Text: {chunk}")
            print("-" * 50)
