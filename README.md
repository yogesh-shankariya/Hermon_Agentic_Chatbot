# Hermon Agentic Chatbot

Streamlit-first text-to-SQL chatbot for Hermon analytics.

## Hermon Q&A Agent Prototype

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Required `.env` values:

```bash
OPENAI_API_KEY="..."
HERMON_DATABASE_URL="postgresql+psycopg://..."
HERMON_DEFAULT_CLERK_ORG_ID="..."
```

Optional `.env` value:

```bash
OPENAI_MODEL="gpt-5.4"
```

Run the Streamlit chat UI:

```bash
streamlit run app/ui/streamlit_app.py
```

## Project Structure

| Path | Purpose |
|---|---|
| `app/agents/sql_agent/` | Generic LangChain SQL agent factory and middleware. |
| `app/tools/` | Agent tool implementations, including SQL validation and execution tools. |
| `app/config/config.yaml` | Model, prompt version, database, and Streamlit runtime config. |
| `app/prompts/sql_agent/` | Versioned YAML prompt for SQL generation behavior. |
| `app/skills/` | Skill registry and Markdown skill instructions loaded by the agent. |
| `app/db/` | Read-only Postgres helper and SQL safety validation. |
| `app/ui/` | Streamlit application. |
| `app/docs/` | SQL/test reference documentation. |
| `notebooks/` | Jupyter notebooks only. |

Cross-check expected SQL and tabular outputs:

```text
app/docs/lead_analytics_expected_sql.md
```

The default SQL agent config enables every skill listed in
`app/skills/registry.yaml`. SQL is executed through `app.db.get_db()`, which
validates read-only SQL and runs it in a read-only transaction.
