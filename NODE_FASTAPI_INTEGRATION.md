# Node Integration Guide for Hermon FastAPI Chatbot

This document is for the Node/backend developer who will call the Hermon FastAPI chatbot after it is deployed with Docker.

The Node app is responsible for user/session management, storing chat messages, and passing the latest chat history to FastAPI. FastAPI is responsible for routing the question, running the chatbot tools, returning the answer, and writing full debug traces to LangSmith.

## Base URL

Local Docker example:

```text
http://127.0.0.1:8000
```

Production should use an environment variable in Node, for example:

```bash
HERMON_CHATBOT_API_URL="https://your-fastapi-service.example.com"
```

## Available Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Health check. |
| `POST` | `/chat` | Normal non-streaming chat response. |
| `POST` | `/chat/stream` | Server-Sent Events streaming response for live progress updates. |

## Important Rules

- Do not send `session_id`.
- Node must send `question`, `user_id`, `org_id`, and `timezone`.
- Node may send `chat_history`; if omitted, FastAPI treats it as an empty list.
- FastAPI does not fetch chat history from Supabase or Node storage.
- FastAPI uses only the `chat_history` included in the request body.
- API responses are intentionally minimal.
- Do not expect generated SQL, raw tool outputs, or debug steps in the API response.
- Use the returned `trace_id` for debugging in LangSmith.
- Do not expose backend `.env` values, OpenAI keys, database URLs, or LangSmith keys to the browser.

## Docker Deployment

Build:

```bash
docker build -t hermon-chatbot-api .
```

Run locally with the backend `.env` file:

```bash
docker run --rm --env-file .env -p 8000:8000 hermon-chatbot-api
```

If port `8000` is already busy:

```bash
docker run --rm --env-file .env -p 8001:8000 hermon-chatbot-api
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

## Required Backend Environment

The FastAPI Docker container needs the existing backend `.env` values. Node should not know or expose these values.

Important backend variables include:

```bash
OPENAI_API_KEY="..."
OPENAI_MODEL="..."
HERMON_DATABASE_URL="..."
DATABASE_URL="..."
HERMON_DEFAULT_CLERK_ORG_ID="..."
```

LangSmith variables should also remain in the FastAPI container environment if tracing is enabled in `.env`.

## Request Body

Use the same body for both `/chat` and `/chat/stream`.

```json
{
  "question": "Show me revenue trend",
  "user_id": "user_123",
  "org_id": "org_3ARuGHeqbbEu5FNexlpC7ElaiyW",
  "timezone": "Europe/Amsterdam",
  "chat_history": [
    {
      "role": "user",
      "content": "Previous user question"
    },
    {
      "role": "assistant",
      "content": "Previous assistant answer"
    }
  ]
}
```

### Field Rules

| Field | Required | Type | Notes |
|---|---:|---|---|
| `question` | Yes | string | The current user question. Must not be blank. |
| `user_id` | Yes | string | The authenticated Node/frontend user ID. |
| `org_id` | Yes | string | Clerk organization ID or equivalent tenant/org ID. |
| `timezone` | Yes | string | IANA timezone, for example `Europe/Amsterdam`. |
| `chat_history` | No | array | Latest role/content messages. Defaults to `[]`. |

### Chat History Format

Each history item should be:

```json
{
  "role": "user",
  "content": "Message text"
}
```

or:

```json
{
  "role": "assistant",
  "content": "Message text"
}
```

Recommended Node behavior:

- Store full chat history in Node/database.
- Send only the latest relevant messages to FastAPI, usually the latest 5 to 10 user/assistant turns.
- Keep messages in chronological order, oldest first.
- Do not include system prompts, internal SQL, or tool output in `chat_history`.

## Normal Chat Endpoint

```text
POST /chat
Content-Type: application/json
```

### Success Response

HTTP status:

```text
200 OK
```

Body:

```json
{
  "status_code": 200,
  "message": "success",
  "answer": "- Trend period: Mar 2026 through May 2026\n- Total gross paid revenue in this period: EUR 936,550.",
  "route": "sql_analytics",
  "standalone_question": "Show me revenue trend",
  "trace_id": "019e9def-fc83-7f72-accc-32d03899a95d"
}
```

### Error Response

Validation errors usually return:

```text
400 Bad Request
```

Example:

```json
{
  "status_code": 400,
  "message": "Question is required.",
  "answer": null,
  "route": null,
  "standalone_question": null,
  "trace_id": null
}
```

Internal errors return:

```text
500 Internal Server Error
```

Example:

```json
{
  "status_code": 500,
  "message": "Unable to complete this request.",
  "answer": null,
  "route": "sql_analytics",
  "standalone_question": "Show me revenue trend",
  "trace_id": "019e9def-fc83-7f72-accc-32d03899a95d"
}
```

### Route Values

Possible `route` values include:

```text
sql_analytics
diagnostic_analytics
lead_360
unsupported
```

## Streaming Chat Endpoint

```text
POST /chat/stream
Content-Type: application/json
Accept: text/event-stream
```

Response content type:

```text
text/event-stream
```

This endpoint streams Server-Sent Events using this format:

```text
event: <event_name>
data: <json_payload>

