# Task 2 — Inbox Agent

Strict TypeScript/Express service. It sends email context to Task 1 over HTTP, drafts a reply using the configured LLM provider, validates the JSON draft, and returns it for human review. It never sends email automatically and does not duplicate Task 1 retrieval.

From this directory, install with `npm ci`, start with `npm run dev`, compile with `npm run build`, and run mocked tests with `npm test`. Configure the root `.env` with `LLM_PROVIDER=groq`, `GROQ_API_KEY`, and `GROQ_MODEL`; set `LLM_PROVIDER=mock` for fixed no-credit demo output that is not genuine AI inference. Task 1 must be reachable at `TASK1_BASE_URL` (default `http://localhost:8000`).

POST email JSON `{ "id": "...", "subject": "...", "body": "..." }` to `/draft`. The result remains `awaiting_human_approval` with `canSendAutomatically: false`. See the root [setup guide](../docs/SETUP.md) for account setup and troubleshooting.
Run: `npm install && npm run dev`. `POST /draft` expects `{ "id":"e1", "subject":"Question", "body":"..." }`.
All drafts require human approval. Feedback is logged but category-specific learning/autonomy rules remain to be implemented.
