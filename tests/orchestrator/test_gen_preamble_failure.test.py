"""Golden-file + failure-path tests for scripts/gen-preamble.mjs (TASK-0004).

The golden file is the source of truth: the committed preamble.md must match
tests/golden/preamble.md byte-for-byte. The golden file is NEVER auto-updated;
a diff is a regression that a human must review.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GEN = REPO / "scripts" / "gen-preamble.mjs"
OUT = REPO / "skills" / "orchestrator-preamble" / "orchestrator-preamble" / "references" / "preamble.md"
GOLDEN = Path(__file__).resolve().parent / "golden" / "preamble.md"
NODE = shutil.which("node") or sys.executable


def run(args, check=True):
    return subprocess.run([NODE, str(GEN), *args], cwd=REPO, capture_output=True, text=True, check=check)


def test_golden_file_matches_committed_body_byte_for_byte():
    assert OUT.read_text() == GOLDEN.read_text()


def test_golden_file_is_not_a_symlink_and_is_regular():
    assert GOLDEN.is_file()
    assert not GOLDEN.is_symlink()


def test_golden_file_has_a_fixed_header_and_four_rules():
    text = GOLDEN.read_text()
    assert text.startswith("# Orchestrator Preamble (generated)")
    for i in range(1, 5):
        assert text.startswith(f"{i}. "), f"rule {i} missing"


def test_generator_refuses_when_a_canonical_skill_is_missing():
    """If a canonical skill is deleted the generator must fail (exit 1), not emit."""
    target = REPO / "skills" / "engineering" / "honest-status"
    backup_dir = REPO / ".truth" / "SKL-W1-02" / "honest-status-backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    moved = False
    try:
        os.replace(target, backup_dir)
        moved = True
        r = run([], check=False)
        assert r.returncode != 0, "generator must fail when a canonical skill is missing"
    finally:
        if moved:
            os.replace(backup_dir, target)


def test_generator_refuses_when_a_canonical_skill_loses_its_gate_command():
    """If a canonical skill's SKILL.md no longer contains the gate command the
    generator must fail (exit 1), keeping the committed body stale-safe."""
    target = REPO / "skills" / "engineering" / "honest-status" / "SKILL.md"
    backup = target.read_text()
    target.write_text(backup.replace("python3 scripts/check_status_evidence.py", "python3 scripts/DELETED_GATE.py"))
    try:
        r = run([], check=False)
        assert r.returncode != 0, "generator must fail when a gate command is absent"
    finally:
        target.write_text(backup)


def test_check_passes_after_a_fresh_generation():
    """Regenerate, then --check must pass (round-trip property)."""
    run([])
    r = run(["--check"])
    assert r.returncode == 0
    assert "up to date" in r.stdout
