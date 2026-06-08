# Codex Instructions: FastAPI Response Contract + LangSmith Full Tracing + SSE Streaming

## Objective

Update the FastAPI chatbot API response contract and LangSmith tracing.

The frontend/Node response must stay minimal, but LangSmith must capture full trace details for debugging.

The client is okay with business-sensitive information being stored in LangSmith traces, including full answers and links if those links are part of the answer. However, never log infrastructure secrets such as API keys, service role keys, database passwords, OpenAI keys, or LangSmith keys.

## Current context

The chatbot already works locally through FastAPI:

```text
POST /chat
```

The chatbot has a two-stage flow:

```text
User question
  -> router
  -> selected route: sql_analytics / diagnostic_analytics / lead_360 / etc.
  -> selected skill or tool
  -> SQL/tool execution where applicable
  -> final answer generation
```

LangSmith project/configuration is already created.

Do not build a custom Supabase audit layer in this task. LangSmith is the primary trace/debug store.

---

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

Rules:

- `question` is required.
- `user_id` is required.
- `org_id` is required.
- `timezone` is required in the request.
- `chat_history` is optional and defaults to an empty list.
- FastAPI should not fetch chat history from Supabase.
- Use only the history passed by Node.

---

## Required `/chat` success response

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
- `answer` must contain the full final answer shown to the user.
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
- Do not return LangSmith provider/project name.
- Do not return full debug steps in the API response.
- Do not return generated SQL in the API response.
- Do not return tool outputs in the API response.

---

## Required `/chat` error response

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

- Do not expose Python stack traces to frontend.
- Do not expose raw database errors to frontend.
- Do not expose OpenAI/LangSmith/API key errors to frontend.
- The detailed error must be captured in LangSmith.
- Frontend should rely on HTTP status code and `message`.

---

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
- The FastAPI response must return only the LangSmith `trace_id`.
- Do not return `root_run_id` in the response.
- Do not hardcode LangSmith API keys or project name.
- Use the LangSmith environment/configuration already present in the project.

---

## What to capture in LangSmith for every request

Capture complete trace data for debugging.

For every request, capture:

```text
question
standalone_question
user_id
org_id
timezone
chat_history_count
route
selected_skill, if applicable
selected_tool, if applicable
full_final_answer
latency
status_code
error_details, if any
```

Important:

- Do not store only `answer_preview`.
- Store the complete final answer in LangSmith.
- If payment links, meeting links, recording references, or contact details are part of the final answer, they may be captured in LangSmith because the client has approved this.
- Never store infrastructure secrets: API keys, service role keys, database passwords, OpenAI keys, LangSmith keys, or `.env` values.

---

## LangSmith capture for `sql_analytics`

For `sql_analytics`, capture full SQL debugging information.

Capture:

```text
selected_skill
complete_generated_sql
sql_params
sql_execution_status
row_count
column_names
complete_sql_result
full_final_answer
```

Rules:

- Do not store only `small_result_preview`.
- Do not store only truncated SQL.
- Store the complete generated SQL text.
- Store the complete SQL result returned to the answer-generation step.
- Large SQL strings/results are acceptable for debugging.
- If LangSmith or transport payload limits are hit, do not silently truncate. Instead:
  - set `truncated: true`
  - store the reason
  - keep as much data as possible
  - optionally add a `full_output_storage_ref` only if an overflow storage mechanism already exists

---

## LangSmith capture for `diagnostic_analytics`

For diagnostic analytics, SQL is usually hidden inside prebuilt tools/functions, so generated SQL is not required unless it already exists in the code.

Capture for each diagnostic tool call:

```text
tool_name
complete_tool_input
complete_tool_output
full_final_answer
```

Rules:

- Do not store only `tool_output_preview`.
- Store complete tool output used by the final answer generation.
- If multiple diagnostic tools are called, capture each tool call as a child span/run.

---

## LangSmith capture for `lead_360`

