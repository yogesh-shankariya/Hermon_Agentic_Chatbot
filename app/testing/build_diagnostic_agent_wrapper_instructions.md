# Codex Task: Build Diagnostic Agent Wrapper

## Goal

Create a separate diagnostic agent for the `diagnostic_analytics` route.

The diagnostic agent must behave like the Lead 360 agent pattern:

- It is separate from SQL analytics.
- It does not call the SQL agent.
- It does not call `load_skill`.
- It does not call `run_readonly_sql`.
- It does not generate SQL.
- It uses only diagnostic tools.
- It answers only from diagnostic tool evidence.

The diagnostic tools already exist and have passed direct smoke tests.

Do not rebuild or modify `diagnostic_lead_snapshot`.
Do not modify diagnostic tool SQL unless tests fail.
Do not add free-form SQL generation.

---

## Expected Runtime Flow

```text
User question
  -> Router
  -> route = diagnostic_analytics
  -> Diagnostic Agent
  -> Diagnostic tools only
  -> Final diagnostic answer
```

This must stay separate from:

```text
sql_analytics
  -> SQL Agent
  -> load_skill
  -> run_readonly_sql
```

and separate from:

```text
lead_360
  -> Lead 360 Agent
  -> get_lead_360
```

---

## Files To Create

Create:

```text
app/agents/diagnostic_agent/__init__.py
app/agents/diagnostic_agent/builder.py
```

---

## Files To Update

Update:

```text
app/orchestrator.py
tests/test_orchestrator.py
```

If the repo uses different existing test files for routing/agent wiring, update the closest matching test file instead.

Do not update SQL skill prompts in this task.

---

## Prompt File

Load the diagnostic prompt from:

```text
app/skills/modules/diagnostic_analytics.md
```

Follow the same prompt-loading style used by the existing Lead 360 agent.

The diagnostic prompt must be used as the system/instruction prompt for the diagnostic agent.

---

## Tool List

Attach only:

```python
DIAGNOSTIC_TOOLS
```

from:

```python
app.tools.diagnostic_tools
```

The diagnostic agent tool list must contain exactly these four tools:

```text
get_diagnostic_funnel_snapshot
get_diagnostic_source_snapshot
get_diagnostic_source_quality_snapshot
get_diagnostic_business_change_snapshot
```

The diagnostic agent must not include:

```text
load_skill
run_readonly_sql
get_lead_360
```

---

## Builder API

Expose a builder function similar to:

```python
create_diagnostic_agent()
```

Also expose a prompt loader function if that matches existing project style:

```python
load_diagnostic_prompt()
```

Use the same model factory / LLM initialization pattern as the existing SQL agent or Lead 360 agent.

Do not create a new custom LLM initialization pattern unless required by the current codebase.

---

## `app/agents/diagnostic_agent/__init__.py`

Export the public builder function.

Expected exports:

```python
from app.agents.diagnostic_agent.builder import create_diagnostic_agent

__all__ = ["create_diagnostic_agent"]
```

If the builder also exposes `load_diagnostic_prompt`, include it in `__all__`.

---

## `app/agents/diagnostic_agent/builder.py`

Implement the diagnostic agent builder.

Required behavior:

1. Load `app/skills/modules/diagnostic_analytics.md`.
2. Create the agent using the existing project agent pattern.
3. Bind only `DIAGNOSTIC_TOOLS`.
4. Return the runnable/agent object expected by the orchestrator.
5. Do not add SQL tools.
6. Do not add Lead 360 tools.
7. Do not add arbitrary database tools.

Pseudo-structure:

```python
from pathlib import Path

from app.tools.diagnostic_tools import DIAGNOSTIC_TOOLS

DIAGNOSTIC_PROMPT_PATH = Path("app/skills/modules/diagnostic_analytics.md")


def load_diagnostic_prompt() -> str:
    return DIAGNOSTIC_PROMPT_PATH.read_text(encoding="utf-8")


def create_diagnostic_agent():
    prompt = load_diagnostic_prompt()
    # Follow existing Lead 360 / SQL agent construction pattern.
    # Attach only DIAGNOSTIC_TOOLS.
    # Return agent.
```

Use the actual project conventions instead of the pseudo-code where needed.

---

## Orchestrator Wiring

Update the orchestrator so that:

```text
route == diagnostic_analytics
```

calls the diagnostic agent instead of returning a static unsupported response.

Expected behavior:

```text
if route == diagnostic_analytics:
    effective_agent = diagnostic_agent or diagnostic_agent_factory()
    result = effective_agent.invoke(...)
```

Follow the existing Lead 360 route pattern as closely as possible.

Do not route diagnostic questions to SQL analytics.

Do not call the SQL agent for diagnostic route.

Do not call Lead 360 agent for diagnostic route.

Do not store generated SQL for diagnostic route.

If the application stores SQL text for SQL analytics responses, leave SQL fields empty/null for diagnostic responses.

---

## History Handling

Use the same history behavior as the existing orchestrator:

- Use router-selected `history_count`.
- Include only the required previous Q&A turns.
- Append the router `standalone_question` as the latest user message.
- Do not invent context.
- Do not pass unnecessary full conversation history.