```

### Event Types

| Event | Purpose |
|---|---|
| `status` | Progress message, for example "Calling the router model...". |
| `route` | Sent when the route is selected. |
| `delta` | Reserved for answer chunks if token streaming is added later. |
| `done` | Final success event. Contains the same schema as `/chat`. |
| `error` | Final error event if the stream already started. |

Important: the current implementation streams live progress messages. The final answer is sent at the end in the `done` event. Answer token deltas are not currently emitted.

### Streaming Example

```text
event: status
data: {"message":"Understanding your question..."}

event: route
data: {"route":"sql_analytics"}

event: done
data: {"status_code":200,"message":"success","answer":"Final answer here","route":"sql_analytics","standalone_question":"Show me revenue trend","trace_id":"019e9def-fc83-7f72-accc-32d03899a95d"}

```

### Terminal Test

Use `curl -N` so the terminal does not buffer events:

```bash
curl -N -X POST "http://127.0.0.1:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "question": "Show me revenue trend",
    "user_id": "user_123",
    "org_id": "org_3ARuGHeqbbEu5FNexlpC7ElaiyW",
    "timezone": "Europe/Amsterdam",
    "chat_history": []
  }'
```

Swagger `/docs` may show the stream only after completion. That is a Swagger/browser buffering behavior, not necessarily an API issue.

## TypeScript Types

```ts
export type HermonChatRole = "user" | "assistant";

export type HermonChatHistoryMessage = {
  role: HermonChatRole;
  content: string;
};

export type HermonChatRequest = {
  question: string;
  user_id: string;
  org_id: string;
  timezone: string;
  chat_history?: HermonChatHistoryMessage[];
};

export type HermonChatRoute =
  | "sql_analytics"
  | "diagnostic_analytics"
  | "lead_360"
  | "unsupported";

export type HermonChatResponse = {
  status_code: number;
  message: string;
  answer: string | null;
  route: HermonChatRoute | null;
  standalone_question: string | null;
  trace_id: string | null;
};

export type HermonStreamEvent =
  | { event: "status"; data: { message: string } }
  | { event: "route"; data: { route: HermonChatRoute } }
  | { event: "delta"; data: { text: string } }
  | { event: "done"; data: HermonChatResponse }
  | { event: "error"; data: HermonChatResponse };
```

## Node Example for `/chat`

```ts
const HERMON_CHATBOT_API_URL =
  process.env.HERMON_CHATBOT_API_URL ?? "http://127.0.0.1:8000";

