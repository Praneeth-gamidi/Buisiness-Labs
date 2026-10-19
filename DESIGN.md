# DESIGN
## Problem
Help a software/service company scale knowledge retrieval, customer support replies, and meeting scoping without losing correctness.
## Selected features
Shared knowledge API; semantic search; citations; expert feedback; email drafts; multi-agent scoping; estimates; follow-up scope diff; mandatory human approval.
## Deferred
Production email-provider integration, auto-send, complete screenshot understanding, multi-tenant auth, robust incremental crawl, production job queue. Explain these as limitations, not completed features.
## Risks
Crawling can fail; HTML changes; retrieval misses evidence; model returns invalid JSON; estimates are uncertain; downstream tasks fail if Task 1 is offline.
## Next
Incremental crawler with safe deletion reconciliation; image extraction and vision evaluation; structured schema validation; authentication; reproducible eval runner.
