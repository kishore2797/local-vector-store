# Local Vector Store (Chroma/FAISS) - User Story

## Project Overview
A full-stack application for **persistent vector storage, metadata filtering, and hybrid search** (vector + keyword) using ChromaDB and FAISS. Provides a visual interface for managing collections, ingesting documents, attaching rich metadata, and running advanced queries that combine semantic similarity with traditional keyword matching — the essential building block for any production RAG pipeline.

### Core Technologies
- **ChromaDB**: Persistent vector store with built-in metadata filtering and collection management
- **FAISS (Facebook AI Similarity Search)**: High-performance vector indexing for large-scale similarity search
- **Sentence-Transformers**: Embedding generation for documents and queries
- **BM25 / TF-IDF**: Keyword-based scoring for hybrid search fusion
- **Reciprocal Rank Fusion (RRF)**: Merging vector and keyword results into a single ranked list

---

## User Personas

### Primary: Arjun (AI/ML Engineer)
- **Background**: Building a production RAG pipeline that serves 50K+ documents for a legal-tech startup
- **Pain Points**: In-memory vector stores lose data on restart. No way to filter by document type, date, or source before running similarity search. Pure vector search misses exact keyword matches that users expect.
- **Goals**: Persistent storage that survives restarts, metadata-driven filtering to narrow search scope, and hybrid search that combines semantic understanding with keyword precision

### Secondary: Meera (Backend Developer)
- **Background**: Integrating vector search into an existing e-commerce product catalog API
- **Pain Points**: Pinecone is too expensive for her startup's budget. She needs a local solution she can self-host. Switching between Chroma and FAISS for benchmarking is painful — different APIs, different data formats.
- **Goals**: Unified API over multiple vector backends, easy switching between Chroma and FAISS, collection management with CRUD operations, and performance benchmarks to pick the right backend

### Tertiary: Dev (Data Scientist)
- **Background**: Experimenting with different embedding models and search strategies for a research project
- **Pain Points**: No visual tool to inspect what's actually stored in the vector DB. Can't easily compare hybrid search vs. pure vector search quality. Metadata filtering docs are confusing.
- **Goals**: Visual collection browser, query playground with adjustable parameters, side-by-side comparison of search strategies, and export results for analysis

---

## User Stories

### Epic 1: Collection Management

**US-1.1: Create Vector Collection**
> As a user, I want to create a named vector collection with a specified embedding model so that I can organize documents into logical groups.

**Acceptance Criteria:**
- Create collection via API: `POST /api/collections`
- Required fields: `name` (unique), `embedding_model` (default: `all-MiniLM-L6-v2`)
- Optional fields: `description`, `metadata_schema` (define expected metadata fields + types)
- Backend selection: `chroma` or `faiss` (default: `chroma`)
- Collection persisted to disk immediately (survives server restart)
- Duplicate name returns `409 Conflict` with clear error message
- Maximum 50 collections per instance

**US-1.2: List & Inspect Collections**
> As a user, I want to view all my collections with their stats so that I can monitor storage usage and document counts.

**Acceptance Criteria:**
- List endpoint: `GET /api/collections`
- Per-collection info: name, description, document count, embedding dimension, backend type, disk size estimate, created/updated timestamps
- Detail endpoint: `GET /api/collections/{name}` — includes metadata schema, sample documents, index stats
- Sort by: name, document count, created date, size
- Search/filter collections by name substring

**US-1.3: Update & Delete Collections**
> As a user, I want to rename, update metadata schema, or delete collections so that I can manage my storage lifecycle.

**Acceptance Criteria:**
- Update endpoint: `PATCH /api/collections/{name}` — update description, metadata schema
- Delete endpoint: `DELETE /api/collections/{name}`
- Delete requires confirmation parameter: `?confirm=true`
- Soft delete with 7-day recovery window (configurable)
- Hard delete option: `?permanent=true` — removes all data from disk
- Cannot delete a collection while an ingestion job is running

**US-1.4: Collection Backup & Restore**
> As a user, I want to export a collection to a portable format and restore it later so that I can migrate between environments or create snapshots.

**Acceptance Criteria:**
- Export endpoint: `POST /api/collections/{name}/export` → returns downloadable archive (.zip)
- Archive contains: vectors, documents, metadata, collection config
- Import endpoint: `POST /api/collections/import` — upload archive to restore
- Import validates embedding dimensions match before restoring
- Supports cross-backend restore: export from Chroma, import to FAISS (re-indexes automatically)
- Export size limit: 2GB per collection