Capture:

```text
tool_name
complete_tool_input
complete_tool_output
sections_used
lead_match_status
full_final_answer
```

Rules:

- Do not store only `safe_output_preview`.
- Store complete output used by final answer generation.
- If the final answer includes payment links, meeting links, or lead-level business details, it is okay to capture them in LangSmith.
- Still never capture infrastructure secrets.

---

## LangSmith capture for all other skills/tools

For every skill/tool/route, capture:

```text
name
input
complete_output
latency
success_or_failure
error_details, if any
```

Rules:

- All skills require complete output in LangSmith tracing.
- Avoid generic `preview` fields unless there is also a full output field.
- Every trace must make it possible to debug:
  - route selection
  - skill selection
  - SQL/tool input
  - SQL/tool output
  - final answer correctness

---

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

The current Streamlit chatbot already has step-by-step streaming behavior. Do not redesign or hardcode a new fake streaming flow.

Goal of this task:

```text
Move existing streaming behavior from Streamlit to FastAPI SSE.
```

The UI should receive the same kind of step-by-step updates that are currently shown in Streamlit.

---

## SSE method

FastAPI should stream events in this format:

```text
event: <event_name>
data: <json_payload>

```

Use these event types:

```text
status
route
delta
done
error
```

### `status` event

Use for existing progress/status messages currently emitted by the chatbot.

Example:

```text
event: status
data: {"message":"Understanding your question..."}

```

### `route` event

Send when route is selected.

Example:

```text
event: route
data: {"route":"sql_analytics"}

```

### `delta` event

Use for answer chunks if the current streaming logic already emits answer chunks.

Example:

```text
event: delta
data: {"text":"- Trend period: Mar 2026 through May 2026\n"}

```

If the current code only emits step updates and returns the final answer at the end, then `delta` can be skipped initially.

### `done` event

The final `done` event must contain the same response schema as `/chat` success.

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

- Once the SSE stream has started, HTTP status is usually already `200`.
- Runtime errors after that point must be sent as `event: error` with `status_code` inside the event data.

---

## Frontend/Node behavior expectation

Frontend/Node should display:

```text
status messages
route if required by UI/admin view
answer deltas or final answer
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

Frontend should not display raw SQL or full LangSmith trace details to normal users.

---

## Acceptance criteria

Implementation is complete only when all of these are true:

- `/chat` returns the exact minimal response schema.
- `/chat` uses HTTP 200 for success.
- `/chat` uses non-200 status codes for errors.
- Success response uses `message: "success"`.
- Error response uses user-safe `message`.
- Response contains only:
  - `status_code`
  - `message`
  - `answer`
  - `route`
  - `standalone_question`
  - `trace_id`
- No `success` boolean is returned.
- No `error: null` is returned.
- No `timezone` is returned.
- No `root_run_id` is returned.
- No generated SQL is returned to frontend.
- No tool output is returned to frontend.
- LangSmith receives one trace per user question.
- LangSmith captures full final answer.
- LangSmith captures complete SQL for `sql_analytics`.
- LangSmith captures complete SQL result for `sql_analytics` where available.
- LangSmith captures complete input and output for diagnostic, lead_360, and other tool/skill calls.
- LangSmith captures detailed errors.
- `/chat/stream` uses SSE.
- `/chat/stream` migrates existing Streamlit step-by-step streaming behavior to FastAPI SSE.
- `/chat/stream` ends with a `done` event using the same final schema.
- Streaming errors are sent using `event: error`.

---

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

### Test 4: LangSmith trace validation

After running `/chat` or `/chat/stream`, open the returned `trace_id` in LangSmith and confirm:

```text
one root trace exists
route decision is captured
selected route is captured
selected skill/tool is captured
complete generated SQL is captured for sql_analytics
complete SQL result is captured for sql_analytics where available
complete tool input/output is captured for diagnostic and lead_360
complete final answer is captured
errors are captured if any
```
