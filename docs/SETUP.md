# Setup And Smoke Tests

## Prerequisites And Groq Key

Install Python 3.11+ and Node.js 20+. Create/sign in to a Groq account at [console.groq.com](https://console.groq.com/), then create an API key in the console's API Keys page. Keep the key private.

At the repository root, copy `.env.example` to `.env` only if `.env` does not already exist. Otherwise edit the existing file and preserve any valid local values. Set:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

The model catalog and account-specific limits are published at [Groq models](https://console.groq.com/docs/models) and [Groq rate limits](https://console.groq.com/docs/rate-limits). `openai/gpt-oss-20b` appeared in the catalog and Free Plan Limits table when this integration was implemented. Check your account for current availability and quotas before relying on it.

## Install

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `.env` and replace the placeholder API key. On macOS/Linux, activate with `source .venv/bin/activate` and copy the file with `cp .env.example .env`.

Install Task 2 dependencies and lockfile from its directory:

```powershell
cd task2-inbox-agent
npm ci
```

## Start Services

Run each command in its own terminal. Task 1 and Task 3 commands run from the repository root.

1. Task 1 API: `uvicorn task1_knowledge_brain.app:app --reload --port 8000`
2. Task 1 ingestion, in a second root terminal: `python -m task1_knowledge_brain.ingest`
3. Task 2 inbox API, from `task2-inbox-agent`: `npm run dev`
4. Task 3 workflow, from root: `python -m task3_meeting_scope.cli examples/meeting_1.txt --output outputs/proposal.json`

Task 1 docs are at <http://localhost:8000/docs>. Ingestion may take time and accesses the public help center; it does not call the LLM.

## Test Each Task

Run mocked automated tests from root with `python -m pytest`. In `task2-inbox-agent`, run `npm test` and `npm run build`. These tests do not require a Groq key or consume API credits.

Task 1 query smoke test (PowerShell):

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/query -ContentType 'application/json' -Body '{"question":"How do I update my account settings?","top_k":5}'
```

Task 2 draft smoke test (Task 1 and Task 2 must both be running):

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:3000/draft -ContentType 'application/json' -Body '{"id":"demo-1","subject":"Account settings","body":"How can I update my account settings?"}'
```

The response remains a draft with `status=awaiting_human_approval` and `canSendAutomatically=false`. Task 3 writes structured output to `outputs/proposal.json`; proposals require approval.

## No-Credit Demo Mode

Set `LLM_PROVIDER=mock` in `.env` and restart the services. Fixed demo output is explicitly marked as mock and is not genuine AI inference. The inbox draft is still human-review-only. Task 1 uses its regular retrieval/no-evidence behavior, and Task 3 still calls Task 1 over HTTP. Ingestion remains a separate network operation.

## Troubleshooting

- Invalid API key: check `GROQ_API_KEY` in the root `.env`, remove accidental surrounding quotes/spaces, and create a replacement key in Groq. Never paste the key into logs or issue reports.
- Rate limit: check current Free Plan Limits in Groq's console, reduce request frequency, or retry after the window resets. The service maps rate-limit responses to HTTP 429.
- Model not found or unavailable: verify the exact `GROQ_MODEL` ID in the current model catalog and that the account can access it.
- Connection/timeouts: confirm network access to Groq and that Task 1 is running. LLM requests time out after 30 seconds.
- Knowledge Brain errors: start Task 1 before calling Task 2 or Task 3. If `/query` has no relevant indexed chunks, Task 1 returns a human-review fallback rather than inventing an answer.

Never commit `.env`. The starter still needs broader evaluation coverage, scheduled refresh, authentication, and image/screenshot understanding before production use.