---

### Epic 2: Document Ingestion & Embedding

**US-2.1: Ingest Documents with Metadata**
> As a user, I want to add documents with rich metadata to a collection so that I can later filter and retrieve them precisely.

**Acceptance Criteria:**
- Ingest endpoint: `POST /api/collections/{name}/documents`
- Request body:
```json
{
  "documents": [
    {
      "text": "The contract shall terminate on December 31, 2025...",
      "metadata": {
        "source": "contract_v2.pdf",
        "category": "legal",
        "date": "2024-06-15",
        "author": "Legal Team",
        "page_number": 3,
        "tags": ["termination", "contract", "deadline"]
      },
      "id": "optional-custom-id"
    }
  ]
}
```
- Auto-generates embeddings using the collection's configured model
- Auto-generates UUID if `id` not provided
- Batch support: up to 500 documents per request
- Duplicate ID detection: returns error or upserts (configurable via `?on_conflict=skip|upsert|error`)
- Metadata types supported: `string`, `int`, `float`, `bool`, `list[string]`, `datetime`
- Returns: ingested count, skipped count, error details per failed document

**US-2.2: Ingest from File Upload**
> As a user, I want to upload files (PDF, TXT, MD, DOCX) and have them automatically chunked, embedded, and stored so that I don't need a separate ingestion pipeline.

**Acceptance Criteria:**
- Upload endpoint: `POST /api/collections/{name}/upload`
- Supported formats: `.pdf`, `.txt`, `.md`, `.docx`
- Auto-chunking with configurable strategy: `fixed` (default: 1000 chars, 200 overlap), `semantic`, `recursive`
- Auto-metadata extraction: filename, format, page number, chunk index, upload timestamp
- Custom metadata attachable at upload time (applied to all chunks from that file)
- File size limit: 50MB per file, 10 files per batch
- Background processing with status polling: `GET /api/collections/{name}/jobs/{job_id}`

**US-2.3: Update & Delete Documents**
> As a user, I want to update document text/metadata or delete specific documents so that I can keep my collection accurate and current.

**Acceptance Criteria:**
- Update endpoint: `PATCH /api/collections/{name}/documents/{id}`
- Update text → re-generates embedding automatically
- Update metadata only → no re-embedding needed
- Delete single: `DELETE /api/collections/{name}/documents/{id}`
- Delete by filter: `DELETE /api/collections/{name}/documents?filter={"category": "outdated"}`
- Bulk delete by ID list: `POST /api/collections/{name}/documents/delete` with `{"ids": [...]}`
- Returns count of affected documents

**US-2.4: Browse & Inspect Documents**
> As a user, I want to browse documents stored in a collection and inspect their text, metadata, and embedding vectors so that I can verify ingestion quality.

**Acceptance Criteria:**
- List endpoint: `GET /api/collections/{name}/documents?page=1&limit=20`
- Paginated response with total count
- Filter by metadata: `?filter={"category": "legal", "date_gte": "2024-01-01"}`
- Sort by: ingestion date, metadata fields, document ID
- Document detail includes: text, metadata, embedding vector (optional, off by default), character count, token estimate
- Search within collection by document ID or metadata value

---

### Epic 3: Vector Search (Semantic)

**US-3.1: Similarity Search**
> As a user, I want to search a collection using natural language and get the most semantically similar documents so that I can find relevant content regardless of exact wording.

**Acceptance Criteria:**
- Search endpoint: `POST /api/collections/{name}/search`
- Request body:
```json
{
  "query": "What are the termination conditions?",
  "top_k": 5,
  "search_type": "vector"
}
```
- Embeds query using the collection's model
- Returns top-k results ranked by cosine similarity
- Each result includes: document ID, text, metadata, similarity score (0.0–1.0), rank
- Response time < 500ms for collections up to 100K documents
- Supports `min_score` threshold: only return results above a minimum similarity

**US-3.2: Search with Metadata Filters**
> As a user, I want to apply metadata filters before vector search so that I can narrow the search scope to relevant documents only.

**Acceptance Criteria:**
- Filter operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `nin`, `contains`
- Compound filters with `$and`, `$or`, `$not`:
```json
{
  "query": "payment terms",
  "top_k": 5,
  "search_type": "vector",
  "filters": {
    "$and": [
      {"category": {"$eq": "legal"}},
      {"date": {"$gte": "2024-01-01"}},
      {"tags": {"$contains": "payment"}}
    ]
  }
}
```
- Filters applied **before** vector search (pre-filtering) for efficiency
- Returns only documents matching ALL filter conditions
- Filter on any metadata field (no pre-registration required for Chroma; schema-based for FAISS)
- Clear error message if filter field doesn't exist in any documents

