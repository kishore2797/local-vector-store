# 🗄️ Local Vector Store

> **Persistent vector storage with metadata filtering and hybrid search — powered by ChromaDB & FAISS**

A full-stack application for managing vector collections, ingesting documents, and running advanced search queries that combine **semantic similarity** with **keyword precision**. The essential building block for any production RAG pipeline.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4+-FF6F00?style=flat-square)
![FAISS](https://img.shields.io/badge/FAISS-1.7+-blue?style=flat-square)
![TailwindCSS](https://img.shields.io/badge/Tailwind-4.0-38B2AC?style=flat-square&logo=tailwindcss&logoColor=white)

Part of the [Mastering RAG](https://github.com/kishore2797/mastering-rag) ecosystem → tutorial: [rag-04-vector-stores](https://github.com/kishore2797/rag-04-vector-stores).

---

## 🌍 Real-World Scenario

> You've embedded 50,000 customer support articles. A user asks "refund policy for international orders placed before January." **Pure vector search** finds refund articles but also domestic and general policy. **With metadata filtering** (e.g. category=international, date&lt;January) and **hybrid search** (keyword "refund" + semantic similarity), you narrow to the 3 articles that matter. That's the power of a well-configured vector store.

---

## 🏗️ What You'll Build

A full-stack vector store app with **ChromaDB and FAISS**: create collections, ingest documents, run **semantic**, **keyword**, and **hybrid search** with metadata filtering. The building block for any production RAG pipeline.

---

## 🔑 Key Concepts

- **ANN search** — Approximate nearest neighbor for fast similarity search
- **Distance metrics** — Cosine similarity, L2, dot product
- **Metadata filtering** — Narrow search by date, category, tags before vector comparison
- **Hybrid search** — Combine vector similarity with keyword matching (BM25)
- **Persistence** — Save and reload vector indexes across restarts

---

## ✨ Features

### 🔍 Three Search Modes
- **Vector Search** — Semantic similarity using sentence-transformers embeddings
- **Keyword Search** — BM25-based term matching with highlighting
- **Hybrid Search** — Combines both with configurable fusion (Weighted Sum, RRF, Relative Score)

### 🗃️ Dual Backend Support
- **ChromaDB** — Built-in metadata filtering, persistent storage, cosine similarity
- **FAISS** — High-performance vector indexing (Flat, IVFFlat, HNSW)
- Unified API — Same endpoints work regardless of backend

### 📄 Document Ingestion
- **File Upload** — PDF, DOCX, TXT, Markdown with auto-chunking
- **Text API** — Direct document ingestion with rich metadata
- **Batch Support** — Up to 500 documents per request
- **Auto-Embedding** — Documents embedded on ingestion using sentence-transformers

### 🏷️ Metadata Filtering
- Filter operators: `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`, `$contains`
- Compound filters: `$and`, `$or`, `$not`
- Pre-filtering before vector search for efficiency

### 💾 Persistent Storage
- Data survives server restarts — zero data loss
- Configurable storage paths via YAML config
- Collection backup & restore

### 📊 Visual Dashboard
- Collection manager with CRUD operations
- Document browser with pagination & metadata inspection
- Interactive search playground with side-by-side comparison
- Storage analytics & system health monitoring

---

## 🏗️ Architecture

```
local-vector-store/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # REST API endpoints
│   │   │   ├── collections.py   # Collection CRUD
│   │   │   ├── documents.py     # Document ingestion & management
│   │   │   ├── search.py        # Vector, keyword, hybrid search
│   │   │   ├── storage.py       # Storage health & persistence
│   │   │   └── health.py        # System health check
│   │   ├── vector_stores/       # Backend implementations
│   │   │   ├── base.py          # Abstract base class
│   │   │   ├── chroma_store.py  # ChromaDB implementation
│   │   │   ├── faiss_store.py   # FAISS implementation
│   │   │   └── factory.py       # Store manager & factory
│   │   ├── search/              # Search engines
│   │   │   ├── vector_search.py # Embedding + cosine similarity
│   │   │   ├── keyword_search.py# BM25 scoring
│   │   │   └── hybrid_search.py # Fusion strategies
│   │   ├── embeddings/          # Embedding model management
│   │   ├── ingestion/           # File parsing & chunking
│   │   ├── models/              # Pydantic schemas
│   │   ├── config.py            # App configuration
│   │   └── main.py              # FastAPI entry point
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CollectionManager.jsx
│   │   │   ├── DocumentBrowser.jsx
│   │   │   ├── SearchPlayground.jsx
│   │   │   └── AnalyticsDashboard.jsx
│   │   ├── api/client.js        # Axios API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── config.yaml                  # Storage & model configuration
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **npm** or **yarn**

### 1️⃣ Clone & Setup Backend

```bash
cd local-vector-store/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at **http://localhost:8000** with docs at **http://localhost:8000/docs**

### 3️⃣ Setup & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at **http://localhost:5173**

---

## 📡 API Reference

### Collections

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/collections` | Create a new collection |
| `GET` | `/api/collections` | List all collections |
| `GET` | `/api/collections/{name}` | Get collection details |
| `PATCH` | `/api/collections/{name}` | Update collection |
| `DELETE` | `/api/collections/{name}?confirm=true` | Delete collection |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/collections/{name}/documents` | Ingest documents with metadata |
| `POST` | `/api/collections/{name}/upload` | Upload & auto-chunk a file |
| `GET` | `/api/collections/{name}/documents` | Browse documents (paginated) |
| `GET` | `/api/collections/{name}/documents/{id}` | Get single document |
| `PATCH` | `/api/collections/{name}/documents/{id}` | Update document |
| `DELETE` | `/api/collections/{name}/documents/{id}` | Delete document |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/collections/{name}/search` | Vector, keyword, or hybrid search |
| `POST` | `/api/collections/{name}/search/compare` | Compare all three search types |
| `POST` | `/api/collections/{name}/search/multi` | Multi-query with RRF fusion |

### Storage & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | System health check |
| `GET` | `/api/storage/health` | Storage stats & disk usage |
| `POST` | `/api/storage/persist` | Force persist all data |

---

## 🔧 Usage Examples

### Create a Collection

```bash
curl -X POST http://localhost:8000/api/collections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "legal-docs",
    "description": "Legal contract documents",
    "backend": "chroma",
    "embedding_model": "all-MiniLM-L6-v2"
  }'
```

### Ingest Documents

```bash
curl -X POST http://localhost:8000/api/collections/legal-docs/documents \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "text": "The contract shall terminate on December 31, 2025...",
        "metadata": {
          "source": "contract_v2.pdf",
          "category": "legal",
          "date": "2024-06-15"
        }
      }
    ],
    "on_conflict": "error"
  }'