export async function callHermonChat(
  payload: HermonChatRequest,
): Promise<HermonChatResponse> {
  const response = await fetch(`${HERMON_CHATBOT_API_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...payload,
      chat_history: payload.chat_history ?? [],
    }),
  });

  const data = (await response.json()) as HermonChatResponse;

  if (!response.ok) {
    // Store trace_id if present, but show only data.message to the user.
    throw new Error(data.message || "Chatbot request failed.");
  }

  return data;
}
```

## Node Example for `/chat/stream`

Use `fetch()` with a stream reader. Do not use browser `EventSource` for this endpoint because `EventSource` only supports `GET`, while this endpoint is `POST`.

```ts
const HERMON_CHATBOT_API_URL =
  process.env.HERMON_CHATBOT_API_URL ?? "http://127.0.0.1:8000";

function parseSseBlock(block: string): HermonStreamEvent | null {
  const lines = block.split("\n");
  let eventName = "";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }

  if (!eventName || dataLines.length === 0) {
    return null;
  }

  return {
    event: eventName,
    data: JSON.parse(dataLines.join("\n")),
  } as HermonStreamEvent;
}

export async function streamHermonChat(
  payload: HermonChatRequest,
  handlers: {
    onStatus?: (message: string) => void;
    onRoute?: (route: HermonChatRoute) => void;
    onDelta?: (text: string) => void;
    onDone?: (response: HermonChatResponse) => void;
    onError?: (response: HermonChatResponse) => void;
  },
): Promise<void> {
  const response = await fetch(`${HERMON_CHATBOT_API_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      ...payload,
      chat_history: payload.chat_history ?? [],
    }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream failed with HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const parsed = parseSseBlock(block);
      if (!parsed) continue;

      if (parsed.event === "status") {
        handlers.onStatus?.(parsed.data.message);
      } else if (parsed.event === "route") {
        handlers.onRoute?.(parsed.data.route);
      } else if (parsed.event === "delta") {
        handlers.onDelta?.(parsed.data.text);
      } else if (parsed.event === "done") {
        handlers.onDone?.(parsed.data);
      } else if (parsed.event === "error") {
        handlers.onError?.(parsed.data);
      }
    }
  }
}
```

## What Node Should Store

After each completed request, store at least:

```json
{
  "question": "Show me revenue trend",
  "answer": "Final answer text",
  "route": "sql_analytics",
  "standalone_question": "Show me revenue trend",
  "trace_id": "019e9def-fc83-7f72-accc-32d03899a95d",
  "status_code": 200,
  "message": "success",
  "created_at": "2026-06-08T10:00:00.000Z"
}
```

Do not store or display raw SQL from the API response, because the API does not return it. Full debug details live in LangSmith under `trace_id`.

## UI Behavior Recommendation

For `/chat/stream`:

1. Show incoming `status` messages as progress text.
2. Optionally show `route` in an admin/debug view.
3. If `delta` events appear in the future, append them to the visible answer.
4. On `done`, replace or finalize the answer with `done.data.answer`.
5. On `error`, show `error.data.message` to the user and log `error.data.trace_id` for support.

For `/chat`:

1. Show loading state until the request completes.
2. If HTTP status is not `200`, show `message`.
3. If HTTP status is `200`, show `answer`.
4. Store `trace_id` with the message for later debugging.

## Browser and CORS Note

The intended integration is:

```text
Browser frontend -> Node backend -> FastAPI chatbot
```

If the browser calls FastAPI directly, CORS and authentication must be added to FastAPI first. Do not expose backend secrets or unrestricted FastAPI access directly to browsers.

## Timeout Guidance

Chatbot requests can take longer than normal CRUD APIs because they may call:

- router model
- SQL generation model
- SQL execution
- diagnostic tools
- final answer model

Recommended Node timeout:

```text
120 seconds minimum
```

Streaming is preferred for the UI because users can see progress while the chatbot works.

## Quick Checklist for Node Developer

- Set `HERMON_CHATBOT_API_URL`.
- Send `question`, `user_id`, `org_id`, `timezone`, and latest `chat_history`.
- Do not send `session_id`.
- Use `/chat` for simple request/response.
- Use `/chat/stream` for live progress.
- Store `answer`, `route`, `standalone_question`, `trace_id`, `status_code`, and `message`.
- Show only user-safe `message` on errors.
- Use `trace_id` for backend support and LangSmith debugging.
