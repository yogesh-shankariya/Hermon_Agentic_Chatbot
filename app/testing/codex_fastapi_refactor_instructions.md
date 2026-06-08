# Codex Instructions: Refactor Streamlit Chatbot to FastAPI Local Service

## Objective

Refactor the current Hermon chatbot so it can run without Streamlit and expose it through a local FastAPI `/chat` endpoint.

This task covers only the first three implementation steps:

1. Make the chatbot run from a plain Python function without Streamlit.
2. Create a FastAPI `/chat` endpoint.
3. Test locally using curl/Postman.

Do not implement Docker in this task yet. Docker will be handled after the FastAPI service works locally.

---

## Current Context

The chatbot is currently working through Streamlit. The business now wants to use the chatbot inside the Hermon portal.

The final expected flow is:

```text
Hermon Portal / Node backend
        |
        | HTTP request
        v
FastAPI chatbot service
        |
        | Existing Python chatbot logic
        v
LLM / tools / Supabase / analytics skills
```

The Python chatbot logic should remain in Python. Node should only call the FastAPI service through HTTP.

---

## Important Scope

### In scope

- Remove direct Streamlit dependency from the core chatbot execution path.
- Create a reusable Python function that can be called from:
  - FastAPI now
  - Streamlit later if still needed for internal testing
  - CLI/local script if needed
- Add a FastAPI app with a `/chat` endpoint.
- Add request and response schemas.
- Add simple local test commands.
- Keep existing chatbot behavior as much as possible.

### Out of scope

- Dockerfile
- docker-compose
- production deployment
- CI/CD
- authentication between Node and FastAPI
- frontend changes in Hermon portal
- streaming endpoint
- WebSocket/SSE
- major architecture rewrite
- prompt rewriting unless required to remove Streamlit dependency

---

## Required Implementation Approach

### Step 1: Separate chatbot logic from Streamlit

Find the current Streamlit entrypoint and identify the code that:

- reads user input from Streamlit
- displays messages in Streamlit
- stores Streamlit session state
- calls the chatbot / agent / router logic
- streams intermediate thinking or final response to the UI

Refactor so the actual chatbot execution is available as a plain Python callable.

Create or update a service file similar to:

```text
app/services/chatbot_service.py
```

The service should expose a function like:

```python
def run_chatbot(request: ChatRequest) -> ChatResponse:
    ...
```

or an async version if the current agent/tool flow is already async:

```python
async def run_chatbot(request: ChatRequest) -> ChatResponse:
    ...
```

The function must not import or call Streamlit.

Avoid these inside the core service:

```python
import streamlit as st
st.write(...)
st.session_state
st.chat_message(...)
st.chat_input(...)
st.spinner(...)
st.status(...)
st.stream(...)
```

If chat history is currently stored in `st.session_state`, replace it with explicit input fields such as:

```python
session_id
question
chat_history
org_id
timezone
user_context
```

Do not depend on UI state inside the core chatbot function.

---

## Proposed Request Schema

Create a Pydantic request model similar to this:

```python
class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None
    org_id: str | None = None
    user_id: str | None = None
    timezone: str | None = "Europe/Amsterdam"
    chat_history: list[dict] | None = None
```

Notes:

- `question` is required.
- `session_id` is optional for now but should be accepted.
- `org_id` should be accepted because the chatbot needs tenant/organization context.
- Default timezone should be `Europe/Amsterdam` for Hermon business reporting unless the existing app already handles timezone differently.
- `chat_history` should be optional. If not provided, run as a fresh question.

Do not hardcode the live organization ID in the service.

---

## Proposed Response Schema

Create a Pydantic response model similar to this:

```python
class ChatResponse(BaseModel):
    answer: str
    route: str | None = None
    session_id: str | None = None
    success: bool = True
    error: str | None = None
    metadata: dict | None = None
```

The response must be safe for Node to consume.

Do not return raw secrets, database URLs, API keys, raw payloads, or internal credentials.

If the chatbot already produces SQL/tool metadata, include only safe metadata. Do not expose sensitive details by default.

---

## Step 2: Add FastAPI endpoint

Create or update:

```text
app/main.py
```

Add a FastAPI app with at least these endpoints:

```text
GET /health
POST /chat
```

### `GET /health`

Expected response:

```json
{
  "status": "ok"
}
```

### `POST /chat`

Expected request:

