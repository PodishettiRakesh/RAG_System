from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="RAG System API", version="1.0.0")

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
            "message": "Welcome to RAG System API"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
