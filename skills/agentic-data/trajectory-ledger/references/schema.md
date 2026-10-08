# Trajectory schema — trajectory-ledger

One JSON object per line (JSONL). Every event has the fields below; `step`,
`timestamp`, `type`, `state_hash` are mandatory on every line.

```json
{
  "schema": "trajectory-ledger-v1",
  "run_id": "uuid",
  "step": 0,
  "timestamp": "2026-10-09T12:00:00Z",
  "type": "think",
  "thought": "planning the next tool call",
  "state_hash": "sha256:...",
  "cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}
}
```

`type` is one of `think`, `tool`, `observe`. A `tool` event also carries:

```json
{
  "type": "tool",
  "tool": "shell",
  "args": {"cmd": "ls -la"},
  "result": {"exit_code": 0, "stdout": "...", "stderr": ""},
  "state_hash": "sha256:...",
  "cost": {"tokens_in": 120, "tokens_out": 40, "seconds": 1.2, "usd": 0.0003}
}
```

An `observe` event carries the new state:

```json
{
  "type": "observe",
  "state": {"files": ["a.txt"], "env": {"k": "v"}},
  "state_hash": "sha256:...",
  "cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}
}
```

Terminal events carry an `outcome`:

```json
{"outcome": "succeeded", "evidence": "output.json written with status ok"}
```

`outcome` is one of `pending`, `running`, `succeeded`, `failed`, `blocked`,
`timeout`. `succeeded` requires `evidence`; `failed` requires `reason`;
`blocked` requires `blocker`; `timeout` requires `elapsed_seconds`.
