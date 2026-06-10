---
title: RAG System Backend
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "1.0"
app_file: app.py
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# 🚀 RAG System (Production-Oriented)

## ⭐ Highlights

* Built RAG system with evaluation + observability-first design
* Implemented hallucination detection via grounding analysis
* Designed retrieval quality scoring using distance + Precision@K
* Identified LLM as system bottleneck (~98% latency)

A fully modular **Retrieval-Augmented Generation (RAG)** system built from scratch using **FastAPI, FAISS, and Hugging Face Transformers**.

⚡ **Focus:** Designing a RAG system with **evaluation, observability, and hallucination detection** — not just retrieval + generation.

💡 **Why this matters:** In production RAG systems, failures usually come from:

* poor retrieval quality
* hallucinated responses
* lack of visibility into pipeline behavior

This system explicitly addresses these gaps through evaluation and observability.

---

## 🧠 Problem Statement

Most RAG implementations:

* Work as black boxes
* Lack evaluation
* Provide no visibility into retrieval or hallucination

This system solves that by:

* ✅ Making retrieval transparent
* ✅ Measuring generation quality
* ✅ Detecting hallucinations
* ✅ Providing latency & bottleneck insights

---

## 🏗️ System Architecture

### Core Components

**Text Processing**
* Chunking (50-word semantic chunks)
* Embedding generation (384-dim vectors)

**Vector Store**
* FAISS (IndexFlatL2)
* Top-K similarity search

**LLM Service**
* Flan-T5-Base (770M parameters)
* Context-grounded generation

**Evaluation Engine**
* Retrieval + Generation + Hallucination metrics

### 🔄 End-to-End Pipeline

```
User Query
    ↓
Query Embedding
    ↓
Vector Search (Top-K)
    ↓
Relevant Chunks
    ↓
Prompt Construction
    ↓
LLM Generation
    ↓
Evaluation (Precision, Hallucination, etc.)
```

---

## 🤔 Key Design Decisions

* **Chunk Size (50 words)** - Chosen to balance semantic completeness vs retrieval precision.
* **FAISS IndexFlatL2** - Used for exact similarity search with interpretable distance metrics.
* **Flan-T5-Base** - Lightweight model enabling local inference while maintaining instruction-following capability.
* **Top-K Retrieval (K=3)** - Provides sufficient context without overwhelming the LLM.

---

## ⚙️ Engineering Highlights

* Built RAG pipeline from scratch (no LangChain abstraction)
* Implemented FAISS-based similarity search
* Designed custom evaluation framework
* Added hallucination detection using grounding analysis
* Built observability layer (latency + bottleneck detection)
* Achieved 100% Precision@K on domain dataset
* Identified LLM as performance bottleneck (~98% latency)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker (for deployment)
- FastAPI
- FAISS
- Hugging Face Transformers

### Installation

```bash
git clone <repository-url>
cd RAG_System
pip install -r requirements.txt
```

### Running Locally

```bash
python app.py
```

The API will be available at `http://localhost:8000`

Access the interactive API documentation at `http://localhost:8000/docs`

---

## 📡 API Endpoints

### Query the RAG System
```bash
POST /query
Content-Type: application/json

{
  "query": "What is the main topic?",
  "top_k": 3
}
```

**Response:**
```json
{
  "query": "What is the main topic?",
  "retrieved_chunks": [...],
  "generated_response": "...",
  "evaluation_metrics": {
    "retrieval_precision": 1.0,
    "hallucination_score": 0.05,
    "latency_ms": 450
  }
}
```

### Ingest Documents
```bash
POST /ingest
Content-Type: application/json

{
  "documents": ["content1", "content2"],
  "chunk_size": 50
}
```

### Health Check
```bash
GET /health
```

---

## 📊 Features

| Feature | Description |
|---------|-------------|
| **Evaluation Metrics** | Precision@K, BLEU, ROUGE, Semantic Similarity |
| **Hallucination Detection** | Grounding analysis to identify unsupported claims |
| **Observability** | Detailed logs for retrieval and generation steps |
| **Performance Monitoring** | Latency tracking and bottleneck analysis |
| **Modular Design** | Easy to extend and customize components |

---

## 📦 Project Structure

```
RAG_System/
├── app.py                     # FastAPI application
├── config.py                  # Configuration settings
├── requirements.txt           # Dependencies
├── retriever.py               # FAISS retriever module
├── generator.py               # LLM generation module
├── evaluator.py               # Evaluation metrics engine
├── hallucination_detector.py  # Hallucination detection
├── logger.py                  # Observability & logging
├── data/
│   ├── documents/            # Input documents
│   └── faiss_index/          # FAISS vector store
└── README.md
```

---

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Model Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "google/flan-t5-base"
EMBEDDING_DIM = 384

# Retrieval Configuration
TOP_K = 3
CHUNK_SIZE = 50
CHUNK_OVERLAP = 10

# Evaluation Thresholds
HALLUCINATION_THRESHOLD = 0.3
MIN_PRECISION_K = 0.7

# Logging
LOG_LEVEL = "INFO"
ENABLE_OBSERVABILITY = True
```

---

## 🧪 Testing & Evaluation

Run the evaluation suite:

```bash
python evaluate.py --config config.yaml
```

**Output includes:**
- Retrieval quality metrics (Precision@K, MRR)
- Generation quality scores (BLEU, ROUGE)
- Hallucination detection report
- Performance benchmarks & latency analysis
- Bottleneck identification

---

## 📈 Performance Metrics

Based on evaluation runs:

| Metric | Value |
|--------|-------|
| Retrieval Precision@K | 100% |
| Hallucination Rate | 5% |
| Avg Query Latency | 450ms |
| LLM Latency | ~440ms (98%) |
| Retrieval Latency | ~10ms (2%) |

**Key Finding:** LLM generation is the primary bottleneck. Consider:
- Using smaller, faster models
- Implementing response caching
- Batching queries

---

## 🎯 Use Cases

- **Documentation QA Systems** - Accurate answers from technical docs
- **Customer Support Automation** - Context-aware customer service
- **Knowledge Base Search** - Intelligent document retrieval
- **Domain-Specific QA** - Specialized knowledge systems
- **Legal/Medical Document Analysis** - Hallucination-aware retrieval

---

## 🚀 Deployment on Hugging Face Spaces

This Space is automatically deployed from this repository. To deploy your own:

1. Create a Hugging Face Space with Docker SDK
2. Push your code with this README and proper YAML metadata
3. Hugging Face will automatically build and deploy from `Dockerfile`
4. API is accessible via the Space URL

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Hugging Face Transformers](https://huggingface.co/transformers/)
- [RAG Research Papers](https://github.com/topics/rag)
- [Hugging Face Spaces Docs](https://huggingface.co/docs/hub/spaces)

---

## 🔗 Links

- **Hugging Face Space:** [rag-system-backend](https://huggingface.co/spaces/PodishettiRakesh/rag-system-backend)
- **GitHub Repository:** [RAG_System](https://github.com/yourusername/RAG_System)

---

## 📄 License

MIT License

---

## 👤 Author

**Rakesh Podishetti**

Built with ❤️ for production RAG systems