#!/usr/bin/env python3
"""Round-trip test: every gen_hostile.py fixture's declared severity must match
the verdict the sanitizer actually produces, per decision table D3.

D3 maps detector verdicts to severities:
  exfil:   -> HIGH
  encoding:-> HIGH
  instruction: -> MEDIUM
  typoglycemia: -> MEDIUM
  (none)   -> CLEAN

A fixture whose severity disagrees with its own detector verdict means the
generator and the decision table have drifted apart -- the skill's checklist
claim ("severity == detector verdict for all 10 fixtures") would be false.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
VERDICT_SEVERITY = {
    "exfil": "high",
    "encoding": "high",
    "instruction": "medium",
    "typoglycemia": "medium",
}


def _detector_verdicts(text: str) -> set[str]:
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "sanitize.py"), "--check"],
        input=text, capture_output=True, text=True,
    )
    out = set()
    for line in r.stderr.splitlines():
        if line.startswith("FAIL: "):
            tag = line[len("FAIL: "):].split(":", 1)[0]
            out.add(tag)
    return out


def test_roundtrip_severity_matches_detector_verdict():
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "gen_hostile.py")],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    mismatches = []
    n = 0
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        n += 1
        verdicts = _detector_verdicts(obj["text"])
        if not verdicts:
            expected = "clean"
        else:
            expected = max((VERDICT_SEVERITY[v] for v in verdicts if v in VERDICT_SEVERITY),
                           default="clean", key=lambda s: {"clean": 0, "medium": 1, "high": 2}[s])
        if expected != obj["severity"]:
            mismatches.append((obj["name"], obj["severity"], sorted(verdicts), expected))
    assert n >= 8, f"expected at least 8 fixtures, got {n}"
    assert not mismatches, f"severity/verdict mismatches: {mismatches}"


if __name__ == "__main__":
    sys.exit(0)
