# AlTi RAG Service

RAG-powered investment research service for AlTi wealth management. Provides natural language Q&A over portfolios, capital market assumptions, fund holdings, and research documents.

## Architecture

```
alti-portfolio-react/          # React Frontend (Next.js 16)
    └── /investment-search     # RAG-powered search UI
    └── /api/rag/query         # Proxy to Python backend

alti-rag-service/              # Python Backend (FastAPI)
    ├── main.py                # FastAPI entry point
    ├── ingestion/             # Document processing
    ├── retrieval/             # Query engine
    └── chroma_db/             # Vector store (persistent)
```

## Quick Start

### 1. Setup Python Environment

```bash
cd alti-rag-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Start the Service

```bash
# Development mode (with auto-reload)
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --port 8000
```

### 4. Ingest Legacy Data

```bash
# Via API (after service is running)
curl -X POST http://localhost:8000/api/v1/ingest/legacy

# Or via Python script
python -c "
from ingestion import IngestionPipeline
pipeline = IngestionPipeline()
result = pipeline.ingest_directory('../alti-risk-portfolio-app/data')
print(result)
"
```

### 5. Start React Frontend

```bash
cd ../alti-portfolio-react
npm run dev
# Open http://localhost:3000/investment-search
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check and collection stats |
| `/api/v1/query` | POST | RAG query with LLM synthesis |
| `/api/v1/search` | POST | Semantic search (no LLM) |
| `/api/v1/ingest/directory` | POST | Ingest documents from directory |
| `/api/v1/ingest/file` | POST | Ingest single file |
| `/api/v1/ingest/legacy` | POST | Ingest from legacy Dash app |
| `/api/v1/stats` | GET | Detailed collection stats |
| `/api/v1/collection` | DELETE | Clear all documents |

## Query Examples

```bash
# Natural language query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the expected returns for equities?"}'

# Semantic search
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "portfolio allocations", "top_k": 10}'
```

## Supported Document Types

| Extension | Loader | Use Case |
|-----------|--------|----------|
| `.csv` | Custom | Portfolio holdings, returns, fund holdings |
| `.xlsx` | Custom | CMA assumptions, multi-sheet data |
| `.pdf` | PyMuPDF | Research reports, client documents |
| `.json` | Custom | Qualtrics survey responses |

## Document Metadata

Each document chunk includes:
- `file_name`: Source file
- `document_type`: Category (portfolio_summary, cma_assumptions, etc.)
- `source`: Full file path
- Additional type-specific metadata

## Configuration

See `.env.example` for all configuration options:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `EMBEDDING_MODEL` | text-embedding-3-small | Embedding model |
| `LLM_MODEL` | gpt-4o-mini | Response generation model |
| `CHUNK_SIZE` | 512 | Text chunk size |
| `CHUNK_OVERLAP` | 128 | Overlap between chunks |
| `SIMILARITY_TOP_K` | 5 | Default retrieval count |

## Development

```bash
# Run tests
pytest

# Format code
black .
isort .

# Type check
mypy .
```

## Troubleshooting

### "RAG service unavailable"
- Ensure Python backend is running on port 8000
- Check that OPENAI_API_KEY is set in .env

### Empty search results
- Run ingestion first: `POST /api/v1/ingest/legacy`
- Check collection count: `GET /api/v1/health`

### Slow queries
- Reduce `top_k` parameter
- Use `search` endpoint instead of `query` for raw results
