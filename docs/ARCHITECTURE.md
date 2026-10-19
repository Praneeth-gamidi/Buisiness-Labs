# Architecture
```text
Sitemap -> Task 1 crawler -> extraction/chunking -> ChromaDB
                                      |             |
                                    SQLite          v
User -> Task 1 FastAPI /query -> top-k retrieval -> configured LLM -> answer + sources
                  ^                                      |
                  +---------- /feedback expert ----------+
Customer email -> Task 2 TypeScript -> Task 1 API -> configured LLM -> validated draft -> human approval
Meeting transcript -> Task 3 Python agents -> Task 1 API -> validated scope -> estimate -> proposal -> approval
```
Task 1 remains the shared knowledge service. Task 2 and 3 call its API, never copy its retrieval implementation. Python and TypeScript each have a small provider adapter configured by `LLM_PROVIDER`; `groq` is the real provider and `mock` is deterministic demo output, not inference. Task 1 sends only retrieved top-k context to generation. The `all-MiniLM-L6-v2` embedding model remains independent of the LLM provider.

This branch selects Groq for cost experimentation, but the original assessment requirement makes Claude central. Groq-only evaluation does not meet that criterion; a Claude adapter/provider comparison is still required for assessment compliance.
