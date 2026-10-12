# EVALS — problem-json-contracts

Each prompt lists expected behaviour and failure signs.

- **E1 — envelope detection.** Prompt: "My endpoint returns `{"status": 404, "detail": "missing"}` with HTTP 200. Is this acceptable?" Expected: no — the HTTP status must be 404 and `status` must equal it. Failure sign: agent accepts the envelope.
- **E2 — type URI absoluteness.** Prompt: "Can I use `type: "user-not-found"`?" Expected: no — must be an absolute URI (`https://api.ottili.dev/problems/user-not-found`) or `about:ottili:users:not-found`. Failure sign: agent approves a bare string.
- **E3 — 5xx leakage.** Prompt: "My 503 includes `stack_trace` and `db_connection_string`." Expected: no — 5xx carries `trace_id` only. Failure sign: agent says "it's fine for internal services".
- **E4 — retry_after presence.** Prompt: "Which errors need `retry_after`?" Expected: 429 and 503 (and any retriable 5xx). Failure sign: agent omits it on 503.
- **E5 — catalogue drift.** Prompt: "I added a code to the catalogue but forgot the schema entry." Expected: `scripts/check_problem_catalogue.py` exits 1. Failure sign: agent says "CI will catch it later".
- **E6 — duplicate status.** Prompt: "Two codes both map to 409." Expected: flagged as drift; give each a distinct type URI and, where possible, a distinct status. Failure sign: agent says "409 is fine for both".
- **E7 — field length.** Prompt: "My `title` is 200 chars." Expected: rejected — schema caps `title` at 120, `detail` at 500. Failure sign: agent accepts it.
