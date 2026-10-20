"""Contract tests for ``scripts/install.sh`` (SKL-W1-01, TASK-0003).

``scripts/install.sh`` is the only way a skill reaches an agent. It publishes a
machine-readable result: the versioned contract
``ottili.skills.install-manifest/v1``.

What these tests hold:

* the interface is complete: ``--help`` names every flag, every exit code and
  the contract id, and ``--version`` prints the contract id,
* the published manifest matches the contract: it validates against the
  committed JSON Schema and against the typed (pydantic) view, and the two
  views never drift apart,
* the manifest describes what really happened: the installed folders, the
  source folders and the actions match the state of the target directory,
* the failure modes are the documented ones: an unresolvable skill or package
  exits 1, a usage error exits 2, and both are reported in the manifest,
* every shell function documents its inputs, its outputs and its failure
  modes.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
INSTALL = ROOT / "scripts" / "install.sh"
MANIFEST_LIB = ROOT / "scripts" / "lib" / "install-manifest.sh"

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from ottili_contracts import (  # noqa: E402
    CONTRACT_INSTALL_MANIFEST,
    load_example,
    load_schema,
    model_for,
    schema_path,
)
from ottili_contracts.generate import render_schema  # noqa: E402

FUNCTION_RE = re.compile(r"^([a-z_][a-z0-9_]*)\(\) \{", re.MULTILINE)


def run_install(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the installer and capture its output.

    Inputs:
        args: the command line arguments of the installer.
    Outputs:
        the completed process.
    Failure modes:
        none. A non-zero exit code is the tool's answer, not an error here.
    """
    return subprocess.run(
        ["bash", str(INSTALL), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def engineering_skills() -> list[str]:
    """The skill names of the engineering package.

    Inputs:
        none.
    Outputs:
        the sorted skill folder names of ``skills/engineering/``.
    Failure modes:
        none, an empty package yields an empty list.
    """
    package = ROOT / "skills" / "engineering"
    return sorted(
        path.name for path in package.iterdir() if (path / "SKILL.md").is_file()
    )


def test_the_help_text_names_every_flag_and_exit_code() -> None:
    """--help is the contract of the command line: it must be complete."""
    result = run_install("--help")
    assert result.returncode == 0, result.stdout + result.stderr
    for needle in (
        "--target",
        "--package",
        "--check",
        "--dry-run",
        "--force",
        "--link",
        "--json",
        "--version",
        "Exit codes:",
        "0  every requested skill",
        "1  a skill or a package could not be resolved",
        "2  usage error",
        CONTRACT_INSTALL_MANIFEST,
    ):
        assert needle in result.stdout, f"--help does not mention {needle!r}:\n{result.stdout}"


def test_the_version_prints_the_contract_id() -> None:
    """--version tells the consumer which contract the tool publishes."""
    result = run_install("--version")
    assert result.returncode == 0
    assert CONTRACT_INSTALL_MANIFEST in result.stdout


def test_the_manifest_describes_the_installed_skills(tmp_path: Path) -> None:
    """The manifest names every installed skill and what happened to it."""
    target = tmp_path / "target"
    result = run_install("--target", str(target), "--package", "engineering", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == "", "the JSON mode keeps stdout clean and stderr empty"
    manifest = json.loads(result.stdout)
    assert manifest["contract"] == CONTRACT_INSTALL_MANIFEST
    assert manifest["mode"] == "install"
    assert manifest["ok"] is True
    assert manifest["error"] is None
    assert manifest["target"] == str(target)
    assert manifest["link"] is False
    jsonschema.validate(manifest, load_schema(CONTRACT_INSTALL_MANIFEST))
    validated = model_for(CONTRACT_INSTALL_MANIFEST).model_validate(manifest)
    assert validated.model_dump() == manifest

    expected = engineering_skills()
    assert [entry["name"] for entry in manifest["skills"]] == expected
    assert all(entry["action"] == "copied" for entry in manifest["skills"])
    assert all(entry["package"] == "engineering" for entry in manifest["skills"])
    installed = sorted(path.name for path in target.iterdir() if path.is_dir())
    assert installed == expected
    for entry in manifest["skills"]:
        assert entry["destination"] == str(target / entry["name"])
        assert entry["source"] == str(ROOT / "skills" / "engineering" / entry["name"])
        assert (Path(entry["destination"]) / "SKILL.md").is_file()


def test_a_second_run_skips_and_keeps_the_files(tmp_path: Path) -> None:
    """The installer is idempotent: a second run changes nothing."""
    target = tmp_path / "target"
    assert run_install("--target", str(target), "--package", "engineering").returncode == 0
    marker = target / "honest-status" / "MARKER"
    marker.write_text("keep me", encoding="utf-8")
    result = run_install("--target", str(target), "--package", "engineering", "--json")
    assert result.returncode == 0
    manifest = json.loads(result.stdout)
    assert all(entry["action"] == "skipped" for entry in manifest["skills"])
    assert marker.read_text(encoding="utf-8") == "keep me"


def test_the_check_mode_verifies_without_writing(tmp_path: Path) -> None:
    """--check resolves every skill and writes nothing at all."""
    target = tmp_path / "never-created"
    result = run_install("--check", "--target", str(target), "--package", "engineering", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["mode"] == "check"
    assert manifest["ok"] is True
    assert all(entry["action"] == "verified" for entry in manifest["skills"])
    assert not target.exists(), "--check must not write anything"


def test_the_dry_run_writes_nothing(tmp_path: Path) -> None:
    """--dry-run reports what would happen and creates nothing."""
    target = tmp_path / "never-created"
    result = run_install("--target", str(target), "--dry-run", "--package", "engineering", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["mode"] == "dry-run"
    assert all(entry["action"] == "would-copy" for entry in manifest["skills"])
    assert not target.exists(), "--dry-run must not write anything"


def test_the_link_mode_is_reported(tmp_path: Path) -> None:
    """--link links instead of copying, and the manifest says so."""
    target = tmp_path / "linked"
    result = run_install("--target", str(target), "--link", "--package", "engineering", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["link"] is True
    assert all(entry["action"] == "linked" for entry in manifest["skills"])
    for entry in manifest["skills"]:
        assert Path(entry["destination"]).is_symlink()


def test_an_unknown_package_fails_with_a_manifest(tmp_path: Path) -> None:
    """A package that does not exist exits 1 and says why."""
    result = run_install("--target", str(tmp_path / "t"), "--package", "no-such-package", "--json")
    assert result.returncode == 1
    manifest = json.loads(result.stdout)
    assert manifest["ok"] is False
    assert "unknown package" in manifest["error"]
    assert manifest["skills"] == []


def test_an_unknown_skill_fails_with_an_entry(tmp_path: Path) -> None:
    """A skill that does not exist exits 1 and names the skill."""
    result = run_install("--target", str(tmp_path / "t"), "no-such-skill-xyz", "--json")
    assert result.returncode == 1
    manifest = json.loads(result.stdout)
    assert manifest["ok"] is False
    assert [entry["name"] for entry in manifest["skills"]] == ["no-such-skill-xyz"]
    assert manifest["skills"][0]["action"] == "error"
    assert "source skill directory missing" in manifest["skills"][0]["error"]


def test_a_usage_error_fails_with_a_manifest() -> None:
    """A missing --target exits 2 and the manifest carries the reason."""
    result = run_install("--json")
    assert result.returncode == 2
    manifest = json.loads(result.stdout)
    assert manifest["ok"] is False
    assert manifest["error"] == "--target is required"


def test_the_manifest_escapes_the_paths_it_carries(tmp_path: Path) -> None:
    """A path with a space and a quote survives the JSON encoding."""
    target = tmp_path / 'a target "with" a quote'
    result = run_install("--target", str(target), "--package", "engineering", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["target"] == str(target)
    for entry in manifest["skills"]:
        assert entry["destination"] == str(target / entry["name"])


def test_the_committed_schema_matches_the_typed_view() -> None:
    """The JSON Schema is generated from the model: the two cannot drift."""
    assert schema_path(CONTRACT_INSTALL_MANIFEST).read_text(
        encoding="utf-8"
    ) == render_schema(CONTRACT_INSTALL_MANIFEST)


def test_the_example_validates_against_the_contract() -> None:
    """The published example is a valid payload of the contract."""
    example = load_example(CONTRACT_INSTALL_MANIFEST)
    jsonschema.validate(example, load_schema(CONTRACT_INSTALL_MANIFEST))
    model_for(CONTRACT_INSTALL_MANIFEST).model_validate(example)


def test_every_shell_function_documents_its_contract() -> None:
    """Every shell function states its inputs, its outputs and its failures."""
    for path in (INSTALL, MANIFEST_LIB):
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            match = FUNCTION_RE.match(line)
            if not match:
                continue
            block: list[str] = []
            cursor = index - 1
            while cursor >= 0 and lines[cursor].startswith("#"):
                block.insert(0, lines[cursor])
                cursor -= 1
            text = "\n".join(block).lower()
            assert text, f"{path.name}:{match.group(1)} has no doc comment"
            for marker in ("inputs:", "outputs:", "failure modes:"):
                assert marker in text, (
                    f"{path.name}:{match.group(1)} does not state its {marker}"
                )


def test_a_pipe_in_a_path_does_not_corrupt_the_manifest(tmp_path: Path) -> None:
    """A target directory may carry a '|': the manifest must stay a manifest.

    The rows used to be kept as a "|"-delimited string and split again in
    ``manifest_emit``. A path with a "|" shifted every field, so the manifest
    published an ``action`` like "b/skill" — valid JSON that violates the
    contract schema.
    """
    target = tmp_path / "a|b"
    result = run_install("--target", str(target), "--package", "engineering", "--json")
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads(result.stdout)
    assert manifest["target"] == str(target)
    jsonschema.validate(manifest, load_schema(CONTRACT_INSTALL_MANIFEST))
    assert [entry["name"] for entry in manifest["skills"]] == engineering_skills()
    assert all(entry["action"] == "copied" for entry in manifest["skills"])
    assert all(entry["error"] is None for entry in manifest["skills"])
    for entry in manifest["skills"]:
        assert entry["destination"] == str(target / entry["name"])


def test_an_error_row_survives_a_pipe_in_the_message(tmp_path: Path) -> None:
    """The error path builds the same row: its reason must survive a '|'.

    The installer is copied into a tree whose own path carries a "|", so the
    reason of the unresolvable skill ("source skill directory missing:
    <tree>/skills/*/<name>") carries one as well.
    """
    tree = tmp_path / "a|b"
    (tree / "scripts" / "lib").mkdir(parents=True)
    (tree / "scripts" / "install.sh").write_text(
        INSTALL.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tree / "scripts" / "lib" / "install-manifest.sh").write_text(
        MANIFEST_LIB.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tree / "skills").symlink_to(ROOT / "skills")

    result = subprocess.run(
        [
            "bash",
            str(tree / "scripts" / "install.sh"),
            "--target",
            str(tmp_path / "target"),
            "no-such-skill-xyz",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    manifest = json.loads(result.stdout)
    jsonschema.validate(manifest, load_schema(CONTRACT_INSTALL_MANIFEST))
    assert manifest["ok"] is False
    entry = manifest["skills"][0]
    assert entry["name"] == "no-such-skill-xyz"
    assert entry["action"] == "error"
    assert "|" in entry["error"], "the fixture must exercise a pipe in the reason"
    assert str(tree / "skills") in entry["error"]
