"""
Examples to explain classes, Pydantic, and your API structure
"""

# ===== REGULAR FUNCTION =====
def regular_function(text):
    """Simple function you're familiar with"""
    words = len(text.split())
    return words

# ===== CLASS EXAMPLE =====
class TextChunker:
    """Class that handles text chunking"""
    
    def __init__(self, max_words=100):
        """Constructor - runs when you create TextChunker()"""
        self.max_words = max_words
        print(f"TextChunker created with max_words={max_words}")
    
    def chunk_text(self, text):
        """Method - function inside class"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.max_words):
            chunk = ' '.join(words[i:i + self.max_words])
            chunks.append(chunk)
        
        return chunks

# ===== PYDANTIC EXAMPLE =====
from pydantic import BaseModel
from typing import List

class TextInput(BaseModel):
    """Pydantic model for input validation"""
    text: str  # Must be a string

class ChunkResponse(BaseModel):
    """Pydantic model for response"""
    total_words: int
    total_chunks: int
    chunks: List[str]

# ===== USAGE EXAMPLES =====
if __name__ == "__main__":
    print("=== REGULAR FUNCTION ===")
    result = regular_function("hello world test")
    print(f"Words: {result}")
    
    print("\n=== CLASS USAGE ===")
    # Create instance
    chunker = TextChunker(max_words=2)
    # Use method
    chunks = chunker.chunk_text("hello world this is a test")
    print(f"Chunks: {chunks}")
    
    print("\n=== PYDANTIC USAGE ===")
    # Pydantic automatically validates
    input_data = TextInput(text="hello world")
    print(f"Input text: {input_data.text}")
    print(f"Input type: {type(input_data.text)}")
    
    # Create response
    response = ChunkResponse(
        total_words=2,
        total_chunks=1,
        chunks=["hello world"]
    )
    print(f"Response: {response}")
    
    print("\n=== ERROR EXAMPLE ===")
    try:
        # This will fail validation
        bad_input = TextInput(text=123)  # Number instead of string
    except Exception as e:
        print(f"Validation error: {e}")
