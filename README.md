# Hermon Agentic Chatbot API

FastAPI service for Hermon analytics Q&A. The API routes each request to one
safe backend flow:

- SQL analytics with read-only, tenant-scoped Postgres queries.
- Lead 360 for a single-lead context view.
- Diagnostic analytics using controlled diagnostic snapshot tools.

This repository is API-only. It intentionally does not include Streamlit,
notebooks, generated artifacts, local seed scripts, or scratchpad instructions.

## Requirements

- Python 3.12
- Postgres database access
- OpenAI API key

Install runtime dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For tests:

```bash
python -m pip install -r requirements-dev.txt
```

## Configuration

Copy `.env.example` to `.env` and set the deployment values:

```bash
OPENAI_API_KEY="..."
HERMON_DATABASE_URL="postgresql+psycopg://user:password@host:5432/database"
HERMON_DEFAULT_CLERK_ORG_ID="org_..."
LANGSMITH_TRACING="true"
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY="..."
LANGSMITH_PROJECT="hermon-prod"
```

Optional environment variables:

```bash
OPENAI_MODEL="gpt-5.4"
HERMON_SQL_MAX_ROWS="500"
HERMON_SQL_TIMEOUT_MS="10000"
HERMON_AGENT_MAX_TOOL_ROWS="20"
```

For DigitalOcean App Platform, set these as app-level environment variables on
the deployed Docker app. Mark `OPENAI_API_KEY`, `HERMON_DATABASE_URL`, and
`LANGSMITH_API_KEY` as encrypted secrets.

The `/chat` and `/chat/stream` responses include `trace_id` only when LangSmith
tracing is enabled and configured well enough to persist hosted traces.

Runtime defaults live in `app/config/config.yaml`.

## Run Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Chat request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me revenue trend",
    "user_id": "user_123",
    "org_id": "org_123",
    "timezone": "Europe/Amsterdam",
    "chat_history": []
  }'
```

Streaming chat:

```bash
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Where are we losing people in the funnel?",
    "user_id": "user_123",
    "org_id": "org_123",
    "timezone": "Europe/Amsterdam",
    "chat_history": []
  }'
```

## Test

```bash
python -m pytest
```

## Project Structure

```text
.
├── app/
│   ├── agents/
│   │   ├── diagnostic_agent/
│   │   ├── lead_360/
│   │   └── sql_agent/
│   ├── config/
│   ├── db/
│   ├── prompts/
│   │   ├── router/
│   │   │   └── 1_0_0.md
│   │   └── sql_agent/
│   │       └── 1_0_0.md
│   ├── schema/
│   ├── services/
│   ├── skills/
│   │   ├── modules/
│   │   │   ├── lead_analytics/
│   │   │   │   └── 1_0_0.md
│   │   │   ├── appointment_analytics/
│   │   │   │   └── 1_0_0.md
│   │   │   ├── acquisition_analytics/
│   │   │   │   └── 1_0_0.md
│   │   │   ├── lead_profile_analytics/
│   │   │   │   └── 1_0_0.md
│   │   │   ├── revenue_analytics/
│   │   │   │   └── 1_0_0.md
│   │   │   ├── diagnostic_analytics/
│   │   │   │   └── 1_0_0.md
│   │   │   └── lead_360/
│   │   │       └── 1_0_0.md
│   │   └── registry.yaml
│   ├── tools/
│   ├── utils/
│   ├── main.py
│   └── orchestrator.py
├── docs/
├── tests/
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

| Path | Purpose |
|---|---|
| `app/main.py` | FastAPI entrypoint and response/streaming contract. |
| `app/services/` | UI-independent chatbot execution service. |
| `app/orchestrator.py` | Router-first flow selection and downstream dispatch. |
| `app/agents/` | LangChain agent factories for SQL, Lead 360, and diagnostics. |
| `app/tools/` | Read-only SQL, Lead 360, and diagnostic tool implementations. |
| `app/db/` | Safe read-only Postgres helper and SQL validation. |
| `app/schema/` | Pydantic request/response and router schemas. |
| `app/prompts/` | Versioned agent prompt files selected from `app/config/config.yaml`. |
| `app/skills/` | Versioned SQL, Lead 360, and diagnostic instruction modules selected from `app/config/config.yaml`. |
| `docs/` | API and business metric reference documentation. |
| `tests/` | Backend contract, safety, and routing tests. |

SQL execution is centralized in `app.db.get_db()`. The validator allows only
`SELECT` or `WITH ... SELECT`, blocks dangerous keywords and sensitive columns,
requires tenant scope for business tables, and wraps results with row limits.
