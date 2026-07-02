# Ugra — AI Workforce Platform

Ugra is an intelligent platform of personal AI agents that automate professional development. The first product version is **Career Agent** — job search, vacancy analysis, resume adaptation, and interview preparation.

## Documentation

- **[AGENTS.md](AGENTS.md)** — rules for AI agents working on this repo
- **[docs/](docs/README.md)** — architecture, intelligence core, agents, API

## Repository layout

Monorepo with a symmetric `backend/src` + `frontend/src` structure:

```
ugra/
├── backend/                 # Python API, agents, Telegram bot
│   ├── src/ugra/            # Application source (Clean Architecture)
│   ├── tests/               # Backend unit tests
│   ├── prompts/             # Agent prompts (.md / .yaml)
│   └── Dockerfile
├── frontend/                # React web UI (Vite + TypeScript)
│   ├── src/
│   └── Dockerfile
├── deploy/                  # Deployment & observability configs
│   └── observability/       # Prometheus, OpenTelemetry
├── docs/                    # Technical documentation
├── scripts/                 # Dev & asset tooling
├── assets/                  # Shared static assets (character sheet)
├── docker-compose.yml       # Full stack (API, bot, web, Postgres, observability)
├── pyproject.toml             # Python package & tooling
└── AGENTS.md
```

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy, Pydantic |
| AI | LangGraph, OpenAI, Anthropic, Ollama |
| RAG | pgvector, PostgreSQL, Sentence Transformers |
| Bot | aiogram 3 |
| Web UI | React 19, Vite, Tailwind CSS |
| Infra | Docker, Docker Compose |
| Observability | OpenTelemetry, Prometheus, Grafana |

## Quick Start

```bash
cp .env.example .env
# Edit .env with your API keys

# Full stack
docker compose up -d

# Local backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
uvicorn ugra.main:app --reload

# Telegram bot
python -m ugra.presentation.telegram.bot

# Web UI (Node.js 20+)
cd frontend && npm install && npm run dev
# → http://localhost:5173
```

## API

```
GET  /api/v1/health
GET  /api/v1/ui/dashboard
POST /api/v1/ui/resumes/upload
GET  /api/v1/ui/candidate-profile
```

Full API docs: **[docs/api.md](docs/api.md)** · Swagger: `http://localhost:8000/docs`

## Tests

```bash
pytest backend/tests -q
```

## License

Private — All rights reserved.