**US-3.3: Multi-Query Search**
> As a user, I want to run multiple queries simultaneously and get merged results so that I can capture different aspects of a complex information need.

**Acceptance Criteria:**
- Multi-query endpoint: `POST /api/collections/{name}/search/multi`
- Accepts array of 2–5 queries
- Each query independently embedded and searched
- Results merged using Reciprocal Rank Fusion (RRF) or configurable fusion method
- Deduplicated: same document from multiple queries appears once with combined score
- Returns: merged ranked list + per-query breakdown

---

### Epic 4: Keyword Search

**US-4.1: BM25 Keyword Search**
> As a user, I want to run traditional keyword search against document text so that I can find exact term matches that vector search might miss.

**Acceptance Criteria:**
- Search endpoint (same as vector, different `search_type`):
```json
{
  "query": "Section 12.3 termination",
  "top_k": 5,
  "search_type": "keyword"
}
```
- BM25 scoring algorithm for term relevance
- Supports: exact phrase matching (`"termination clause"`), boolean operators (`AND`, `OR`, `NOT`)
- Handles: stemming, case-insensitive matching, stop word removal
- BM25 index built and persisted alongside vector index
- Index auto-updates when documents are added/removed
- Response time < 300ms for collections up to 100K documents

**US-4.2: Full-Text Search with Highlighting**
> As a user, I want keyword matches highlighted in the returned text so that I can quickly see why a document was matched.

**Acceptance Criteria:**
- Highlight parameter: `"highlight": true`
- Returns `highlighted_text` field with matched terms wrapped in `<mark>` tags
- Snippet mode: returns only the relevant passage (±100 chars around match) instead of full text
- Multiple matches per document: returns all match positions
- Configurable highlight tag (default: `<mark>`, customizable for different frontends)

---

### Epic 5: Hybrid Search (Vector + Keyword)

**US-5.1: Hybrid Search with Configurable Fusion**
> As a user, I want to combine vector and keyword search results into a single ranked list so that I get the best of both semantic understanding and keyword precision.

**Acceptance Criteria:**
- Search endpoint:
```json
{
  "query": "Section 12.3 termination conditions",
  "top_k": 10,
  "search_type": "hybrid",
  "hybrid_config": {
    "vector_weight": 0.7,
    "keyword_weight": 0.3,
    "fusion_method": "weighted_sum"
  }
}
```
- Fusion methods:
  - **Weighted sum**: `final_score = (vector_weight × vector_score) + (keyword_weight × keyword_score)`
  - **Reciprocal Rank Fusion (RRF)**: `score = Σ 1/(k + rank)` across both result lists
  - **Relative Score Fusion**: Normalize both score distributions, then combine
- Default: `vector_weight=0.7, keyword_weight=0.3, fusion=weighted_sum`
- Results include: `vector_score`, `keyword_score`, `combined_score`, `vector_rank`, `keyword_rank`
- Metadata filters apply to both vector and keyword search
- Response time < 800ms for collections up to 100K documents

**US-5.2: Search Strategy Comparison**
> As a user, I want to run the same query across all three search types (vector, keyword, hybrid) and compare results side-by-side so that I can evaluate which strategy works best for my use case.

**Acceptance Criteria:**
- Compare endpoint: `POST /api/collections/{name}/search/compare`
- Runs vector, keyword, and hybrid search in parallel
- Returns per-strategy results with scores and ranks
- Overlap analysis: documents appearing in multiple strategies highlighted
- Unique finds: documents found by only one strategy flagged
- Metrics: Mean Reciprocal Rank (MRR), Precision@K, result overlap percentage
- Configurable hybrid weights for the comparison

**US-5.3: Auto-Tune Hybrid Weights**
> As a user, I want the system to suggest optimal hybrid weights based on my query patterns so that I don't have to manually tune parameters.

**Acceptance Criteria:**
- Endpoint: `POST /api/collections/{name}/search/auto-tune`
- User provides 5–20 sample queries with expected relevant document IDs (ground truth)
- System runs grid search over weight combinations (0.0–1.0 in 0.1 steps)
- Evaluates: Precision@5, Recall@10, MRR, NDCG
- Returns: optimal weights, performance metrics per weight combination, recommendation
- Stores tuning results for future reference
- Visual chart: performance vs. weight distribution

