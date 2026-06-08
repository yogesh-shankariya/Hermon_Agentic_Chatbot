# Codex Instructions: FastAPI Response Contract + LangSmith Trace ID

## Objective

Update the FastAPI chatbot API so every response has a small, stable response shape that is easy for the Node/Hermon frontend to consume.

The API must return only the user-facing answer and the LangSmith `trace_id`. Full internal debugging details must be stored in LangSmith, not returned in the API response.

## Current context

The chatbot already works locally through FastAPI:

```text
POST /chat
```

The current chatbot has a two-stage flow:

```text
User question
  -> router
  -> selected route: sql_analytics / diagnostic_analytics / lead_360 / etc.
  -> selected skill or tool
  -> SQL/tool execution where applicable
  -> final answer generation
```

The project now has a LangSmith project configured for tracing.

## Required request body

Do not use `session_id`.

Node will pass the latest chat history to FastAPI directly.

Expected request body:

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

Notes:

- `question` is required.
- `user_id` is required.
- `org_id` is required.
- `timezone` is required in the request, but must not be returned in the final response body.
- `chat_history` is optional and defaults to an empty list.
- Use only the latest history passed by Node. FastAPI should not fetch chat history from Supabase.

## Required normal `/chat` success response

HTTP status code:

```text
200 OK
```

Response body must contain only these fields:

```json
{
  "status_code": 200,
  "message": "success",
  "answer": "- Trend period: Mar 2026 through May 2026\n- Total gross paid revenue in this period: €936,550.",
  "route": "sql_analytics",
  "standalone_question": "Show me revenue trend",
  "trace_id": "trace_abc123"
}
```

Rules:

- `status_code` must match the HTTP status code.
- `message` must be exactly `success` for successful requests.
- `answer` must contain the final chatbot answer shown to the user.
- `route` must contain the selected route, for example:
  - `sql_analytics`
  - `diagnostic_analytics`
  - `lead_360`
  - `unsupported`
- `standalone_question` must contain the rewritten standalone question used by the chatbot.
- `trace_id` must contain the LangSmith trace ID for this request.
- Do not return `success: true`.
- Do not return `error: null`.
- Do not return `timezone`.
- Do not return `root_run_id`.
- Do not return full debug steps.
- Do not return generated SQL in the API response.
- Do not return SQL result preview in the API response.

## Required normal `/chat` error response

For validation errors, return a non-200 HTTP status code, usually:

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

For internal errors, return:

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
  "trace_id": "trace_error_123"
}
```

Rules:

- Do not expose Python stack traces to the frontend.
- Do not expose raw database errors to the frontend.
- Do not expose OpenAI/LangSmith/API key errors to the frontend.
- The detailed error should be captured in LangSmith trace.
- The frontend should rely on HTTP status code and `message`.

## LangSmith tracing requirement

Implement LangSmith tracing around the full `/chat` execution.

There must be exactly one root trace per user question.

Correct trace structure:

```text
Root trace: /chat request
  -> route_decision
  -> skill_selection or tool_selection
  -> sql_generation, if applicable
  -> sql_execution, if applicable
  -> diagnostic_tool_call, if applicable
  -> lead_360_tool_call, if applicable
  -> final_answer_generation
