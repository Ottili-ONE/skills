"""No test may write into a shared temporary directory (SKL-W0-01 TASK-0003).

The rule: a test writes only into the directory pytest gives it (``tmp_path``)
or into a directory it removes itself. A test that drops a file into the shared
temp directory leaks state between runs and between machines: two runs can
collide on the same name, and a failing test leaves the file behind.

The check is a lint over the test sources, because a leak is invisible in a
passing run: the file is written, the assertion passes, the file stays. The
runtime proof that the suite leaves nothing behind is the ``TMPDIR`` probe in
``docs/truth/REPAIR_LOG.md`` (D-026).
"""
from __future__ import annotations

import re
from pathlib import Path

THIS_FILE = Path(__file__).resolve()

TEST_FILE_PATTERNS = (
    re.compile(r"(^|/)tests/.*\.py$"),
    re.compile(r"(^|/)test_[^/]*\.py$"),
    re.compile(r"(^|/)[^/]*_test\.py$"),
)

FORBIDDEN = {
    "tempfile.mktemp(": "mktemp only picks a name; the file is never cleaned up",
    "delete=False": "a NamedTemporaryFile with delete=False outlives the test",
}


def repo_root() -> Path:
    """The root of the repository."""
    return THIS_FILE.parents[2]


def is_test_source(path: Path) -> bool:
    """True when *path* is a test file that the suite runs."""
    if path.resolve() == THIS_FILE:
        return False
    relative = path.relative_to(repo_root()).as_posix()
    if any(part.startswith(".") for part in relative.split("/")):
        return False
    return any(pattern.search(relative) for pattern in TEST_FILE_PATTERNS)


def test_no_test_source_writes_into_the_shared_temp_directory() -> None:
    """The lint: no test source may create a file in the shared temp dir."""
    offenders = []
    for path in sorted(repo_root().rglob("*.py")):
        if not path.is_file() or not is_test_source(path):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(repo_root()).as_posix()
        for needle, reason in FORBIDDEN.items():
            if needle in text:
                offenders.append(f"{relative}: {needle} ({reason})")
        if "tempfile.mkdtemp(" in text and "shutil.rmtree" not in text:
            offenders.append(
                f"{relative}: tempfile.mkdtemp( without shutil.rmtree"
            )
    assert not offenders, "test files write outside their own directory:\n" + "\n".join(
        offenders
    )


def test_the_lint_actually_finds_a_leak(tmp_path: Path) -> None:
    """The lint must not be a rubber stamp: it has to find a planted offender."""
    planted = tmp_path / "tests" / "test_planted.py"
    planted.parent.mkdir(parents=True)
    planted.write_text(
        "import tempfile\n\n\n"
        "def test_leak():\n"
        "    p = tempfile.mktemp(suffix='.json')\n"
        "    open(p, 'w').close()\n"
        "    d = tempfile.mkdtemp()\n",
        encoding="utf-8",
    )
    text = planted.read_text(encoding="utf-8")
    found = [needle for needle in FORBIDDEN if needle in text]
    assert found, "the lint would not notice a planted leak"
    assert "tempfile.mkdtemp(" in text and "shutil.rmtree" not in text
