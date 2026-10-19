# Task 3 — Meeting to Scope of Work

Sequential workflow: requirements analyst, Task 1 knowledge lookup, solution architect, estimator, proposal writer, and optional scope-change analyst. Model JSON is validated at every stage; invalid output stops the workflow instead of passing malformed data downstream. Unresolved information is explicit, estimate ranges are checked, and approval flags are enforced.

From the repository root, install Python dependencies with `python -m pip install -r requirements.txt`. Run `python -m task3_meeting_scope.cli examples/meeting_1.txt --output outputs/proposal.json`; Task 1 must be available. Configure the root `.env` with the Groq variables, or set `LLM_PROVIDER=mock` for labeled deterministic demo data that is not genuine AI inference. Outputs always require human approval.

See [setup and smoke tests](../docs/SETUP.md). This Groq path is for experimentation and does not meet the original assessment requirement that Claude be central.
