# REST API

Base URL: `/api/v1`

## Health

```
GET /health
→ {"status": "ok", "version": "0.1.0"}
```

## Agents

```
GET /agents
→ [{"name": "career_agent", "capabilities": ["job_search", ...]}]

GET /agents/state
→ {"active_agent": "career_agent", "agents": {"career_agent": "idle", ...}}
```

## Messages

```
POST /message
Body: {"user_id": "uuid", "message": "find jobs", "metadata": {"is_owner": true}}
→ {"agent": "career_agent", "content": "...", "data": {...}}
```

## Jobs

```
POST /jobs/search
Body: filters + skills + experience_years

POST /jobs/{job_id}/cover-letter
POST /jobs/{job_id}/interview-prep
```

## Goals

```
POST /goals
Body: {"user_id": "uuid", "title": "Get AI Engineer job", "goal_type": "find_job"}

GET /goals/{user_id}
→ [{"id": "...", "title": "...", "status": "active", "progress": 0.0}]
```

## Intelligence

```
GET /reasoning/{user_id}?limit=20
→ [{"agent": "career_agent", "category": "vacancy_selection", "decision": "skip", "rationale": "..."}]

GET /memory/{user_id}
→ {"vacancies": 5, "interviews": 1, "ignored_companies": ["BadCorp"], ...}
```

## Metadata для Personality

В `POST /message` metadata:

```json
{
  "channel": "owner",
  "is_owner": true,
  "skills": ["python", "rag"],
  "experience_years": 5,
  "filters": {"remote_only": true}
}
```

| channel | Режим |
|---------|-------|
| `owner` | Hunter |
| `email`, `hr`, `linkedin`, `hh` | Professional |
