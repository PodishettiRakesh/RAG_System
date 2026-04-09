from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import List
from src.services.user_input_service import UserInputService
from src.services.simple_embedding_service import SimpleEmbeddingService
from src.services.vector_store_service import VectorStoreService
from src.services.llm_service import LLMService

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

class RAGResponse(BaseModel):
    query: str
    response: str
    context_used: int
    context_preview: str
    model_info: dict
    tokens_used: int

class SearchResponse(BaseModel):
    query: str
    k: int
    total_found: int
    results: List[dict]

class StoreResponse(BaseModel):
    chunks_added: int
    total_chunks: int
    stats: dict

# Initialize services
user_input_service = UserInputService()
embedding_service = SimpleEmbeddingService()
vector_store = VectorStoreService()
llm_service = LLMService()

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

@app.post("/store-chunks", response_model=StoreResponse)
async def store_chunks(input_data: TextInput):
    """Store text chunks in vector database."""
    try:
        print(f"Storing chunks for text: {len(input_data.text)} characters")
        
        # Step 1: Create chunks
        chunks = user_input_service.chunker.chunk_text(input_data.text)
        
        # Step 2: Store chunks in vector database
        chunks_added = vector_store.add_chunks(chunks)
        
        # Step 3: Get updated stats
        stats = vector_store.get_stats()
        
        print(f"Stored {chunks_added} chunks successfully")
        
        return StoreResponse(
            chunks_added=chunks_added,
            total_chunks=stats["total_chunks"],
            stats=stats
        )
        
    except Exception as e:
        print(f"Error storing chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing chunks: {str(e)}")

@app.get("/store-stats")
async def get_store_stats():
    """Get vector store statistics."""
    try:
        stats = vector_store.get_stats()
        return JSONResponse(
            status_code=200,
            content=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/stored-chunks")
async def get_stored_chunks():
    """Get all stored chunks."""
    try:
        chunks = vector_store.get_all_chunks()
        return JSONResponse(
            status_code=200,
            content={
                "chunks": chunks,
                "total": len(chunks)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chunks: {str(e)}")
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

@app.post("/rag", response_model=RAGResponse)
async def rag_query(query_data: dict):
    """Complete RAG pipeline: Search + LLM generation."""
    try:
        # Extract query and k from request
        query = query_data.get("query", "")
        k = query_data.get("k", 3)
        max_length = query_data.get("max_length", 200)
        
        print(f"🚀 RAG Query: '{query[:50]}...', k={k}")
        
        # Validate inputs
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if k <= 0:
            raise HTTPException(status_code=400, detail="k must be positive")
        
        # Step 1: Search for relevant chunks
        print("🔍 Step 1: Searching for relevant chunks...")
        search_results = vector_store.search_similar(query, k)
        
        if not search_results:
            raise HTTPException(status_code=404, detail="No relevant information found")
        
        print(f"📚 Found {len(search_results)} relevant chunks")
        
        # Step 2: Generate LLM response
        print("🤖 Step 2: Generating LLM response...")
        llm_result = llm_service.generate_response(query, search_results, max_length)
        
        if llm_result.get("error"):
            raise HTTPException(status_code=500, detail="Error generating response")
        
        # Step 3: Return RAG response
        print("✅ RAG pipeline completed successfully!")
        
        return RAGResponse(
            query=llm_result["query"],
            response=llm_result["response"],
            context_used=llm_result["context_used"],
            context_preview=llm_result["context_preview"],
            model_info=llm_result["model_info"],
            tokens_used=llm_result["tokens_used"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ RAG pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {str(e)}")

@app.get("/llm-stats")
async def get_llm_stats():
    """Get LLM model statistics."""
    try:
        stats = llm_service.get_model_stats()
        return JSONResponse(
            status_code=200,
            content=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting LLM stats: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_similar_chunks(query_data: dict):
    """Search for similar chunks using query text."""
    try:
        # Extract query and k from request
        query = query_data.get("query", "")
        k = query_data.get("k", 3)
        
        print(f"Search request: query='{query[:50]}...', k={k}")
        
        # Validate inputs
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if k <= 0:
            raise HTTPException(status_code=400, detail="k must be positive")
        
        # Search for similar chunks
        results = vector_store.search_similar(query, k)
        
        print(f"Search completed: found {len(results)} results")
        
        return SearchResponse(
            query=query,
            k=k,
            total_found=len(results),
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error searching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching: {str(e)}")

@app.get("/detailed-structure")
async def get_detailed_structure():
    """Get detailed FAISS storage structure."""
    try:
        structure = vector_store.get_detailed_structure()
        return JSONResponse(
            status_code=200,
            content=structure
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting structure: {str(e)}")

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
                "store_chunks": "/store-chunks (POST)",
                "store_stats": "/store-stats (GET)",
                "stored_chunks": "/stored-chunks (GET)",
                "search": "/search (POST)",
                "rag": "/rag (POST)",
                "llm_stats": "/llm-stats (GET)",
                "detailed_structure": "/detailed-structure (GET)",
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
