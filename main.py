import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError, Field
from typing import List
from src.services.user_input_service import UserInputService
from src.services.embedding_service import EmbeddingService
from src.services.vector_store_service import VectorStoreService
from src.services.llm_service import LLMService
from src.utils.observability import observability, PerformanceTracker

app = FastAPI(title="RAG System API", version="1.0.0")

class TextInput(BaseModel):
    text: str = Field(..., min_length=10, description="Text to process and store")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    k: int = Field(3, ge=1, le=10, description="Number of results to return")

class RAGRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query for RAG pipeline")
    k: int = Field(3, ge=1, le=10, description="Number of context chunks to retrieve")
    max_length: int = Field(200, ge=50, le=500, description="Maximum response length")

class ChunkResponse(BaseModel):
    total_words: int = Field(..., description="Total number of words in input text")
    total_chunks: int = Field(..., description="Number of chunks generated")
    chunks: List[str] = Field(..., description="List of text chunks")

class EmbeddingResponse(BaseModel):
    total_chunks: int = Field(..., description="Number of chunks processed")
    embedding_dimensions: int = Field(..., description="Dimensions of each embedding vector")
    chunks_with_embeddings: List[dict] = Field(..., description="Chunks with their embedding vectors")

class RAGResponse(BaseModel):
    query: str = Field(..., description="Original user query")
    response: str = Field(..., description="Generated response from LLM")
    context_used: int = Field(..., description="Number of context chunks used")
    context_preview: str = Field(..., description="Preview of context used for generation")
    model_info: dict = Field(..., description="Information about the LLM model used")
    tokens_used: int = Field(..., description="Number of tokens in generated response")

class SearchResult(BaseModel):
    rank: int = Field(..., description="Rank of the result (1 = most similar)")
    chunk_id: int = Field(..., description="ID of the chunk in storage")
    chunk_text: str = Field(..., description="Text content of the chunk")
    similarity_score: float = Field(..., description="Similarity distance score")
    distance_type: str = Field(..., description="Type of distance metric used")
    words: int = Field(..., description="Number of words in chunk")
    characters: int = Field(..., description="Number of characters in chunk")
    lower_is_better: bool = Field(..., description="Whether lower scores indicate better similarity")

class SearchResponse(BaseModel):
    query: str = Field(..., description="Search query that was executed")
    k: int = Field(..., description="Number of results requested")
    total_found: int = Field(..., description="Total number of results found")
    results: List[SearchResult] = Field(..., description="List of search results")

class StoreResponse(BaseModel):
    chunks_added: int = Field(..., description="Number of chunks added to storage")
    total_chunks: int = Field(..., description="Total number of chunks in storage after addition")
    stats: dict = Field(..., description="Storage statistics")

# Initialize services
user_input_service = UserInputService()
embedding_service = EmbeddingService()
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

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions including JSON parsing errors."""
    if "JSON decode error" in str(exc) or "Invalid control character" in str(exc):
        return JSONResponse(
            status_code=422,
            content={
                "error": "JSON Parsing Error",
                "message": "Invalid JSON format. Make sure all special characters are properly escaped.",
                "suggestion": "Use \\n for newlines, \\t for tabs, and \\\ for quotes in JSON strings"
            }
        )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc)
        }
    )

@app.post("/store-chunks", response_model=StoreResponse)
async def store_chunks(input_data: TextInput):
    """Store text chunks in vector database."""
    try:
        print(f"\n=== API CALL: /store-chunks ===")
        print(f"Request received at: {time.strftime('%H:%M:%S')}")
        print(f"Text length: {len(input_data.text)} characters")
        print(f"Text preview: {input_data.text[:100]}...")
        
        # Step 1: Create chunks
        chunks = user_input_service.chunker.chunk_text(input_data.text)
        print(f"Generated {len(chunks)} chunks")
        
        # Step 2: Store chunks in vector database
        chunks_added = vector_store.add_chunks(chunks)
        print(f"Added {chunks_added} chunks to vector store")
        
        # Step 3: Get updated stats
        stats = vector_store.get_stats()
        
        print(f"✅ Successfully stored {chunks_added} chunks")
        print(f"Total chunks in storage: {stats['total_chunks']}")
        print("=" * 50)
        
        return StoreResponse(
            chunks_added=chunks_added,
            total_chunks=stats["total_chunks"],
            stats=stats
        )
        
    except Exception as e:
        print(f"❌ Error storing chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error storing chunks: {str(e)}")

@app.get("/store-stats")
async def get_store_stats():
    """Get vector store statistics."""
    print(f"\n=== API CALL: /store-stats ===")
    print(f"Request received at: {time.strftime('%H:%M:%S')}")
    print("Getting vector store statistics")
    
    try:
        stats = vector_store.get_stats()
        print(f"✅ Retrieved stats: {stats['total_chunks']} chunks stored")
        print("=" * 50)
        return JSONResponse(
            status_code=200,
            content=stats
        )
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/stored-chunks")
async def get_stored_chunks():
    """Get all stored chunks."""
    print(f"\n=== API CALL: /stored-chunks ===")
    print(f"Request received at: {time.strftime('%H:%M:%S')}")
    print("Retrieving all stored chunks")
    
    try:
        chunks = vector_store.get_all_chunks()
        print(f"✅ Retrieved {len(chunks)} chunks from storage")
        print("=" * 50)
        return JSONResponse(
            status_code=200,
            content={
                "chunks": chunks,
                "total": len(chunks)
            }
        )
    except Exception as e:
        print(f"❌ Error getting chunks: {str(e)}")
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
        print(f"\n=== API CALL: /process-text ===")
        print(f"Request received at: {time.strftime('%H:%M:%S')}")
        print(f"Text length: {len(input_data.text)} characters")
        print(f"Text preview: {input_data.text[:100]}...")
        
        # Process the text
        chunks = user_input_service.chunker.chunk_text(input_data.text)
        
        # Calculate statistics
        total_words = len(input_data.text.split())
        total_chunks = len(chunks)
        
        print(f"Generated {total_chunks} chunks from {total_words} words")
        print("✅ Text processing completed successfully")
        print("=" * 50)
        
        return ChunkResponse(
            total_words=total_words,
            total_chunks=total_chunks,
            chunks=chunks
        )
        
    except Exception as e:
        print(f"❌ Error in process_text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint to verify server status."""
    print(f"\n=== API CALL: /health ===")
    print(f"Request received at: {time.strftime('%H:%M:%S')}")
    print("Health check requested")
    print("Server is healthy")
    print("=" * 50)
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "message": "Server is running successfully",
            "version": "1.0.0"
        }
    )

