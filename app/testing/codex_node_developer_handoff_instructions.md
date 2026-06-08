# Codex Instructions: Create Node Developer Handoff for DigitalOcean + Docker + FastAPI Chatbot Integration

## Goal

Create a clear Markdown handoff document for the Node.js developer explaining how the existing Python/FastAPI chatbot backend should be hosted on DigitalOcean using Docker and how the Node.js application should integrate with it.

The handoff document should be practical, implementation-focused, and written for a Node.js developer who will call the FastAPI chatbot service from the client web application or Node backend.

Create a new file in the repo named:

```text
NODE_FASTAPI_DIGITALOCEAN_INTEGRATION.md
```

---

## Context

The chatbot logic is already built in Python using FastAPI.

The Python backend exposes chatbot APIs such as:

```text
POST /chat
POST /chat/stream
GET /health
```

The application will be hosted on DigitalOcean using Docker.

The client system is built using Node.js / JavaScript. The Node developer should not rewrite the chatbot logic in Node.js. Instead, Node.js should call the hosted FastAPI chatbot API.

The recommended architecture is:

```text
Client Web UI / Node.js App
        |
        | HTTP / HTTPS API call
        v
Python FastAPI Chatbot Service
Hosted on DigitalOcean using Docker
        |
        v
Supabase / Database / OpenAI / AWS Textract / Other external services
```

---

## Main Message For Node Developer

The Python chatbot backend should remain separate from the Node.js application.

Node.js should act as the frontend/backend integration layer and call the FastAPI chatbot service over HTTPS.

Do not embed Python logic inside Node.js.

Do not run Python inside the Node.js process.

Do not duplicate chatbot business logic in Node.js.

---

## Required Design

### 1. FastAPI Service Hosting

The FastAPI app will be hosted independently on DigitalOcean.

Preferred hosting option:

```text
DigitalOcean App Platform + Dockerfile
```

The FastAPI service should expose a public HTTPS base URL, for example:

```text
https://chatbot-api.example.com
```

or the default DigitalOcean App Platform URL during development.

The Node.js app should store this URL as an environment variable:

```text
CHATBOT_API_BASE_URL=https://chatbot-api.example.com
```

---

### 2. Required FastAPI Endpoints

The Node.js developer should assume these endpoints exist.

#### Health Check

```http
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

Purpose:

- Used by DigitalOcean health checks.
- Can also be used by Node.js to verify backend availability.

---

#### Normal Chat Endpoint

```http
POST /chat
Content-Type: application/json
```

Example request body:

```json
{
  "question": "Show me revenue trend",
  "org_id": "org_3ARuGHeqbbEu5FNexlpC7ElaiyW",
  "timezone": "Europe/Amsterdam",
  "chat_history": []
}
```

Expected response body:

```json
{
  "status_code": 200,
  "message": "success",
  "answer": "..."
}
```

Use this endpoint when the UI does not need streaming.

---

#### Streaming Chat Endpoint

```http
POST /chat/stream
Content-Type: application/json
Accept: text/event-stream
```

Example request body:

```json
{
  "question": "Show me revenue trend",
  "org_id": "org_3ARuGHeqbbEu5FNexlpC7ElaiyW",
  "timezone": "Europe/Amsterdam",
  "chat_history": []
}
```

The response should be streamed back to the UI.

The Node developer should support streaming using one of these approaches:

1. Browser calls FastAPI `/chat/stream` directly using `fetch()` and reads the `ReadableStream`.
2. Browser calls Node.js, and Node.js proxies the stream from FastAPI to the browser.

Recommended for better security:

```text
Browser UI -> Node.js backend -> FastAPI /chat/stream
```

This keeps API URLs, auth logic, and backend access controlled by Node.js.

---

## Important Request Fields

### org_id

`org_id` is required.

It tells the FastAPI chatbot which organization’s data should be used.

Node.js should pass the correct organization ID based on the logged-in user/session/tenant.

Example:

```json
{
  "org_id": "org_3ARuGHeqbbEu5FNexlpC7ElaiyW"
}
```

Do not hardcode the org ID in frontend code for production.

---

### user_id

`user_id` is optional if Node.js is already passing `chat_history`.

The earlier use of `user_id` was mainly to fetch the latest historical conversations from the chatbot backend.

If Node.js owns and sends the chat history, then `user_id` is not required for core answer generation.

Recommended approach:

```text
Node.js manages user session and chat history.
FastAPI receives chat_history directly.
```

Optional:

Keep `user_id` only for logging, tracing, analytics, or future backend-side memory.

---

### timezone

Node.js should pass the user or organization timezone.

For the current client use case, use:

```json
{
  "timezone": "Europe/Amsterdam"
}
```

This is important for date-range questions because dashboard/business metrics depend on the correct timezone.

Do not rely only on server timezone.

---

### chat_history

Node.js should pass the latest conversation history when needed.

Recommended format:

```json
[
  {
    "role": "user",
    "content": "Show me revenue trend"
  },
  {
    "role": "assistant",
    "content": "Revenue trend was..."
  }
]
```

Recommended limit:

```text
latest 5 Q&A turns
```

The chatbot does not need unlimited conversation history.

---

## Node.js Integration Design

### Option A: Node.js Backend Proxy

Recommended production design.

```text
Browser UI
   |
   v
