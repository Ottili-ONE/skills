"""Tests for scripts/gen_fixtures.py (offline, deterministic)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "gen_fixtures.py"


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def test_generates_all_fixtures() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "fx"
        r = run("--out", str(out))
        assert r.returncode == 0, r.stderr
        assert "PASS: fixtures written" in r.stderr
        for name in ("SPEC.md", "contract.json", "contract_broken.json",
                     "checks.json", "checks_neutered.json"):
            assert (out / name).is_file(), name
        for agent in ("good", "broken", "lazy"):
            assert (out / agent).is_dir(), agent
        assert (out / "good" / "output.json").is_file()
        assert not (out / "broken" / "output.json").exists()
        assert not (out / "broken" / "summary.md").exists()
        assert not (out / "lazy" / "summary.md").exists()


def test_rejects_existing_output_dir() -> None:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "fx"
        out.mkdir()
        r = run("--out", str(out))
        assert r.returncode == 1
        assert "already exists" in r.stderr


def test_good_agent_passes_harness() -> None:
    """Generated good fixtures must pass the shipped verify_harness.py."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("vh", ROOT / "scripts" / "verify_harness.py")
    assert spec is not None and spec.loader is not None
    vh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vh)

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "fx"
        run("--out", str(out))
        contract = vh.load_contract(out / "contract.json")
        assert vh.assert_contract(contract) == []
        checks = vh.load_checks(out / "checks.json")
        good, total, _ = vh.run_checks(checks, out / "good")
        broken, _, _ = vh.run_checks(checks, out / "broken")
        lazy, _, _ = vh.run_checks(checks, out / "lazy")
        assert vh.pass_rate(good, total) == 1.0
        assert vh.pass_rate(broken, total) == 0.0
        assert vh.pass_rate(lazy, total) < vh.pass_rate(good, total)


def test_neutered_check_drops_power() -> None:
    """Flipping a check to always-pass must drop the discriminating power."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("vh2", ROOT / "scripts" / "verify_harness.py")
    assert spec is not None and spec.loader is not None
    vh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vh)

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "fx"
        run("--out", str(out))
        good_checks = vh.load_checks(out / "checks.json")
        neutered = vh.load_checks(out / "checks_neutered.json")
        good, total, _ = vh.run_checks(good_checks, out / "good")
        lazy, _, _ = vh.run_checks(good_checks, out / "lazy")
        power_full = vh.pass_rate(good, total) - vh.pass_rate(lazy, total)
        # neutered checks have no content assertions, so the lazy agent passes them
        g2, t2, _ = vh.run_checks(neutered, out / "good")
        l2, _, _ = vh.run_checks(neutered, out / "lazy")
        power_neutered = vh.pass_rate(g2, t2) - vh.pass_rate(l2, t2)
        assert power_neutered < power_full, (power_full, power_neutered)