```json
{
  "question": "Show me revenue trend",
  "session_id": "test-session-001",
  "org_id": "org_xxx",
  "timezone": "Europe/Amsterdam",
  "chat_history": []
}
```

Expected response:

```json
{
  "answer": "The revenue trend is...",
  "route": "sql_analytics",
  "session_id": "test-session-001",
  "success": true,
  "error": null,
  "metadata": {}
}
```

The endpoint should call only the plain chatbot service function.

FastAPI should not contain the full chatbot logic directly. Keep FastAPI thin.

Preferred structure:

```text
app/
  main.py
  schemas/
    chat.py
  services/
    chatbot_service.py
  core/
    config.py
```

If the existing repo has a different structure, follow the repo style but keep the same separation.

---

## Error Handling

Add basic error handling around the chatbot execution.

If the chatbot fails, return a controlled response or raise a proper HTTP exception.

Preferred behavior for now:

```json
{
  "answer": "",
  "route": null,
  "session_id": "test-session-001",
  "success": false,
  "error": "Safe error message",
  "metadata": {}
}
```

Do not expose stack traces to the API response.

Stack traces can be logged locally.

---

## Environment Variables

Move all secrets/configuration to environment variables if they are not already there.

Expected variables may include:

```text
OPENAI_API_KEY
DATABASE_URL
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
HORIZON_API_KEY
HORIZON_BASE_URL
DEFAULT_TIMEZONE
ENVIRONMENT
```

Only add variables that are actually used in the existing project.

Create or update `.env.example` with dummy values only.

Do not commit real secrets.

---

## Local Run Command

Add or confirm these dependencies in `requirements.txt` or `pyproject.toml`:

```text
fastapi
uvicorn
pydantic
python-dotenv
```

Then the app should run locally with:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If the app path is different, update the command in the README or notes.

---

## Local Test Commands

### Health check

```bash
curl http://localhost:8000/health
```

Expected:

```json
{
  "status": "ok"
}
```

### Chat test

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me revenue trend",
    "session_id": "local-test-session-001",
    "org_id": "org_xxx",
    "timezone": "Europe/Amsterdam",
    "chat_history": []
  }'
```

Expected:

```json
{
  "answer": "...",
  "route": "...",
  "session_id": "local-test-session-001",
  "success": true,
  "error": null,
  "metadata": {}
}
```

---

## Postman Test

Create a Postman request:

```text
Method: POST
URL: http://localhost:8000/chat
Headers:
  Content-Type: application/json
Body:
  raw JSON
```

Body:

```json
{
  "question": "How many leads came last month?",
  "session_id": "postman-test-001",
  "org_id": "org_xxx",
  "timezone": "Europe/Amsterdam",
  "chat_history": []
}
```

The response should return a valid chatbot answer without using Streamlit.

---

## Acceptance Criteria

The task is complete only when all of the following are true:

- The chatbot can answer a question through a plain Python function without Streamlit.
- The core chatbot service does not import Streamlit.
- FastAPI starts locally using uvicorn.
- `GET /health` returns status ok.
- `POST /chat` accepts JSON input and returns JSON output.
- The `/chat` endpoint works from curl or Postman.
- Existing Streamlit UI is not required for chatbot execution.
- Existing Streamlit UI is not broken unnecessarily. If Streamlit is still needed, it should call the same service function.
- Secrets are not hardcoded.
- Real organization IDs are not hardcoded in code.
- Errors are returned safely without exposing stack traces to the API response.

---

## Recommended Implementation Order For Codex

1. Inspect the current Streamlit file and identify the smallest reusable chatbot execution block.
2. Move that execution block into a service function.
3. Replace Streamlit-specific inputs with explicit function arguments.
4. Replace Streamlit-specific outputs with returned values.
5. Add Pydantic request/response models.
6. Add FastAPI `main.py`.
7. Add `/health`.
8. Add `/chat`.
9. Add local uvicorn run instruction.
10. Test with curl.
11. Only after this works, prepare for Docker in a separate task.

---

## Important Notes

Do not over-engineer this task.

The goal is not to redesign the chatbot. The goal is to make the current chatbot callable through FastAPI.

Keep changes minimal and focused.

Do not add Docker yet.

Do not add streaming yet.

Do not change prompts, routing logic, SQL logic, or analytics definitions unless they are directly blocking the Streamlit-to-FastAPI refactor.