Node.js backend API
   |
   v
FastAPI chatbot service
```

Benefits:

- FastAPI base URL is hidden from the browser.
- Node.js can validate user auth/session.
- Node.js can inject correct `org_id`.
- Node.js can control `chat_history`.
- Node.js can apply rate limits and logging.
- Easier to protect backend APIs.

Node.js endpoint example:

```text
POST /api/chat
POST /api/chat/stream
```

Node.js receives browser request, validates user, builds FastAPI request, and forwards it.

---

### Option B: Browser Calls FastAPI Directly

Only acceptable for early internal testing.

```text
Browser UI
   |
   v
FastAPI chatbot service
```

This is simpler but less secure because the frontend directly knows the FastAPI endpoint.

If used, configure CORS properly in FastAPI.

---

## Recommended Production Flow

### Non-Streaming Flow

```text
1. User asks a question in the web UI.
2. Browser sends the question to Node.js backend.
3. Node.js validates logged-in user/session.
4. Node.js resolves org_id and timezone.
5. Node.js attaches latest chat_history.
6. Node.js calls FastAPI POST /chat.
7. FastAPI returns final answer.
8. Node.js returns answer to browser.
9. Browser renders answer.
```

---

### Streaming Flow

```text
1. User asks a question in the web UI.
2. Browser sends the question to Node.js backend streaming endpoint.
3. Node.js validates user/session.
4. Node.js builds request body with question, org_id, timezone, and chat_history.
5. Node.js calls FastAPI POST /chat/stream.
6. Node.js streams chunks back to browser as they arrive.
7. Browser renders tokens/chunks progressively.
8. When stream completes, browser stores final answer in chat history.
```

---

## Streaming Implementation Notes For Node.js

If using Node.js as a streaming proxy, do not wait for the full FastAPI response before sending it to the browser.

The Node.js endpoint should pipe or forward chunks as they arrive.

Expected behavior:

```text
FastAPI stream chunk -> Node.js receives chunk -> Node.js immediately sends chunk to browser
```

Avoid this bad pattern:

```text
FastAPI full stream completes -> Node.js combines all chunks -> Browser receives answer at the end
```

That removes the benefit of streaming.

---

## Authentication And Authorization

Node.js should remain responsible for user authentication.

FastAPI should receive only trusted, already-resolved business context from Node.js, such as:

```json
{
  "org_id": "...",
  "timezone": "...",
  "chat_history": [...]
}
```

Recommended:

- Node.js validates the logged-in user.
- Node.js determines which `org_id` the user belongs to.
- Node.js sends that `org_id` to FastAPI.
- FastAPI uses `org_id` only for data filtering.
- The frontend should not be trusted to send arbitrary org IDs in production.

---

## Environment Variables

### Node.js Environment Variables

```text
CHATBOT_API_BASE_URL=https://chatbot-api.example.com
CHATBOT_API_TIMEOUT_MS=120000
```

Optional:

```text
CHATBOT_API_KEY=<internal-service-key-if-added>
```

---

### FastAPI Environment Variables

These should be configured in DigitalOcean App Platform:

```text
DATABASE_URL=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
DEFAULT_TIMEZONE=Europe/Amsterdam
ENVIRONMENT=dev
```

Use DigitalOcean environment variables/secrets, not hardcoded values.

---

## CORS Guidance

If browser calls FastAPI directly, FastAPI must allow the frontend domain.

Example allowed origins:

```text
https://client-app.example.com
http://localhost:3000
```

If browser calls only Node.js and Node.js calls FastAPI server-to-server, FastAPI does not need broad browser CORS access.

Preferred production approach:

```text
Browser -> Node.js
Node.js -> FastAPI
```

So CORS is mainly handled by Node.js frontend/backend setup.

---

## Error Handling

Node.js should handle FastAPI errors gracefully.

Recommended behavior:

| FastAPI issue | Node.js/UI behavior |
|---|---|
| FastAPI unavailable | Show friendly message: chatbot is temporarily unavailable |
| Timeout | Show retry option |
| 400 validation error | Show user-friendly invalid request message |
| 401/403 if internal auth is added | Do not show technical details |
| 500 error | Log internally and show generic failure message |
| Stream interrupted | Show partial answer if useful and allow retry |

Do not expose internal Python stack traces to the browser.

---

## Timeout Guidance

Chatbot responses may take longer than normal API calls because LLM and database/tool calls can be involved.

Recommended timeout:

```text
60 to 120 seconds
```

For streaming, keep the connection open while chunks are arriving.

---

## Logging Guidance

Node.js should log:

```text
request_id
user_id or session_id
org_id
question timestamp
FastAPI response status
latency
stream completed or failed
```

Do not log sensitive data unnecessarily.

Do not log API keys or secrets.

---

## Request ID

Node.js should generate a request ID and pass it to FastAPI using a header:

```http
X-Request-ID: <uuid>
```

This helps trace one user question across Node.js logs and FastAPI logs.

Optional additional headers:

```http
X-Org-ID: <org_id>
X-User-ID: <user_id>
```

Only use headers for tracing/context. The request body should still include required fields unless the FastAPI contract is changed.

---

## Deployment Design On DigitalOcean

Recommended:

```text
FastAPI backend:
DigitalOcean App Platform
Dockerfile-based deployment
Auto deploy from GitHub branch

