# BusinessLabs AI Tech Consultant

Three connected components: Task 1 is a FastAPI/ChromaDB knowledge service, Task 2 drafts inbox replies in TypeScript, and Task 3 turns meeting transcripts into structured scopes, estimates, proposals, and optional change reports. Tasks 2 and 3 use Task 1 over HTTP; retrieval, embeddings, SQLite feedback, citations, and human approval remain part of the workflow.

## Provider And Assessment

This working configuration uses Groq for LLM experimentation. The original BusinessLabs assessment brief recorded in the starter documentation requires Claude to be the central model. This Groq configuration does **not** satisfy that original requirement; restore a Claude adapter or run a measured provider comparison before presenting it as assessment-compliant. The Python and TypeScript provider adapters isolate provider calls so another adapter can be added without changing the task workflows.

The default model is `openai/gpt-oss-20b`, listed in Groq's model catalog and Free Plan Limits documentation when this change was made. Account availability and quotas can change; verify the model in your account at [Groq models](https://console.groq.com/docs/models) and [Groq rate limits](https://console.groq.com/docs/rate-limits).

## Setup

Requirements: Python 3.11+, Node.js 20+, and (for live inference) a Groq account and API key.

1. Create or sign in to a Groq account at [console.groq.com](https://console.groq.com/), then create an API key from the API Keys page. Copy it once into your local `.env`; never commit or share it.
2. Copy `.env.example` to `.env` only if `.env` does not already exist; otherwise preserve and edit your local file. Configure `LLM_PROVIDER=groq`, `GROQ_API_KEY`, and `GROQ_MODEL` as shown there. The example key is a placeholder only.
3. At the repository root, create and activate Python, then install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

   macOS/Linux activation: `source .venv/bin/activate`.
4. Start Task 1 from the repository root: `uvicorn task1_knowledge_brain.app:app --reload --port 8000`. In a second root terminal, ingest documentation with `python -m task1_knowledge_brain.ingest`.
5. Start Task 2 in another terminal: `cd task2-inbox-agent`, `npm ci`, `npm run dev`.
6. Run Task 3 from the repository root: `python -m task3_meeting_scope.cli examples/meeting_1.txt --output outputs/proposal.json`.

Task 1 API docs: <http://localhost:8000/docs>. Detailed setup and smoke tests are in [docs/SETUP.md](docs/SETUP.md).

## Tests

From the root, run `python -m pytest`. For Task 2, run `cd task2-inbox-agent`, `npm test`, and `npm run build`. All provider tests use mocked responses and do not consume Groq credits.

Set `LLM_PROVIDER=mock` in `.env` to exercise provider-backed workflows without API calls. Mock responses are deterministic demo data, are labeled as mock output, and are not genuine AI results. Task 1's no-evidence fallback remains a human-review response; ingestion still fetches public docs.

## Honest Status

This is still an assessment starter, not a finished capstone. The original brief calls for at least 20 evaluations per task, measured provider comparisons, 50 realistic inbox examples, and meeting role-plays. Do not fabricate metrics. Human review is required before sending emails or proposals.
