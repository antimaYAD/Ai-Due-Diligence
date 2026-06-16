# AI Due Diligence Copilot — Backend

FastAPI backend with LangGraph agents, RAG pipeline, Celery workers, PostgreSQL + pgvector, and AWS S3.

## Architecture

```
backend/
├── app/
│   ├── api/          # FastAPI routers (auth, companies, documents, analysis, chat)
│   ├── ai/           # LangGraph orchestrator + RAG + 5 AI agents
│   ├── core/         # Config, database, security, dependencies
│   ├── models/       # SQLAlchemy ORM models
│   ├── schemas/      # Pydantic request/response schemas
│   ├── services/     # S3, embedding, document processor
│   ├── worker/       # Celery app + tasks
│   └── main.py       # FastAPI application entry point
├── alembic/          # Database migrations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login → JWT token |
| GET | `/api/v1/auth/me` | Current user info |
| GET | `/api/v1/companies/` | List all companies |
| POST | `/api/v1/companies/` | Create company |
| GET | `/api/v1/companies/{id}` | Get company |
| DELETE | `/api/v1/companies/{id}` | Delete company |
| POST | `/api/v1/documents/upload` | Upload PDF → S3 → Celery pipeline |
| GET | `/api/v1/documents/` | List documents (filter by company) |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| POST | `/api/v1/analysis/` | Trigger AI agent analysis |
| GET | `/api/v1/analysis/` | List analyses |
| GET | `/api/v1/analysis/{id}` | Get analysis result |
| GET | `/api/v1/analysis/reports/` | List generated reports |
| POST | `/api/v1/chat/` | RAG chat query |
| GET | `/api/v1/chat/history` | Chat history |
| GET | `/health` | Health check |

## Quick Start

### 1. Start infrastructure
```bash
docker-compose up db redis -d
```

### 2. Set up Python environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your OpenAI API key, AWS credentials, etc.
```

### 4. Run database migrations
```bash
alembic upgrade head
```

### 5. Start the API server
```bash
uvicorn app.main:application --reload --port 8000
```

### 6. Start the Celery worker
```bash
celery -A app.worker.celery_app worker --loglevel=info
```

### 7. (Optional) Celery Flower dashboard
```bash
celery -A app.worker.celery_app flower --port=5555
```

## Or run everything with Docker
```bash
docker-compose up --build
```

## Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Flower**: http://localhost:5555

## Document Processing Pipeline
1. PDF uploaded → stored in S3
2. Celery task queued via Redis
3. Worker downloads PDF → extracts text per page (pypdf)
4. Text chunked (800 tokens, 100 overlap)
5. Embeddings generated via OpenAI `text-embedding-3-small`
6. Chunks + embedding IDs stored in PostgreSQL
7. Document status updated to `processed`

## AI Agent Pipeline (LangGraph)
```
retrieve → financial ─┐
         → risk      ─┼→ thesis → report_generator
         → market    ─┘
```
- **Orchestrator**: coordinates all agents via LangGraph StateGraph
- **Financial Agent**: revenue, margins, FCF, PE analysis
- **Risk Agent**: regulatory, litigation, market, operational risk
- **Market Agent**: TAM/SAM, competitors, trends
- **Investment Thesis Agent**: Buy/Hold/Sell + conviction + price target
- **Report Generator**: full narrative executive summary
