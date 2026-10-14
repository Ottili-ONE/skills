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

## server/discover — good vs bad

**Good:** client calls `server/discover` first, reads `supportedVersions`,
intersects with its own vendored list, agrees on the highest common version,
and stores it in config. On empty intersection it refuses with `-32022`.

```python
result = call("server/discover", {}, meta=meta)
agreed = negotiate(client_versions, result["result"]["supportedVersions"])
if agreed is None:
    raise SystemExit("-32022: no common version")
config.revision = agreed            # config, never a literal in logic
```

**Bad:** skipping discover and hardcoding `"2026-07-28"`. The next revision
ships and the client keeps talking a removed revision. Detection: grep for the
literal; every hit must sit behind a config/env read.

**Bad:** a discover response whose `capabilities.tasks` advertises
`tasks/result`. Detection: `scripts/protocol_check.py` prints
`FAIL: capabilities advertises tasks/result, which was removed in 2026-07-28`.

## per-request `_meta` — good vs bad

**Good:** every request, including `tasks/get` polls, carries
`protocolVersion`, `clientInfo`, `clientCapabilities`. Detection: the request
log shows `_meta` on every line.

**Bad:** sending `_meta` only on the first request. Detection: the second request
returns `-32021` MissingRequiredClientCapability. Per-request means per-request.

## Tasks extension — full worked example

A tool that generates a report takes three minutes.

1. Client declares `io.modelcontextprotocol/tasks` in `clientCapabilities.extensions`
   and confirms the server advertised it in `server/discover`.
2. Call the tool. Response:
   ```json
   {"resultType": "task", "task": {"id": "t1", "status": "working"}}
   ```
3. Poll `tasks/get` with id `t1` every 250 ms (doubling to a 5 s cap).
4. The server responds `{"status": "input_required", "question": "Which quarter?"}`.
5. Client sends `tasks/update` with `{"id": "t1", "inputResponses": ["Q3"]}`.
6. Status returns to `working`, then `completed` with the report in `task.result`.

Detection signal: no blocking on the plain tool call; no call to `tasks/result`;
`input_required` is handled, not treated as an error.

## Good — OAuth discovery-first client

```python
import httpx

def obtain_token(server_url: str, client_id: str, code_verifier: str) -> str:
    # 1. discover (never hardcode an issuer)
    disc = httpx.post(server_url + "/mcp", json={"jsonrpc": "2.0", "id": 1,
        "method": "server/discover", "params": {}}).json()
    as_url = disc["result"]["capabilities"]["authorization"]["authorizationServers"][0]

    # 2. metadata document is the contract
    meta = httpx.get(f"{as_url}/.well-known/client-id-metadata").json()
    assert client_id == meta["client_id"], "client_id must match the metadata document"

    # 3. validate iss before redeeming (RFC 9207 / SEP-2468)
    token_resp = httpx.post(meta["token_endpoint"], data={
        "grant_type": "authorization_code", "code_verifier": code_verifier,
        "client_id": client_id, "redirect_uri": meta["redirect_uris"][0]})
    iss = token_resp.json().get("iss")
    assert iss == as_url, "issuer mismatch — re-run discovery, never reuse creds"
    return token_resp.json()["access_token"]
```

Detection signal: a client that fetches the metadata document and asserts `iss`
before redeeming is correct; one that hardcodes `client_id` + `token_endpoint` is not.

## Bad — DCR for a new client

```python
# WRONG: Dynamic Client Registration is deprecated since 2026-07-28 (PR #2858).
# It still works for legacy ASes, so the failure is silent, not an error.
httpx.post(as_url + "/register", json={
    "client_name": "my-agent", "redirect_uris": ["https://agent/cb"],
    "token_endpoint_auth_method": "none"})
```

Detection signal: grep for `/register` or `DynamicClientRegistration`; any hit in
new client code is a deprecation warning, not a bug. Use the Client ID Metadata
Document at `/.well-known/client-id-metadata` instead.

## Good — tasks extension, poll loop

```python
def run_long_tool(client, tool_name: str, args: dict) -> dict:
    res = client.call(tool_name, args)          # may carry resultType
    if res.get("resultType") == "task":
        task_id = res["task"]["id"]
        while True:
            t = client.call("tasks/get", {"id": task_id})
            if t["status"] in ("completed", "failed", "cancelled", "suspended"):
                return t
            time.sleep(t.get("pollIntervalSeconds", 5))
    if res.get("resultType") == "input_required":
        answer = ask_human(res["inputRequired"])
        return client.call("tasks/update", {"id": res["task"]["id"],
                                             "inputResponses": [answer]})
    return res  # "complete" or absent -> short tool
```

Detection signal: the loop calls `tasks/get` and handles `input_required` via
`tasks/update`. A loop calling `tasks/result` (removed in 2026-07-28) is wrong.

## Bad — silent version downgrade

```python
# WRONG: picking the *lowest* common version to "maximise compatibility"
agreed = min(client_versions & server_versions)   # weakens security, loses server/discover
```

Detection signal: `version_negotiate.py --client ... --server ...` must print the
**highest** common version. `min()` in negotiation code is a fail.