---

### Epic 6: Persistent Storage & Backend Management

**US-6.1: Persistent Storage Configuration**
> As a user, I want to configure where and how vector data is persisted so that I can control storage location, size, and durability.

**Acceptance Criteria:**
- Configuration via environment variables or config file:
```yaml
storage:
  base_path: "./vector_data"
  backend: "chroma"          # chroma | faiss
  chroma:
    persist_directory: "./vector_data/chroma"
    anonymized_telemetry: false
  faiss:
    index_type: "IVFFlat"    # Flat | IVFFlat | IVFPQ | HNSW
    nprobe: 10
    persist_directory: "./vector_data/faiss"
```
- Data persisted automatically after every write operation
- Graceful shutdown: flushes all pending writes before exit
- Startup: auto-loads all persisted collections
- Storage health check: `GET /api/storage/health` — reports disk usage, collection count, total vectors

**US-6.2: Switch Between Chroma & FAISS Backends**
> As a user, I want to switch between Chroma and FAISS backends without changing my application code so that I can benchmark and choose the best option.

**Acceptance Criteria:**
- Backend specified per collection at creation time
- Unified API: same endpoints work regardless of backend
- Migration tool: `POST /api/collections/{name}/migrate?target_backend=faiss`
- Migration re-indexes all vectors in the target backend
- Performance comparison endpoint: `POST /api/benchmark` — runs same queries on both backends, reports latency and recall
- Feature parity matrix documented (which features each backend supports)

**US-6.3: Index Management & Optimization**
> As a user, I want to manage and optimize vector indices so that search performance stays fast as collections grow.

**Acceptance Criteria:**
- Index stats endpoint: `GET /api/collections/{name}/index`
- Reports: index type, vector count, dimension, memory usage, estimated query latency
- Rebuild index: `POST /api/collections/{name}/index/rebuild` — useful after bulk deletes
- FAISS-specific: change index type (Flat → IVFFlat → HNSW) with automatic re-indexing
- Chroma-specific: compact/vacuum to reclaim disk space
- Auto-optimization: suggest index type based on collection size (< 10K → Flat, 10K–1M → IVFFlat, > 1M → HNSW)

---

### Epic 7: Frontend Dashboard

**US-7.1: Collection Manager UI**
> As a user, I want a visual dashboard to create, browse, and manage vector collections so that I don't need to use the API directly.

**Acceptance Criteria:**
- Dashboard home: grid/list view of all collections with stats cards
- Create collection modal: name, description, backend, embedding model selection
- Collection detail page: document count, storage size, metadata schema, recent activity
- Delete collection with confirmation dialog
- Search/filter collections by name
- Responsive layout: works on desktop and tablet

**US-7.2: Document Browser**
> As a user, I want to browse and inspect documents within a collection so that I can verify what's stored and spot data quality issues.

**Acceptance Criteria:**
- Paginated document list with metadata columns
- Configurable visible columns (choose which metadata fields to show)
- Click document to expand: full text, all metadata, embedding vector visualization (2D t-SNE/UMAP projection)
- Inline edit metadata fields
- Bulk select + delete documents
- Filter bar: filter documents by any metadata field
- Export visible documents as JSON or CSV

**US-7.3: Search Playground**
> As a user, I want an interactive search interface where I can test queries, adjust parameters, and compare search strategies visually.

**Acceptance Criteria:**
- Query input with search type selector (vector / keyword / hybrid)
- Hybrid weight sliders (vector ↔ keyword balance)
- Metadata filter builder: visual filter construction (field, operator, value)
- Results panel: ranked list with scores, highlighted text, metadata badges
- Compare mode: side-by-side results for vector vs. keyword vs. hybrid
- Query history: last 20 queries saved in browser
- Copy query as cURL or Python code snippet

**US-7.4: Analytics & Monitoring**
> As a user, I want to see storage analytics and search performance metrics so that I can monitor system health and optimize configurations.

**Acceptance Criteria:**
- Storage dashboard: total vectors, disk usage, collections breakdown (pie chart)
- Search latency chart: P50, P95, P99 over time
- Query log: recent searches with latency, result count, search type
- Embedding model usage: which models are used, vector dimensions
- Collection growth chart: document count over time
- Alert indicators: disk usage > 80%, search latency > 1s

