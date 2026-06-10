import os
import re
from typing import List, Optional


class TextChunker:
    """Handles text chunking operations."""
    
    def __init__(self, max_words: Optional[int] = None, overlap_words: Optional[int] = None):
        """
        Initialize the TextChunker.
        
        Environment variables can override chunking defaults:
        - CHUNK_MAX_WORDS
        - CHUNK_OVERLAP_WORDS
        - CHUNK_SENTENCE_AWARE
        - CHUNK_OVERLAP_SENTENCES
        
        Args:
            max_words (int, optional): Maximum words per chunk
            overlap_words (int, optional): Number of words to overlap between chunks
        """
        env_max_words = os.getenv("CHUNK_MAX_WORDS")
        env_overlap_words = os.getenv("CHUNK_OVERLAP_WORDS")
        env_sentence_aware = os.getenv("CHUNK_SENTENCE_AWARE")
        env_overlap_sentences = os.getenv("CHUNK_OVERLAP_SENTENCES")

        self.max_words = int(env_max_words) if env_max_words is not None else (max_words if max_words is not None else 50)
        overlap_value = int(env_overlap_words) if env_overlap_words is not None else (overlap_words if overlap_words is not None else 5)
        self.overlap_words = min(overlap_value, self.max_words // 2)  # Prevent overlap > 50% of chunk

        self.default_sentence_aware = self._parse_bool(env_sentence_aware, default=False)
        self.default_overlap_sentences = int(env_overlap_sentences) if env_overlap_sentences is not None else None
    
    @staticmethod
    def _parse_bool(value: Optional[str], default: bool = False) -> bool:
        """Parse boolean environment variables from string values."""
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    
    def chunk_text(
        self,
        text: str,
        overlap_words: Optional[int] = None,
        sentence_aware: Optional[bool] = None,
        overlap_sentences: Optional[int] = None,
    ) -> List[str]:
        """
        Split text into chunks while preserving sentence boundaries and overlapping context.
        
        SENTENCE-AWARE MODE (when enabled):
        - Splits text into sentences first
        - Targets ~max_words per chunk (e.g., 50 words)
        - Allows flexible range: 60%-140% of max_words (e.g., 30-70 for max_words=50)
        - **Never splits sentences**: Even if a sentence exceeds the max range, it stays intact
        - Applies word-level overlap: Last N words from previous chunk prepended to next chunk
        
        WORD-BASED MODE (default):
        - Uses sliding window with word-level overlap
        - Respects exact max_words limit
        - May split sentences that are very long
        
        EXAMPLE (Sentence-Aware with max_words=50, overlap=10):
        S1 (30 words) + S2 (20 words) = Chunk 1 (50 words)
        [Last 10 words of Chunk1] + S3 (25 words) + S4 (20 words) = Chunk 2 (55 words)
        [Last 10 words of Chunk2] + S5 (65 words) = Chunk 3 (75 words, sentence kept intact!)
        
        Args:
            text (str): Input text to chunk (supports multi-line content)
            overlap_words (int, optional): Override default overlap (max 50% of max_words)
            sentence_aware (bool): Keep sentence boundaries intact when chunking
            overlap_sentences (int, optional): Deprecated (kept for compatibility)
        
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
        
        if sentence_aware is None:
            sentence_aware = self.default_sentence_aware
        
        if sentence_aware:
            # Use word-level overlap for sentence-aware chunking
            # (not sentence-level overlap; _sentence_aware_chunks expects word count)
            return self._sentence_aware_chunks(text, overlap)
        
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
        """
        Create chunks from complete sentences with flexible sizing.
        
        Strategy:
        - Target chunk size is max_words (e.g., 50)
        - Allow flexible range: [min_words, max_words_range] where:
          - min_words = max_words * 0.6 (e.g., 30 for max_words=50)
          - max_words_range = max_words * 1.4 (e.g., 70 for max_words=50)
        - If a sentence exceeds max_words_range, keep it as single chunk (never split sentences)
        - Apply word-level overlap between chunks (from last N words of previous chunk)
        """
        sentences = self._split_into_sentences(text)
        if not sentences:
            return []
        
        # Define flexible range for chunk size
        min_words = int(self.max_words * 0.6)  # Lower bound (e.g., 30 for max_words=50)
        max_words_range = int(self.max_words * 1.4)  # Upper bound (e.g., 70 for max_words=50)
        
        # Step 1: Build chunks from complete sentences, respecting the flexible range
        chunks = []
        current_chunk_sentences = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = re.findall(r'\S+', sentence)
            if not sentence_words:
                continue
            
            sentence_word_count = len(sentence_words)
            
            # If the sentence itself exceeds max_words_range, keep it as a separate chunk (never split)
            if sentence_word_count > max_words_range:
                # Finalize current chunk if it has content
                if current_chunk_sentences:
                    chunks.append(' '.join(current_chunk_sentences))
                    current_chunk_sentences = []
                    current_word_count = 0
                # Add the oversized sentence as its own chunk
                chunks.append(sentence)
            elif current_word_count + sentence_word_count <= max_words_range:
                # Sentence fits in current chunk
                current_chunk_sentences.append(sentence)
                current_word_count += sentence_word_count
            else:
                # Sentence doesn't fit; finalize current chunk and start new one
                if current_chunk_sentences:
                    chunks.append(' '.join(current_chunk_sentences))
                current_chunk_sentences = [sentence]
                current_word_count = sentence_word_count
        
        # Finalize last chunk
        if current_chunk_sentences:
            chunks.append(' '.join(current_chunk_sentences))
        
        # Step 2: Apply word-level overlap between chunks
        if overlap <= 0 or len(chunks) <= 1:
            return chunks
        
        final_chunks = []
        prev_chunk_words = []
        
        for chunk in chunks:
            chunk_words = re.findall(r'\S+', chunk)
            
            if not prev_chunk_words:
                # First chunk: no overlap from previous
                final_chunks.append(chunk)
            else:
                # Add overlap from previous chunk (last N words)
                overlap_count = min(overlap, len(prev_chunk_words))
                overlap_words = prev_chunk_words[-overlap_count:]
                combined_words = overlap_words + chunk_words
                final_chunks.append(' '.join(combined_words))
            
            # Save chunk words for next iteration's overlap
            prev_chunk_words = chunk_words
        
        return final_chunks
    
    def print_chunks(self, chunks: List[str]) -> None:
        """Print chunks with numbering and details."""
        print(f"\n--- Text Chunks ({len(chunks)} chunks) ---")
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}:")
            print(f"Words: {len(chunk.split())}")
            print(f"Text: {chunk}")
            print("-" * 50)
