# Codex Task — Streamlit Sidebar User/Admin Mode

## Goal

Update the Streamlit UI so the same deployed Streamlit link can be used by both:

- Normal users
- Internal admin/manager users

By default, the app must open in normal `User` mode.

The client/user should not see wording like:

```text
demo data
dummy data
test data
fake data
```

The UI should look clean and normal for the client.

---

## Required Sidebar UI

Add a sidebar mode selector:

```text
Mode:
- User
- Admin
```

Default selected mode:

```text
User
```

---

## User Mode Behavior

When `User` mode is selected:

```text
active_org_id = DEMO_ORG_ID
```

No access code is required.

Do not mention demo/dummy/test/fake data in the UI.

Show only a neutral label if needed:

```text
Mode: User
```

or:

```text
Access: Standard
```

Do not show the actual organization ID.

---

## Admin Mode Behavior

When `Admin` mode is selected, show a masked input field:

```text
Admin Access Code
```

Use the term:

```text
Admin Access Code
```

Do not call it:

```text
Password
Live org ID
Organization ID
Client org ID
```

If the entered code matches `ADMIN_ACCESS_CODE` from Streamlit secrets/environment:

```text
active_org_id = LIVE_ORG_ID
```

Show a small safe label:

```text
Mode: Admin
```

or:

```text
Access: Admin
```

Do not show the live organization ID in the UI.

If the code is missing or incorrect:

```text
active_org_id = DEMO_ORG_ID
```

Show a safe warning:

```text
Invalid admin access code. Continuing in User mode.
```

Do not mention demo data in the warning.

---

## Required Secrets / Environment Variables

Read these values from Streamlit secrets or environment variables:

```text
DEMO_ORG_ID
LIVE_ORG_ID
ADMIN_ACCESS_CODE
```

Expected values:

```toml
DEMO_ORG_ID = "org_dummy_client_demo_001"
LIVE_ORG_ID = "<actual live client org id>"
ADMIN_ACCESS_CODE = "<private manager access code>"
```

The `LIVE_ORG_ID` must stay hidden in secrets/environment variables.

Do not require the manager to type the live org ID into the UI.

Do not display `DEMO_ORG_ID`, `LIVE_ORG_ID`, or `ADMIN_ACCESS_CODE`.

---

## Recommended Secret Loading Helper

Create a helper that can read from Streamlit secrets first and environment variables second.

Example behavior:

```text
value = st.secrets.get(name) if available
fallback = os.getenv(name)
```

Do not crash if `st.secrets` is unavailable in local runs.

---

## Fallback Rules

The fallback must always be safe.

If `DEMO_ORG_ID` is missing:

```text
Use HERMON_DEFAULT_CLERK_ORG_ID only if it is explicitly configured for the safe User-mode organization.
Otherwise stop with a safe configuration error.
```

If `LIVE_ORG_ID` is missing:

```text
Admin mode must not unlock admin data.
Show a safe configuration error.
Continue in User mode.
```

If `ADMIN_ACCESS_CODE` is missing:

```text
Admin mode must not unlock admin data.
Show a safe configuration error.
Continue in User mode.
```

If anything fails:

```text
active_org_id = DEMO_ORG_ID
```

Never fail open to `LIVE_ORG_ID`.

---

## Org ID Resolution Logic

Create one runtime variable:

```text
active_org_id
```

Suggested logic:

```text
mode = User by default

if mode == User:
    active_org_id = DEMO_ORG_ID

if mode == Admin:
    ask for Admin Access Code

    if code is correct:
        active_org_id = LIVE_ORG_ID
    else:
        active_org_id = DEMO_ORG_ID
```

Do not allow the user to manually type or select an organization ID.

Do not expose an organization dropdown.

Do not allow arbitrary organization switching.

---

## Org ID Propagation

Update the app so `active_org_id` is used consistently by all downstream flows:

```text
SQL analytics
Lead 360
Diagnostic analytics
POC chat history
```

Any current usage of:

```text
HERMON_DEFAULT_CLERK_ORG_ID
settings.default_org_id
```

