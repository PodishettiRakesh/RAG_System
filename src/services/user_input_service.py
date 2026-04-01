from typing import Optional
from ..utils.text_chunker import TextChunker


class UserInputService:
    """Handles user input and processing operations."""
    
    def __init__(self, chunker: Optional[TextChunker] = None):
        """
        Initialize the UserInputService.
        
        Args:
            chunker (TextChunker): Text chunker instance
        """
        self.chunker = chunker or TextChunker()
    
    def process_user_input(self, user_text: str) -> None:
        """
        Process user input by chunking and displaying it.
        
        Args:
            user_text (str): Input text from user
        """
        print(f"Entered Text: {user_text}")
        
        # Create chunks from the input text
        chunks = self.chunker.chunk_text(user_text)
        self.chunker.print_chunks(chunks)
