"""Regenerate trajectory-ledger test fixtures.

`traj.jsonl` is the canonical good trajectory (3 events, grounded, replayable).
`traj_cost.jsonl` is the same run with a non-zero USD cost so the budget gates
can be exercised against a real overrun. Both are hand-written, deterministic
and offline.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

TRAJ = [
    {"schema": "trajectory-ledger-v1", "step": 0, "timestamp": "2026-10-09T12:00:00Z",
     "type": "think", "state": {"files": []}, "cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}},
    {"schema": "trajectory-ledger-v1", "step": 1, "timestamp": "2026-10-09T12:00:01Z",
     "type": "tool", "tool": "shell", "args": {"cmd": "ls -la"},
     "result": {"exit_code": 0, "stderr": "", "stdout": "x"},
     "state": {"files": ["x"]}, "cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.1, "usd": 0.0}},
    {"schema": "trajectory-ledger-v1", "step": 2, "timestamp": "2026-10-09T12:00:02Z",
     "type": "observe", "outcome": "succeeded", "evidence": "x written",
     "state": {"files": ["x"]}, "cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}},
]

TRAJ_COST = [
    {"schema": "trajectory-ledger-v1", "step": 0, "timestamp": "2026-10-09T12:00:00Z",
     "type": "think", "state": {"files": []}, "cost": {"tokens_in": 100, "tokens_out": 50, "seconds": 0.5, "usd": 0.05}},
    {"schema": "trajectory-ledger-v1", "step": 1, "timestamp": "2026-10-09T12:00:01Z",
     "type": "tool", "tool": "shell", "args": {"cmd": "ls -la"},
     "result": {"exit_code": 0, "stderr": "", "stdout": "x"},
     "state": {"files": ["x"]}, "cost": {"tokens_in": 200, "tokens_out": 100, "seconds": 1.5, "usd": 0.10}},
    {"schema": "trajectory-ledger-v1", "step": 2, "timestamp": "2026-10-09T12:00:02Z",
     "type": "observe", "outcome": "succeeded", "evidence": "x written",
     "state": {"files": ["x"]}, "cost": {"tokens_in": 50, "tokens_out": 25, "seconds": 0.25, "usd": 0.025}},
]


def main() -> int:
    import hashlib
    for name, rows in (("traj", TRAJ), ("traj_cost", TRAJ_COST)):
        for r in rows:
            if "state" in r and "state_hash" not in r:
                body = json.dumps(r["state"], sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                r["state_hash"] = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
        (OUT / f"{name}.jsonl").write_text(
            "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows),
            encoding="utf-8",
        )
        print(f"{name}.jsonl: {len(rows)} events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
