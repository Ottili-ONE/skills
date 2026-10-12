# Tasks extension — `io.modelcontextprotocol/tasks`

Verified 2026-10-12 against SEP-2663 (raw HTTP 200) and SEP-1686 (raw HTTP 200).
Long-running tools are no longer a core feature. In 2026-07-28 they live in the
extension identified by `io.modelcontextprotocol/tasks`, available only to clients
that declare it in per-request `clientCapabilities.extensions`.

## What was removed from core
| Method | 2025-11-25 (SEP-1686, experimental) | 2026-07-28 |
|--------|--------------------------------------|------------|
| `tasks/result` | present | **removed** — returns `-32601` |
| `tasks/list` | present | **removed** — returns `-32601` |
| `tasks/get` | absent | **added** (extension) |
| `tasks/update` | absent | **added** (extension) |
| `tasks/cancel` | absent | **added** (extension) |

## The three extension methods

### `tasks/get`
Poll a running task. Returns the task object with a `status` from the machine
below. Idempotent; safe to call repeatedly.

### `tasks/update`
Client-to-server input for a task in `input_required` state. Carries
`inputResponses`. The server resumes and the task moves to `working` or
`completed`.

### `tasks/cancel`
Request cancellation. The task moves to `cancelled`; the original tool call's
response is still the task object, so the caller must check status.

## Task status machine
```
created -> working -> completed
                -> input_required -> (tasks/update) -> working -> ...
                -> failed
                -> cancelled
                -> suspended
```
- `created` -> server accepted the tool call but has not started work.
- `working` -> in flight. Poll with `tasks/get`.
- `input_required` -> a Multi Round-Trip Request. Respond with `tasks/update`.
- `completed`, `failed`, `cancelled`, `suspended` -> terminal.

## The `resultType` field on tool results
A long-running tool returns a result object carrying `resultType`:

| `resultType` | Meaning | Next step |
|--------------|---------|-----------|
| `"complete"` | ordinary result | use `result` directly |
| `"input_required"` | MRTR | send `tasks/update` with `inputResponses` |
| `"task"` | Tasks extension | poll with `tasks/get` |

A tool that returns no `resultType` is a short tool — block on it normally.

## Ordered procedure
1. Declare `io.modelcontextprotocol/tasks` in per-request `clientCapabilities.extensions`.
2. Confirm the server advertised it in `server/discover.capabilities.extensions`.
3. Call the tool. If the result carries `resultType: "task"`, read `task.id`.
4. Poll `tasks/get` until status is terminal.
5. On `input_required`, send `tasks/update` with `inputResponses`; resume polling.
6. On `cancelled` or `failed`, read `task.error` if present; do not retry blindly.

## Thresholds and constants
| Parameter | Value | Source |
|-----------|-------|--------|
| Extension identifier | `io.modelcontextprotocol/tasks` | SEP-2663 |
| Poll interval | start 250 ms, double each attempt, cap 5 s | convention |
| Max poll attempts | 60 before treating as `suspended` | convention |
| `resultType` values | `complete`, `input_required`, `task` | 2026-07-28 changelog |

## Near-miss triggers
- Calling `tasks/result` -> `-32601`. It was removed; use `tasks/get`.
- Assuming tasks is core -> it is an extension; the server may not have it.
- Polling without declaring the extension -> `-32021` MissingRequiredClientCapability.
- Blocking on a tool that returns `resultType: "task"` -> you wait forever.
- Treating `input_required` as an error -> it is a legitimate MRTR; respond, do not abort.
