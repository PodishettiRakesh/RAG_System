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
    
    def chunk_text(
        self,
        text: str,
        overlap_words: Optional[int] = None,
        sentence_aware: bool = False,
        overlap_sentences: Optional[int] = None,
    ) -> List[str]:
        """
        Split text into chunks while preserving sentence boundaries and overlapping context.
        
        # STRATEGY:
        # - Normalize newlines and whitespace while preserving text structure
        # - Optionally keep sentences intact to avoid splitting semantic units
        # - Use overlap so each chunk retains context from the previous chunk
        #
        # EXAMPLE:
        # Text: "word1 word2 word3 word4 word5 word6 word7"
        # Max=4, Overlap=2:
        #   Chunk1: "word1 word2 word3 word4"
        #   Chunk2: "word3 word4 word5 word6"
        #   Chunk3: "word5 word6 word7"
        
        Args:
            text (str): Input text to chunk (supports multi-line content)
            overlap_words (int, optional): Override default overlap (max 50% of max_words)
            sentence_aware (bool): Keep sentence boundaries intact when chunking
            overlap_sentences (int, optional): Override sentence overlap count when sentence_aware=True
        
        Returns:
            List[str]: List of text chunks
        """
        # Use provided overlap or fall back to instance default
        overlap = overlap_words if overlap_words is not None else self.overlap_words
        overlap = min(overlap, self.max_words // 2)  # Safety: prevent overlap > 50%
        
        # NEWLINE HANDLING: Normalize whitespace while preserving text integrity
        # Replace multiple consecutive newlines with a single space (paragraph breaks)
        text = re.sub(r'\n\s*\n+', ' ', text)
        # Replace single newlines with space (inline breaks)
        text = re.sub(r'\n', ' ', text)
        # Collapse multiple spaces into single space
        text = re.sub(r'\s+', ' ', text).strip()
        
        if sentence_aware:
            if overlap_sentences is None:
                overlap_sentences = max(1, overlap // 5)
            return self._sentence_aware_chunks(text, overlap_sentences)
        
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
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split normalized text into sentence segments without losing punctuation."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [sentence.strip() for sentence in sentences if sentence.strip()]
    
    def _sentence_aware_chunks(self, text: str, overlap: int) -> List[str]:
        """Create chunks that keep sentences intact and optionally overlap by sentence boundaries."""
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []
        
        # Build chunks from full sentences without splitting sentences across boundaries
        chunk_sentence_groups: List[List[str]] = []
        current_group: List[str] = []
        current_count = 0
        
        for sentence in sentences:
            sentence_words = re.findall(r'\S+', sentence)
            if not sentence_words:
                continue
            
            if current_count + len(sentence_words) <= self.max_words:
                current_group.append(sentence)
                current_count += len(sentence_words)
            else:
                if current_group:
                    chunk_sentence_groups.append(current_group)
                
                if len(sentence_words) > self.max_words:
                    # Very long sentence: split by words as a fallback, preserving chunk size
                    for i in range(0, len(sentence_words), self.max_words):
                        chunk = ' '.join(sentence_words[i:i + self.max_words])
                        chunk_sentence_groups.append([chunk])
                    current_group = []
                    current_count = 0
                else:
                    current_group = [sentence]
                    current_count = len(sentence_words)
        
        if current_group:
            chunk_sentence_groups.append(current_group)
        
        if overlap <= 0 or len(chunk_sentence_groups) <= 1:
            return [' '.join(group) for group in chunk_sentence_groups]
        
        # Overlap by sentence groups to preserve sentence integrity
        overlap_sentences = max(1, overlap)
        overlapped_chunks: List[str] = []
        for idx, group in enumerate(chunk_sentence_groups):
            if idx == 0:
                overlapped_chunks.append(' '.join(group))
                continue
            prev_group = chunk_sentence_groups[idx - 1]
            overlap_segment = prev_group[-overlap_sentences:]
            overlapped_chunks.append(' '.join(overlap_segment + group))
        
        return overlapped_chunks
    
    def print_chunks(self, chunks: List[str]) -> None:
        """Print chunks with numbering and details."""
        print(f"\n--- Text Chunks ({len(chunks)} chunks) ---")
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"Words: {len(chunk.split())}")
            print(f"Text: {chunk}")
            print("-" * 50)