```

Important:

- Do not create a separate root trace for every model call.
- Model calls, SQL calls, and tool calls must be child runs/spans under the same root trace.
- The FastAPI response must return the LangSmith `trace_id`.
- Do not return LangSmith project name or provider in the response.
- Do not return `root_run_id` in the response.
- Do not hardcode LangSmith API keys or project name.
- Use the LangSmith environment/configuration already present in the project.

## What to store in LangSmith

LangSmith should contain detailed trace data for debugging.

For every request, capture at least:

```text
question
standalone_question
user_id
org_id
route
selected_skill
selected_tool
chat_history_count
timezone
latency
final_answer
error, if any
```

For `sql_analytics`, capture in LangSmith:

```text
generated_sql
sql_params
row_count
column_names
small_result_preview
```

For `diagnostic_analytics`, capture in LangSmith:

```text
tool_name
tool_input
tool_output_preview
```

For `lead_360`, capture in LangSmith:

```text
lead_match_status
sections_used
safe_output_preview
```

Do not send these sensitive values to LangSmith unless explicitly required and approved:

```text
API keys
service role keys
full payment links
full meeting links
full recording links
large raw transcripts
large raw SQL results
unmasked private contact details
```

## Required `/chat/stream` behavior

Keep `/chat` working as a normal non-streaming endpoint.

Add or update:

```text
POST /chat/stream
```

This endpoint must use Server-Sent Events.

Response content type:

```text
text/event-stream
```

Streaming is for UI experience only. Full debug trace still goes to LangSmith.

## `/chat/stream` event types

Use these event types:

```text
status
route
delta
done
error
```

### `status` event

Use for user-friendly progress updates.

Example:

```text
event: status
data: {"message":"Understanding your question..."}
```

### `route` event

Send after the route is selected.

Example:

```text
event: route
data: {"route":"sql_analytics"}
```

### `delta` event

Use for final answer chunks when token streaming is available.

Example:

```text
event: delta
data: {"text":"- Trend period: Mar 2026 through May 2026\n"}
```

If the final OpenAI call is not yet implemented with token streaming, it is acceptable to skip `delta` events initially and return the full answer in the `done` event.

### `done` event

The `done` event must contain the same response schema as `/chat` success.

Example:

```text
event: done
data: {"status_code":200,"message":"success","answer":"- Trend period: Mar 2026 through May 2026\n- Total gross paid revenue in this period: €936,550.","route":"sql_analytics","standalone_question":"Show me revenue trend","trace_id":"trace_abc123"}
```

### `error` event

If an error happens after streaming has already started, send an `error` event.

Example:

```text
event: error
data: {"status_code":500,"message":"Unable to complete this request.","answer":null,"route":"sql_analytics","standalone_question":"Show me revenue trend","trace_id":"trace_error_123"}
```

Important streaming rule:

- Once the SSE stream has started, the HTTP status is usually already `200`.
- Runtime errors after that point must be sent as `event: error` with `status_code` inside the event data.

## Frontend behavior expectation

Frontend/Node should display only the chatbot answer and optionally progress messages.

Frontend should not display:

```text
generated SQL
raw tool input
raw tool output
LangSmith internals
full debug traces
```

Frontend/Node should store at least:

```text
question
answer
route
standalone_question
trace_id
status_code
message
created_at
```

This allows later debugging by looking up the `trace_id` in LangSmith.

## Acceptance criteria

The implementation is complete only when all of these are true:

- `/chat` returns the exact minimal response schema.
- `/chat` uses HTTP 200 for success.
- `/chat` uses non-200 status codes for errors.
- Success response uses `message: "success"`.
- Error response uses a user-safe error message.
- No `success` boolean is returned.
- No `error: null` is returned.
- No `timezone` is returned.
- No `root_run_id` is returned.
- No full debug trace is returned.
- No SQL/debug payload is returned to frontend.
- LangSmith receives one trace per user question.
- The API response includes LangSmith `trace_id`.
- `/chat/stream` sends SSE events and ends with a `done` event using the same final schema.
- Streaming errors are sent using `event: error`.
- Existing `/chat` behavior remains backward-compatible at business logic level.

## Suggested test cases

### Test 1: Health

```bash
curl http://127.0.0.1:8000/health
```

### Test 2: Normal chat

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me revenue trend",
    "user_id": "user_test",
    "org_id": "org_3ARuGHeqbbEu5FNexlpC7ElaiyW",
    "timezone": "Europe/Amsterdam",
    "chat_history": []
  }'
```

Expected:

```json
{
  "status_code": 200,
  "message": "success",
  "answer": "...",
  "route": "sql_analytics",
  "standalone_question": "Show me revenue trend",
  "trace_id": "..."
}
```

### Test 3: Streaming chat

```bash
curl -N -X POST "http://127.0.0.1:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me revenue trend",
    "user_id": "user_test",
    "org_id": "org_3ARuGHeqbbEu5FNexlpC7ElaiyW",
    "timezone": "Europe/Amsterdam",
    "chat_history": []
  }'
```

Expected:

```text
event: status
...
event: route
...
event: done
...
```

The `done` event must contain:

```json
{
  "status_code": 200,
  "message": "success",
  "answer": "...",
  "route": "sql_analytics",
  "standalone_question": "...",
  "trace_id": "..."
}
```
