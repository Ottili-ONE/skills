"""Tests for scripts/eval_metrics.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "eval_metrics.py"
EVALS = ROOT / "fixtures" / "sample_evals.json"
FIRINGS = ROOT / "fixtures" / "sample_firings.txt"


EVALS_DATA = json.loads(EVALS.read_text(encoding="utf-8"))


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True,
    )


def test_perfect_scores_pass():
    r = run("metrics", str(EVALS), str(FIRINGS))
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stderr
    assert "1 0 0" in r.stdout


def test_json_output_shape():
    r = run("metrics", str(EVALS), str(FIRINGS), "--json")
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["precision"] == 1.0
    assert data["recall"] == 1.0
    assert data["pass"] is True
    assert data["target_precision"] == 0.9
    assert data["target_recall"] == 0.9
    assert len(data["cases"]) == 9


def test_low_recall_fails():
    firings = FIRINGS.with_suffix(".miss.txt")
    firings.write_text("\n".join(
        f"{e} 0" for e in ["E1", "E2", "E3", "E4", "E5", "E6"]
    ) + "\n", encoding="utf-8")
    try:
        r = run("metrics", str(EVALS), str(firings))
        assert r.returncode == 1
        assert "FAIL" in r.stderr
        assert "recall" in r.stderr.lower()
    finally:
        firings.unlink(missing_ok=True)


def test_broad_description_fails_precision():
    firings = FIRINGS.with_suffix(".broad.txt")
    firings.write_text("\n".join(
        f"{e} 1" for e in ["E1", "E2", "E3", "E4", "E5", "E6", "N1", "N2", "N3"]
    ) + "\n", encoding="utf-8")
    try:
        r = run("metrics", str(EVALS), str(firings))
        assert r.returncode == 1
        assert "precision" in r.stderr.lower()
    finally:
        firings.unlink(missing_ok=True)


def test_missing_firing_record_counts_as_miss():
    firings = FIRINGS.with_suffix(".gap.txt")
    body = "\n".join(
        line for line in FIRINGS.read_text().splitlines() if not line.startswith("E1 ")
    )
    firings.write_text(body + "\n", encoding="utf-8")
    try:
        r = run("metrics", str(EVALS), str(firings))
        assert r.returncode == 1
        assert "FAIL" in r.stderr
    finally:
        firings.unlink(missing_ok=True)


def test_bad_firing_line_format():
    bad = FIRINGS.with_suffix(".malformed.txt")
    bad.write_text("E1 notabool\n", encoding="utf-8")
    try:
        r = run("metrics", str(EVALS), str(bad))
        assert r.returncode == 2
        assert "FAIL" in r.stderr
    finally:
        bad.unlink(missing_ok=True)


def test_evals_json_must_be_list(tmp_path):
    ev = tmp_path / "bad.json"
    ev.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    r = run("metrics", str(ev), str(FIRINGS))
    assert r.returncode == 2


def test_delta_identical_output_fails(tmp_path):
    w = tmp_path / "with"
    b = tmp_path / "without"
    w.mkdir()
    b.mkdir()
    (w / "E1.txt").write_text("same answer\n", encoding="utf-8")
    (b / "E1.txt").write_text("same answer\n", encoding="utf-8")
    r = run("delta", str(w), str(b))
    assert r.returncode == 1
    assert "identical to baseline" in r.stderr


def test_delta_changed_output_passes(tmp_path):
    w = tmp_path / "with"
    b = tmp_path / "without"
    w.mkdir()
    b.mkdir()
    (w / "E1.txt").write_text("a much longer answer than the baseline\n", encoding="utf-8")
    (b / "E1.txt").write_text("no\n", encoding="utf-8")
    r = run("delta", str(w), str(b))
    assert r.returncode == 0
    assert "PASS" in r.stderr


def test_delta_missing_side_fails(tmp_path):
    w = tmp_path / "with"
    b = tmp_path / "without"
    w.mkdir()
    b.mkdir()
    (w / "E1.txt").write_text("x\n", encoding="utf-8")
    (b / "E2.txt").write_text("y\n", encoding="utf-8")
    r = run("delta", str(w), str(b))
    assert r.returncode == 1
    assert "missing from one side" in r.stderr


def test_split_missing_field_fails(tmp_path):
    ev = tmp_path / "no_split.json"
    ev.write_text(json.dumps(EVALS_DATA), encoding="utf-8")
    r = run("split", str(ev))
    assert r.returncode == 1
    assert "split" in r.stderr.lower()


def test_split_both_splits_pass(tmp_path):
    ev = tmp_path / "split.json"
    data = [
        {**EVALS_DATA[0], "split": "train"},
        {**EVALS_DATA[1], "split": "val"},
    ]
    ev.write_text(json.dumps(data), encoding="utf-8")
    r = run("split", str(ev))
    assert r.returncode == 0
    assert "PASS" in r.stderr