should be reviewed.

The default org ID can remain as fallback, but runtime execution should use:

```text
active_org_id
```

---

## Chat History Behavior

POC chat history must be scoped by `active_org_id`.

This means:

```text
User mode history uses DEMO_ORG_ID.
Admin mode history uses LIVE_ORG_ID.
```

The histories must not mix.

If the user switches mode, the displayed/retrieved chat history should correspond to the newly selected `active_org_id`.

---

## Session Behavior

Default app load:

```text
Mode = User
active_org_id = DEMO_ORG_ID
```

If the app is refreshed, it should return to User mode unless Admin access is entered again.

Do not persist Admin access beyond the current Streamlit session unless explicitly required later.

---

## UI Text Requirements

Use neutral client-safe wording.

Allowed UI labels:

```text
Mode
User
Admin
Admin Access Code
Access: Standard
Access: Admin
Invalid admin access code. Continuing in User mode.
Admin access is not configured. Continuing in User mode.
```

Avoid UI labels:

```text
demo data
dummy data
fake data
test data
live org
client org id
organization id
password
```

---

## Security / Safety Rules

Never display:

```text
DEMO_ORG_ID
LIVE_ORG_ID
ADMIN_ACCESS_CODE
database URL
API keys
secrets
raw payloads
credentials
```

Never log `ADMIN_ACCESS_CODE`.

Never print secrets to Streamlit UI.

Never allow live/admin data unless:

```text
mode == Admin
and
entered_code == ADMIN_ACCESS_CODE
and
LIVE_ORG_ID is configured
```

If the access code is wrong, empty, or missing:

```text
active_org_id = DEMO_ORG_ID
```

---

## Expected Result

Base Streamlit link opens in `User` mode.

Client users can use the chatbot without entering any code.

The UI does not mention demo/dummy/test data.

Manager can select `Admin`, enter the `Admin Access Code`, and use the same chatbot against the admin/live organization.

If the access code is wrong, the app continues in `User` mode.

---

## Manual Test Cases

After implementation, test these cases.

### Test 1: Default User Mode

Steps:

```text
Open Streamlit app.
Do not select Admin.
Ask: Show monthly lead trend.
```

Expected:

```text
App uses DEMO_ORG_ID internally.
No access code required.
UI does not mention demo/dummy/test data.
```

### Test 2: Wrong Admin Code

Steps:

```text
Select Admin.
Enter wrong access code.
Ask: Show monthly lead trend.
```

Expected:

```text
App falls back to DEMO_ORG_ID.
Shows warning: Invalid admin access code. Continuing in User mode.
Does not reveal org IDs.
```

### Test 3: Correct Admin Code

Steps:

```text
Select Admin.
Enter correct Admin Access Code.
Ask: Show monthly lead trend.
```

Expected:

```text
App uses LIVE_ORG_ID internally.
Shows Access: Admin or Mode: Admin.
Does not reveal LIVE_ORG_ID.
```

### Test 4: Missing Admin Config

Steps:

```text
Remove or unset LIVE_ORG_ID or ADMIN_ACCESS_CODE.
Select Admin.
```

Expected:

```text
Admin mode does not unlock admin data.
App continues in User mode.
Shows safe configuration warning.
```

### Test 5: Chat History Separation

Steps:

```text
Ask a question in User mode.
Switch to Admin with correct code.
Check history.
```

Expected:

```text
User-mode and Admin-mode chat histories do not mix.
```

---

## Definition of Done

This task is complete when:

```text
Sidebar has User/Admin mode selector.
User mode is default.
User mode requires no access code.
Admin mode requires Admin Access Code.
Correct Admin Access Code switches active_org_id to LIVE_ORG_ID.
Wrong/missing Admin Access Code keeps active_org_id as DEMO_ORG_ID.
The UI does not mention demo/dummy/test/fake data.
Org IDs and secrets are never displayed.
active_org_id is used by SQL analytics, Lead 360, Diagnostic analytics, and POC chat history.
Chat histories are separated by active_org_id.
Manual test cases pass.
```