---

## Technical Requirements

### Tech Stack

**Backend:**
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI | Async REST API with auto-generated docs |
| **Server** | Uvicorn | ASGI server |
| **Vector Store** | ChromaDB | Persistent vector storage with metadata filtering |
| **Vector Index** | FAISS | High-performance similarity search |
| **Embeddings** | sentence-transformers | Document and query embedding generation |
| **Keyword Search** | rank-bm25 | BM25 scoring for keyword retrieval |
| **Validation** | Pydantic | Request/response schema validation |
| **Config** | python-dotenv + YAML | Environment and storage configuration |

**Frontend:**
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | React 19 | Component-based UI |
| **Build Tool** | Vite | Fast dev server + production bundler |
| **Styling** | Tailwind CSS | Utility-first responsive styling |
| **Components** | shadcn/ui | Pre-built accessible UI components |
| **Charts** | Recharts | Analytics and distribution charts |
| **Icons** | Lucide React | Consistent icon set |
| **HTTP Client** | Axios | API communication |
| **State** | React Query + Zustand | Server state + client state management |

### Architecture
```
local-vector-store/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app, CORS, router registration
│   │   ├── config.py                  # Storage paths, defaults, model config
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── collections.py     # CRUD for collections
│   │   │       ├── documents.py       # Ingest, update, delete, browse documents
│   │   │       ├── search.py          # Vector, keyword, hybrid, compare endpoints
│   │   │       ├── storage.py         # Storage health, backup, restore
│   │   │       └── health.py          # Backend health check
│   │   │
│   │   ├── vector_stores/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # BaseVectorStore abstract class
│   │   │   ├── chroma_store.py        # ChromaDB implementation
│   │   │   ├── faiss_store.py         # FAISS implementation
│   │   │   └── factory.py             # Backend factory (chroma | faiss)
│   │   │
│   │   ├── search/
│   │   │   ├── __init__.py
│   │   │   ├── vector_search.py       # Embedding + cosine similarity
│   │   │   ├── keyword_search.py      # BM25 index + scoring
│   │   │   ├── hybrid_search.py       # Fusion strategies (weighted, RRF)
│   │   │   └── auto_tune.py           # Weight optimization with ground truth
│   │   │
│   │   ├── embeddings/
│   │   │   ├── __init__.py
│   │   │   ├── manager.py             # Embedding model loader + caching
│   │   │   └── models.py              # Supported model registry
│   │   │
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── chunker.py             # Text chunking strategies
│   │   │   ├── file_parser.py         # PDF, DOCX, TXT, MD parsing
│   │   │   └── metadata.py            # Metadata extraction + validation
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── collection.py          # Collection Pydantic models
│   │   │   ├── document.py            # Document Pydantic models
│   │   │   └── schemas.py             # API request/response schemas
│   │   │
│   │   └── storage/
│   │       ├── __init__.py
│   │       ├── persistence.py         # Disk persistence management
│   │       └── backup.py              # Export/import logic
│   │
│   ├── vector_data/                   # Persisted vector storage (gitignored)
│   │   ├── chroma/
│   │   └── faiss/
│   │
│   ├── requirements.txt
│   └── venv/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CollectionManager.jsx   # Collection grid/list + CRUD
│   │   │   ├── DocumentBrowser.jsx     # Paginated document table + inspector
│   │   │   ├── SearchPlayground.jsx    # Query input + results + compare mode
│   │   │   ├── FilterBuilder.jsx       # Visual metadata filter constructor
│   │   │   ├── HybridWeightSlider.jsx  # Vector ↔ keyword weight control
│   │   │   ├── ResultsPanel.jsx        # Ranked results with scores + highlights
│   │   │   ├── AnalyticsDashboard.jsx  # Storage stats + performance charts
│   │   │   ├── IngestionPanel.jsx      # File upload + text input + progress
│   │   │   └── CompareView.jsx         # Side-by-side search strategy comparison
│   │   │
│   │   ├── api/
│   │   │   └── client.js              # Axios API client
│   │   │
│   │   ├── hooks/
│   │   │   ├── useCollections.js       # React Query hooks for collections
│   │   │   ├── useSearch.js            # Search state + debouncing
│   │   │   └── useDocuments.js         # Document CRUD hooks
│   │   │
│   │   ├── store/
│   │   │   └── appStore.js            # Zustand global state
│   │   │
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── package-lock.json
│
├── assets/                             # Screenshots for README
├── config.yaml                         # Storage + model configuration
└── README.md
```

