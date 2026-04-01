from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import List
from src.services.user_input_service import UserInputService
from src.services.embedding_service import EmbeddingService

app = FastAPI(title="RAG System API", version="1.0.0")

class TextInput(BaseModel):
    text: str

class ChunkResponse(BaseModel):
    total_words: int
    total_chunks: int
    chunks: List[str]

class EmbeddingResponse(BaseModel):
    total_chunks: int
    embedding_dimensions: int
    chunks_with_embeddings: List[dict]

# Initialize services
user_input_service = UserInputService()
embedding_service = EmbeddingService()

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors with detailed information."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "message": "Please check your request format"
        }
    )

@app.post("/generate-embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(input_data: TextInput):
    """Generate embeddings for text chunks."""
    try:
        print(f"Received text for embedding: {len(input_data.text)} characters")
        
        # Step 1: Create chunks
        chunks = user_input_service.chunker.chunk_text(input_data.text)
        total_chunks = len(chunks)
        
        print(f"Created {total_chunks} chunks")
        
        # Step 2: Generate embeddings
        embeddings = embedding_service.generate_embeddings(chunks)
        embedding_dimensions = embedding_service.get_embedding_dimensions()
        
        # Step 3: Combine chunks with embeddings
        chunks_with_embeddings = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunks_with_embeddings.append({
                "chunk_id": i + 1,
                "chunk_text": chunk,
                "embedding": embedding,
                "embedding_preview": embedding[:5]  # Show first 5 dimensions for preview
            })
        
        print(f"Generated embeddings for {total_chunks} chunks ({embedding_dimensions} dimensions each)")
        
        return EmbeddingResponse(
            total_chunks=total_chunks,
            embedding_dimensions=embedding_dimensions,
            chunks_with_embeddings=chunks_with_embeddings
        )
        
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

@app.post("/process-text", response_model=ChunkResponse)
async def process_text(input_data: TextInput):
    """Process text input and return chunks."""
    try:
        print(f"Received input: {input_data}")
        print(f"Text value: '{input_data.text}'")
        print(f"Text type: {type(input_data.text)}")
        
        # Process the text
        chunks = user_input_service.chunker.chunk_text(input_data.text)
        
        # Calculate statistics
        total_words = len(input_data.text.split())
        total_chunks = len(chunks)
        
        print(f"Processed: {total_words} words, {total_chunks} chunks")
        
        return ChunkResponse(
            total_words=total_words,
            total_chunks=total_chunks,
            chunks=chunks
        )
        
    except Exception as e:
        print(f"Error in process_text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify server status."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "message": "Server is running successfully",
            "version": "1.0.0"
        }
    )

@app.get("/")
async def root():
    """Root endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "message": "Welcome to RAG System API",
            "endpoints": {
                "health": "/health",
                "process_text": "/process-text (POST)",
                "generate_embeddings": "/generate-embeddings (POST)",
                "docs": "/docs"
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    print("RAG System Server starting...")
    print("Server running on http://0.0.0.0:8000")
    print("API Documentation: http://0.0.0.0:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
