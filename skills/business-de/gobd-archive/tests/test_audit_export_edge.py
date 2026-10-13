"""Edge cases: a raw DB dump must not pass as an audit export."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "audit_export.py"


def run(args):
    r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    blob = (r.stdout + r.stderr).strip()
    return r.returncode, (json.loads(blob) if blob else {"ok": False, "error": "no output"})


def test_manifest_lists_original_files_not_db_dump(tmp_path):
    """A directory of raw .sql/.db dumps is *not* a valid audit export source
    because audit_export.py only copies files and emits a manifest; it does
    not turn a DB dump into a chronological, checksummed export."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "backup.sql").write_text("DROP TABLE bookings;")
    (src / "ledger.db").write_bytes(b"sqlite format 3")
    out = tmp_path / "out"
    code, out_json = run(["--source", str(src), "--output", str(out), "--year", "2026"])
    assert code == 0 and out_json["ok"]
    # the script happily copies the dump, but the manifest records no
    # chronological/checksummed export semantics — the *agent* must reject it
    manifest = json.loads((out / "MANIFEST.json").read_text())
    names = [f["file"] for f in manifest["files"]]
    assert "backup.sql" in names and "ledger.db" in names
    assert manifest["format"] == "original-files-plus-manifest"


def test_verify_catches_tampered_export(tmp_path):
    """Export once, then tamper the exported copy in place and re-verify the
    manifest directly (the CLI re-exports from source, so the tamper check is
    done against the existing manifest)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("audit_export", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    src = tmp_path / "src"
    src.mkdir()
    (src / "inv.xml").write_text("<x/>")
    out = tmp_path / "out"
    mod.export(src, out, 2026, "2026-10-08")
    (out / "inv.xml").write_text("<y/>")  # in-place modification of the export
    res = mod.verify_export(out, "2026-10-08")
    assert res["ok"] is False
    assert any("checksum" in m for m in res["mismatches"])
