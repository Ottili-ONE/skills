# Worked examples — mcp-2026-07-28

Verified 2026-10-12. Good and bad output, with the detection signal for each.

## Good — discover-first client

```python
import os
from scripts.version_negotiate import negotiate

ALLOWED = ["2026-07-28", "2025-11-25", "2025-06-18"]
client_versions = os.environ.get("MCP_PROTOCOL_VERSION", "2026-07-28").split(",")
server_versions = discover()["supportedVersions"]          # server/discover (MUST)
agreed = negotiate(client_versions, server_versions)
if agreed is None:
    raise SystemExit("no common version; server returns -32022")
```

Detection signal: `scripts/version_negotiate.py --client ... --server ...` exits 0 and
prints `agreed <rev>`.

## Bad — hardcoded version

```python
VERSION = "2026-07-28"      # will go stale on the next revision
```

Detection signal: grep the codebase for the literal; every hit must sit behind a
config/env read. A hit in logic is a fail.

## Bad — assuming `tasks/result` exists

```python
await client.call("tasks/result", {"id": task_id})   # -32601 on 2026-07-28
```

Detection signal: any code calling `tasks/result` or `tasks/list` returns
`-32601` Method not found. Fix: poll with `tasks/get`, send input with `tasks/update`.

## Bad — shipping a 2025-06-18 server as-is

A 2026-07-28 client sends its first request with `_meta` and no `initialize`. The old
server waits for `initialize`, times out, and returns `-32603`.

Detection signal: the server log never saw an `initialize` call. Fix: run
`server/discover` first; if the server does not advertise `2026-07-28`, either upgrade
it or pin the client to the server's version in config — never in logic.

## Good — stateless replay proof

```bash
scripts/stateless_probe.py pair_a.json pair_b.json
# -> "1 0 0" and "PASS: replay identical, _meta complete, no session state"
```

Detection signal: identical `_meta`, identical `result`, no key containing `session`.

## Tasks extension — good vs bad

**Good:** tool returns `{"resultType": "task", "task": {"id": "t1", "status": "working"}}`;
client polls `tasks/get`; on `input_required` it sends `tasks/update` with
`inputResponses`.

**Bad:** blocking on a plain tool call for three minutes, or calling `tasks/result`.