```

### Upload a File

```bash
curl -X POST http://localhost:8000/api/collections/legal-docs/upload \
  -F "file=@contract.pdf" \
  -F "chunk_strategy=recursive" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200"
```

### Hybrid Search with Metadata Filters

```bash
curl -X POST http://localhost:8000/api/collections/legal-docs/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "termination conditions",
    "top_k": 5,
    "search_type": "hybrid",
    "highlight": true,
    "filters": {
      "category": {"$eq": "legal"}
    },
    "hybrid_config": {
      "vector_weight": 0.7,
      "keyword_weight": 0.3,
      "fusion_method": "rrf"
    }
  }'
```

### Compare Search Strategies

```bash
curl -X POST http://localhost:8000/api/collections/legal-docs/search/compare \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Section 12.3 termination",
    "top_k": 5
  }'
```

---

## ⚙️ Configuration

Edit `config.yaml` in the project root:

```yaml
storage:
  base_path: "./vector_data"
  default_backend: "chroma"       # chroma | faiss
  chroma:
    persist_directory: "./vector_data/chroma"
  faiss:
    index_type: "Flat"            # Flat | IVFFlat | HNSW
    persist_directory: "./vector_data/faiss"

embedding:
  default_model: "all-MiniLM-L6-v2"
  device: "cpu"                   # cpu | cuda

chunking:
  default_strategy: "recursive"   # fixed | semantic | recursive
  default_chunk_size: 1000
  default_chunk_overlap: 200

api:
  port: 8000
  max_upload_size_mb: 50
  max_batch_size: 500
  max_collections: 50
```

---

## 🧠 Embedding Models

| Model | Dimensions | Speed | Quality | Best For |
|-------|-----------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | ⚡ Fast | ⭐⭐⭐ | General purpose (default) |
| `all-MiniLM-L12-v2` | 384 | 🔄 Medium | ⭐⭐⭐⭐ | Better quality |
| `all-mpnet-base-v2` | 768 | 🐢 Slower | ⭐⭐⭐⭐⭐ | Best quality |

---

## 🔀 Hybrid Search Fusion Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **Weighted Sum** | `score = w₁·vector + w₂·keyword` | Simple, tunable balance |
| **RRF** | Reciprocal Rank Fusion across result lists | Robust, no score normalization needed |
| **Relative Score** | Normalize distributions, then combine | When score scales differ significantly |

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — Async REST API with auto-generated OpenAPI docs
- **ChromaDB** — Persistent vector store with metadata filtering
- **FAISS** — High-performance similarity search (Facebook AI)
- **Sentence-Transformers** — Local embedding generation
- **rank-bm25** — BM25 keyword scoring
- **LangChain Text Splitters** — Document chunking strategies
- **PyPDF2 / python-docx** — File parsing

### Frontend
- **React 19** — Component-based UI
- **Vite** — Fast dev server & bundler
- **Tailwind CSS 4** — Utility-first styling
- **Recharts** — Analytics charts
- **Lucide React** — Icon set
- **Axios** — HTTP client

---

## 📋 Supported File Formats

| Format | Parser | Features |
|--------|--------|----------|
| 📄 **PDF** | PyPDF2 | Page-level extraction, metadata |
| 📝 **DOCX** | python-docx | Paragraph styles, metadata |
| 📃 **TXT** | Built-in | Auto encoding detection |
| 📑 **Markdown** | Built-in | Frontmatter extraction |

---

## 🗺️ Roadmap

- [ ] GPU-accelerated FAISS (`faiss-gpu`)
- [ ] Additional backends (Qdrant, Weaviate)
- [ ] Embedding model comparison tool
- [ ] Auto-tune hybrid weights with ground truth
- [ ] Collection backup/export to ZIP
- [ ] Multi-modal embeddings (CLIP)
- [ ] WebSocket live updates
- [ ] Semantic caching for frequent queries
- [ ] RAG integration (LLM answer generation)
- [ ] gRPC API for high-performance access

---

## 📄 License

MIT

---

**Built with ❤️ for the RAG community**
