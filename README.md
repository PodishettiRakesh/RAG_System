# RAG System

A FastAPI-based system with health check endpoint.

## Quick Start

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
# Normal mode
python main.py

# Debug mode (use VS Code debugger)
# Press F5 or go to Run and Debug panel
```

5. Check health endpoint:
```bash
curl http://localhost:8000/health
```

## API Endpoints

- `GET /health` - Health check endpoint

## Development

- Use VS Code debugger with F5 to run in debug mode
- Launch configuration is available in `.vscode/launch.json`