---

## Diagnostic Route Output

The diagnostic agent final answer should be returned as the normal assistant answer.

Do not expose:

```text
raw tool JSON
raw SQL
internal tool traces
internal IDs
debug metadata
```

unless the existing app already shows tool traces separately in a developer/debug UI.

The business-facing answer must come from the diagnostic agent final message.

---

## Safety Constraints

The diagnostic agent must never:

```text
generate SQL
call run_readonly_sql
call load_skill
call get_lead_360
modify data
refresh diagnostic_lead_snapshot
run admin scripts
create/update/delete records
access raw payloads
access credentials
access API keys
access webhook payloads
access emails or phone numbers
access raw notes or raw call summaries
```

---

## Tests To Add Or Update

Add tests for agent tool isolation.

### Test 1: Diagnostic Agent Tool List

Assert diagnostic agent has exactly these tools:

```text
get_diagnostic_funnel_snapshot
get_diagnostic_source_snapshot
get_diagnostic_source_quality_snapshot
get_diagnostic_business_change_snapshot
```

Assert diagnostic agent does not have:

```text
load_skill
run_readonly_sql
get_lead_360
```

---

### Test 2: Diagnostic Prompt Guardrails

Assert loaded diagnostic prompt contains these rules:

```text
Do not generate SQL
Do not call `run_readonly_sql`
Do not call `load_skill`
Use only diagnostic tools
```

If exact case/format differs, assert equivalent substrings.

---

### Test 3: SQL Agent Isolation

Assert SQL agent tools still contain only the existing SQL tools:

```text
load_skill
run_readonly_sql
```

Diagnostic tools must not be added to SQL agent.

---

### Test 4: Lead 360 Agent Isolation

Assert Lead 360 agent still contains only:

```text
get_lead_360
```

Diagnostic tools must not be added to Lead 360 agent.

---

### Test 5: Orchestrator Diagnostic Route

Mock router output:

```json
{
  "route": "diagnostic_analytics",
  "history_count": 0,
  "standalone_question": "Why are leads increasing but revenue is not?"
}
```

Expected:

```text
diagnostic agent is called once
SQL agent is not called
Lead 360 agent is not called
unsupported static response is not returned
```

---

### Test 6: Orchestrator SQL Route Still Works

Mock router output:

```json
{
  "route": "sql_analytics",
  "history_count": 0,
  "standalone_question": "Show revenue by source."
}
```

Expected:

```text
SQL agent is called once
diagnostic agent is not called
Lead 360 agent is not called
```

---

### Test 7: Orchestrator Lead 360 Route Still Works

Mock router output:

```json
{
  "route": "lead_360",
  "history_count": 0,
  "standalone_question": "What happened with Vedran?"
}
```

Expected:

```text
Lead 360 agent is called once
SQL agent is not called
diagnostic agent is not called
```

---

### Test 8: Unsupported Route Still Stops

Mock router output:

```json
{
  "route": "unsupported",
  "history_count": 0,
  "standalone_question": "What is Facebook Ads ROAS?"
}
```

Expected:

```text
No downstream agent is called
unsupported response is returned
```

---

## Diagnostic Route Test Questions

Use these questions for route-to-agent tests:

```text
Why are leads increasing but revenue is not?
Where are we losing people in the funnel?
Which source looks good but may be misleading?
Can we trust source performance?
What changed this month?
What should sales focus on this week?
What should marketing investigate this week?
Which source has signed contracts but low collected cash?
```

Expected route:

```text
diagnostic_analytics
```

Expected downstream agent:

```text
diagnostic_agent
```

---

## Do Not Build In This Task

Do not build:

```text
diagnostic planner
diagnostic_text_insights
semantic search
vector search
snapshot refresh tool
admin rebuild tool
free-form SQL generation
new database tables
new diagnostic SQL skills
new router logic unless existing tests require a small fix
```

---

## Completion Criteria

This task is complete only when:

```text
1. app/agents/diagnostic_agent/__init__.py exists.
2. app/agents/diagnostic_agent/builder.py exists.
3. create_diagnostic_agent() is implemented.
4. diagnostic_analytics.md is loaded as the diagnostic system prompt.
5. diagnostic agent has exactly the four diagnostic tools.
6. diagnostic agent does not have SQL tools or Lead 360 tools.
7. orchestrator routes diagnostic_analytics to diagnostic agent.
8. SQL route still goes to SQL agent.
9. Lead 360 route still goes to Lead 360 agent.
10. Unsupported route still stops without downstream agent calls.
11. Tests pass.
```

---

## Final Important Note

Diagnostic analytics is a separate agent flow, not a SQL analytics flow.

The diagnostic agent should explain using evidence from controlled diagnostic tools over `diagnostic_lead_snapshot`.

All monetary fields returned by those diagnostic tools are already major-unit EUR values from `diagnostic_lead_snapshot`. The diagnostic agent must not divide `gross_paid_amount`, `refund_amount`, `net_collected_amount`, `outstanding_amount`, `signed_contract_value`, or related current/previous money fields by `100` again.

It must not generate SQL or call the SQL agent.
