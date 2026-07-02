# Ugra — AI Workforce Platform

Ugra is an intelligent platform of personal AI agents that automate professional development. The first product version is **Career Agent** — job search, vacancy analysis, resume adaptation, and interview preparation.

## Documentation

- **[AGENTS.md](AGENTS.md)** — rules for AI agents working on this repo
- **[docs/](docs/README.md)** — architecture, intelligence core, agents, API

## Architecture

```
                   Ugra
             Agent Orchestrator
                     │
        ┌────────────┼────────────┐
        │            │            │
   Career Agent  Resume Agent  Interview Agent
        │            │            │
   Cover Letter   Learning     (future agents)
```

### Design Principles

- **Clean Architecture** — domain, application, infrastructure, presentation layers
- **Plugin-based agents** — new agents register without modifying existing code
- **LangGraph** — each agent has its own graph, memory, tools, and prompts
- **MCP** — plug-and-play MCP server registry
- **RAG** — pgvector knowledge base for docs, resumes, vacancies, interview history
- **Event-Driven** — domain events for job analysis, applications, skill gaps

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy, Pydantic |
| AI | LangGraph, OpenAI, Anthropic, Ollama |
| RAG | pgvector, PostgreSQL, Sentence Transformers |
| Bot | aiogram 3 |
| Infra | Docker, Docker Compose, Kubernetes |
| Observability | OpenTelemetry, Prometheus, Grafana |

## Quick Start

```bash
# Clone and setup
cd Projects/ugra
cp .env.example .env
# Edit .env with your API keys

# Docker (recommended)
docker compose up -d

# Local development
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"

# Run API
uvicorn ugra.main:app --reload

# Run Telegram bot
python -m ugra.presentation.telegram.bot
```

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/jobs` | Search vacancies (HH.ru, HH.kz, Habr Career, GeekJob) |
| `/top` | Top matches by Match Score |
| `/resume` | Manage resume versions |
| `/interview` | Interview preparation |
| `/settings` | User preferences |
| `/stats` | Search statistics |

## API Endpoints

```
GET  /api/v1/health
GET  /api/v1/agents
GET  /api/v1/agents/state
POST /api/v1/jobs/search
POST /api/v1/message
POST /api/v1/goals
GET  /api/v1/goals/{user_id}
GET  /api/v1/reasoning/{user_id}
GET  /api/v1/memory/{user_id}
POST /api/v1/jobs/{id}/cover-letter
POST /api/v1/jobs/{id}/interview-prep
```

Full API docs: **[docs/api.md](docs/api.md)**

## Adding a New Agent

See **[docs/agents.md](docs/agents.md)** for the full guide. Summary:

1. Create `src/ugra/agents/my_agent/agent.py` extending `IntelligenceAgent`
2. Add prompt in `prompts/my_agent/v1.yaml`
3. Register in `Container._create_agent_registry()` in `core/di/container.py`
4. No changes to orchestrator or existing agents required

## Adding an MCP Server

Configure in `.env`:

```json
MCP_SERVERS=[
  {"name": "filesystem", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/data"]},
  {"name": "github", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}
]
```

## Project Structure

```
src/ugra/
├── agents/           # LangGraph agents (plugin modules)
│   ├── base/         # BaseAgent, AgentRegistry
│   ├── orchestrator/ # Routing logic
│   ├── career/       # MVP Career Agent
│   ├── resume/
│   ├── cover_letter/
│   ├── interview/
│   └── learning/
├── application/      # Use cases
├── domain/           # Entities, value objects, repository ports
├── infrastructure/   # DB, LLM, RAG, MCP, job source adapters
├── presentation/     # FastAPI routes, Telegram bot
├── core/             # DI, events, logging, observability
└── config/           # Settings
```

## Tests

```bash
pytest tests/ -v
```

## License

Private — All rights reserved.