@app.post("/rag", response_model=RAGResponse)
async def rag_query(request: RAGRequest):
    """Complete RAG pipeline: Search + LLM generation with professional observability."""
    try:
        # Extract query and parameters from request
        query = request.query
        k = request.k
        max_length = request.max_length
        
        # Validate inputs
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if k <= 0:
            raise HTTPException(status_code=400, detail="k must be positive")
        
        # Initialize performance tracker
        tracker = PerformanceTracker(f"rag_{int(time.time())}")
        
        # Step 1: Search for relevant chunks
        tracker.mark_step("search_start")
        search_results = vector_store.search_similar(query, k)
        tracker.mark_step("search_complete")
        
        if not search_results:
            raise HTTPException(status_code=404, detail="No relevant information found")
        
        # Step 2: Generate LLM response
        tracker.mark_step("llm_start")
        llm_result = llm_service.generate_response(query, search_results, max_length)
        tracker.mark_step("llm_complete")
        
        if llm_result.get("error"):
            raise HTTPException(status_code=500, detail="Error generating response")
        
        # Step 3: Calculate latencies
        total_latency = tracker.get_total_latency()
        search_time = tracker.get_step_latency("search_complete") - tracker.get_step_latency("search_start")
        llm_time = tracker.get_step_latency("llm_complete") - tracker.get_step_latency("llm_start")
        embedding_time = search_time  # Search includes query embedding
        
        # Extract distances from search results
        distances = [result.get("similarity_score", 0) for result in search_results]
        
        # Track complete RAG pipeline with enhanced observability
        observability.track_rag_pipeline(
            query=query,
            total_latency_ms=total_latency,
            embedding_time_ms=embedding_time,
            search_time_ms=search_time,
            llm_time_ms=llm_time,
            success=not llm_result.get("error", False),
            operation_id=tracker.operation_id,
            k=k,
            response_length=len(llm_result.get("response", "")),
            tokens_used=llm_result.get("tokens_used", 0),
            distances=distances
        )
        
        # Return RAG response
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
        print(f"RAG pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {str(e)}")

@app.get("/llm-stats")
async def get_llm_stats():
    """Get LLM model statistics."""
    print(f"\n=== API CALL: /llm-stats ===")
    print(f"Request received at: {time.strftime('%H:%M:%S')}")
    print("Getting LLM model statistics")
    
    try:
        stats = llm_service.get_model_stats()
        print(f"✅ Retrieved LLM stats for {stats.get('model_name', 'unknown')}")
        print("=" * 50)
        return JSONResponse(
            status_code=200,
            content=stats
        )
    except Exception as e:
        print(f"❌ Error getting LLM stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting LLM stats: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_similar_chunks(request: SearchRequest):
    """Search for similar chunks using query text."""
    try:
        # Extract query and parameters from request
        query = request.query
        k = request.k
        
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
    print(f"\n=== API CALL: /detailed-structure ===")
    print(f"Request received at: {time.strftime('%H:%M:%S')}")
    print("Getting detailed FAISS storage structure")
    
    try:
        structure = vector_store.get_detailed_structure()
        print(f"✅ Retrieved detailed structure for {structure.get('index_type', 'unknown')}")
        print("=" * 50)
        return JSONResponse(
            status_code=200,
            content=structure
        )
    except Exception as e:
        print(f"❌ Error getting structure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting structure: {str(e)}")

@app.get("/observability/metrics")
async def get_observability_metrics():
    """Get comprehensive observability metrics and performance data."""
    print(f"\n=== API CALL: /observability/metrics ===")
    print(f"Request received at: {time.strftime('%H:%M:%S')}")
    print("Getting observability metrics")
    
    try:
        metrics_summary = observability.get_metrics_summary()
        print(f"✅ Retrieved observability metrics with {len(metrics_summary)} operations tracked")
        print("=" * 50)
        return JSONResponse(
            status_code=200,
            content={
                "metrics_summary": metrics_summary,
                "system_info": {
                    "timestamp": time.time(),
                    "server_uptime": "Running since last restart",
                    "tracking_enabled": True,
                    "tracked_operations": list(observability.metrics.keys())
                }
            }
        )
    except Exception as e:
        print(f"❌ Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "message": "Welcome to RAG System API with Observability",
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
                "observability_metrics": "/observability/metrics (GET)",
                "detailed_structure": "/detailed-structure (GET)",
                "docs": "/docs"
            },
            "features": [
                "Real-time embedding generation",
                "Vector similarity search",
                "LLM-powered responses",
                "Comprehensive observability",
                "Latency tracking",
                "Anti-hallucination measures"
            ]
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    print("RAG System Server starting...")
    print("Server running on http://0.0.0.0:8000")
    print("API Documentation: http://0.0.0.0:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