Node.js app:
Existing client hosting or separate DigitalOcean App Platform app
```

If both Node.js and FastAPI are deployed on DigitalOcean App Platform, keep them as separate services/apps unless the client specifically wants one combined deployment.

Recommended separation:

```text
node-web-app
chatbot-fastapi-api
```

This keeps Python dependencies and Node.js dependencies independent.

---

## Docker Expectations For FastAPI

The FastAPI Docker container should:

- Install Python dependencies.
- Expose the correct port.
- Start Uvicorn.
- Use environment variables.
- Not store persistent files inside the container.
- Write only temporary files to local disk if required.

Runtime command example:

```text
uvicorn main:app --host 0.0.0.0 --port 8080
```

If DigitalOcean provides a `PORT` environment variable, use that in the startup command if needed.

---

## File Storage Guidance

Do not rely on container local storage for persistent files.

For uploaded PDFs, OCR files, logs, or generated artifacts, use external storage such as:

```text
Supabase Storage
DigitalOcean Spaces
AWS S3
Database storage where appropriate
```

Local container storage should be treated as temporary.

---

## Suggested API Contract

### POST /chat

Request:

```json
{
  "question": "string",
  "org_id": "string",
  "timezone": "string",
  "chat_history": [
    {
      "role": "user",
      "content": "string"
    },
    {
      "role": "assistant",
      "content": "string"
    }
  ]
}
```

Response:

```json
{
  "status_code": 200,
  "message": "success",
  "answer": "string"
}
```

---

### POST /chat/stream

Request:

```json
{
  "question": "string",
  "org_id": "string",
  "timezone": "string",
  "chat_history": []
}
```

Streaming response examples:

```text
data: {"type":"token","content":"Trend period:"}

data: {"type":"token","content":" Mar 2026 through May 2026"}

data: {"type":"final","answer":"Full final answer here"}

data: [DONE]
```

The exact stream format should be confirmed with the FastAPI implementation.

Node.js should not assume only one chunk format unless it is documented by the backend.

---

## UI Behavior Requirements

The UI should support:

- User text input.
- Loading state.
- Streaming answer display.
- Retry on failure.
- Chat history display.
- Reset/new chat option.
- Optional display of “thinking” or progress messages only if the backend sends them.
- Disable send button while a request is actively streaming, unless multi-message concurrency is intentionally supported.

---

## Security Notes

- Do not expose service keys in browser JavaScript.
- Do not trust frontend-provided `org_id` in production.
- Resolve `org_id` in Node.js from authenticated session or tenant context.
- Keep FastAPI service protected if possible.
- Consider an internal API key between Node.js and FastAPI:

```http
Authorization: Bearer <internal-service-key>
```

- Store secrets in DigitalOcean environment variables or the client’s secret manager.

---

## Acceptance Criteria

The generated handoff document is complete when it explains:

- Why Python/FastAPI remains separate from Node.js.
- How Node.js should call FastAPI.
- How `/chat` and `/chat/stream` should be used.
- How streaming should be proxied.
- Why `org_id` is required.
- Why `user_id` is optional if Node.js sends chat history.
- How timezone should be passed.
- What environment variables are needed.
- How errors, timeout, and logs should be handled.
- How DigitalOcean App Platform + Docker fits into the deployment.
- What the recommended production architecture is.

---

## Final Instruction To Codex

Create the file:

```text
NODE_FASTAPI_DIGITALOCEAN_INTEGRATION.md
```

Use the above content as the basis, but make it clean and developer-friendly.

Do not add unrelated implementation details.

Do not modify application code unless specifically asked.

Do not change existing API behavior unless the codebase already has a different confirmed contract.

If the current FastAPI endpoint request/response schemas are different from the examples above, document the actual schema from the codebase and mention the difference clearly.