### Dependencies

**Backend (`requirements.txt`):**
```
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0
chromadb>=0.4.22
faiss-cpu>=1.7.4
sentence-transformers>=2.2.2
rank-bm25>=0.2.2
numpy>=1.24.0
PyPDF2>=3.0.0
python-docx>=1.0.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
pyyaml>=6.0.1
chardet>=5.2.0
langchain-text-splitters>=0.0.1
```

**Frontend (`package.json` key deps):**
```
react, react-dom, vite, tailwindcss, @shadcn/ui, axios, lucide-react, recharts, @tanstack/react-query, zustand
```

### Security
- File uploads validated by magic bytes (not just extension)
- Maximum file size enforced at 50MB (configurable)
- No external API calls — all embedding and search runs locally
- CORS restricted to frontend origin
- Rate limiting: 100 requests per minute per IP
- No user authentication in MVP (single-user local tool); auth as future enhancement
- Vector data directory permissions: read/write restricted to app process
- Input sanitization on all metadata values and filter expressions
- No arbitrary code execution from filter queries (parameterized, not eval'd)

---

## Non-Functional Requirements

| Aspect | Requirement |
|--------|-------------|
| **Performance** | Vector search < 500ms for collections up to 100K documents |
| **Performance** | Keyword search < 300ms for collections up to 100K documents |
| **Performance** | Hybrid search < 800ms for collections up to 100K documents |
| **Performance** | Document ingestion: 100 documents/second (batch mode) |
| **Persistence** | Zero data loss on graceful shutdown; WAL for crash recovery |
| **Storage** | Support collections up to 1M vectors (FAISS), 500K vectors (Chroma) |
| **Concurrency** | Handle 20 concurrent search requests |
| **File Size** | Support document uploads up to 50MB |
| **Startup** | Cold start with persisted data < 10s for 100K vectors |
| **Browser Support** | Chrome, Firefox, Safari, Edge (latest 2 versions) |
| **Accessibility** | Keyboard navigable, screen reader compatible labels |

---

## Future Considerations (Post-MVP)

1. **Multi-Tenant Support**: User authentication + collection-level access control
2. **GPU-Accelerated FAISS**: `faiss-gpu` for sub-millisecond search on large collections
3. **Qdrant / Weaviate Backends**: Additional vector store backends via the same unified API
4. **Embedding Model Comparison**: Ingest same documents with different models, compare retrieval quality
5. **Real-Time Sync**: WebSocket-based live updates when documents are added/removed
6. **Semantic Caching**: Cache frequent query embeddings to skip re-computation
7. **Multi-Modal Embeddings**: Support image + text embeddings (CLIP) for visual search
8. **Distributed FAISS**: Sharded indices across multiple nodes for billion-scale collections
9. **RAG Integration**: Built-in LLM answer generation using retrieved chunks (Gemini / GPT-4o-mini)
10. **REST → gRPC**: High-performance gRPC API for programmatic access from other services

---

## Definition of Done

- [ ] All acceptance criteria met and tested
- [ ] ChromaDB and FAISS backends fully implemented with unified API
- [ ] Persistent storage survives server restart with zero data loss
- [ ] Metadata filtering works with all operators ($eq, $gt, $in, $and, $or, etc.)
- [ ] Hybrid search with weighted sum and RRF fusion methods working
- [ ] BM25 keyword search with highlighting implemented
- [ ] Search strategy comparison (vector vs. keyword vs. hybrid) functional
- [ ] File upload with auto-chunking and metadata extraction working
- [ ] Frontend dashboard: collection manager, document browser, search playground
- [ ] Analytics dashboard with storage stats and search latency metrics
- [ ] Collection backup/export and restore/import functional
- [ ] API documentation auto-generated at `/docs`
- [ ] Performance benchmarks met (vector < 500ms, keyword < 300ms, hybrid < 800ms)
- [ ] Unit test coverage > 80% for vector stores, search, and ingestion
- [ ] Integration tests for full ingest → search → filter pipeline
- [ ] README with setup instructions, API examples, screenshots, and architecture diagram

---

**Estimated Effort**: 3–4 weeks (1 developer)
**MVP Target**: Week 1–2 (Chroma backend + document ingestion + vector search + metadata filtering + basic UI)
**Full Feature Set**: Week 3–4 (FAISS backend + hybrid search + auto-tune + analytics + backup/restore + comparison tools)
