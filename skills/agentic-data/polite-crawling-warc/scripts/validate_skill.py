#!/usr/bin/env python3
"""Validate the polite-crawling-warc skill against the Agent Skills standard.

Checks: SKILL.md front matter (name == folder, description <= 1024 chars),
body < 500 lines, every references/*.md linked one level deep, every script
parses, EVALS.md has >= 5 prompts, SOURCES.md has >= 6 URLs with retrieval
dates, and the robots parser + WARC writer + WARC validator run offline.

Usage:
  python3 validate_skill.py
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_DESC = 1024
MAX_BODY_LINES = 500
MIN_EVALS = 5
MIN_SOURCES = 6

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
DESC_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)


def validate(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return [f"SKILL.md missing in {skill_dir}"]

    text = skill_md.read_text(encoding="utf-8")
    fm = FRONTMATTER_RE.match(text)
    if not fm:
        errors.append("missing YAML frontmatter")
    else:
        block = fm.group(1)
        name_m = NAME_RE.search(block)
        desc_m = DESC_RE.search(block)
        if not name_m:
            errors.append("frontmatter missing name")
        else:
            name = name_m.group(1).strip().strip('"').strip("'")
            if name != skill_dir.name:
                errors.append(f"name '{name}' != folder name '{skill_dir.name}'")
            if re.search(r"[A-Z_]", name):
                errors.append(f"name '{name}' is not lowercase-hyphenated")
        if not desc_m:
            errors.append("frontmatter missing description")
        else:
            desc = desc_m.group(1).strip().strip('"').strip("'")
            if len(desc) > MAX_DESC:
                errors.append(f"description {len(desc)} chars > {MAX_DESC}")

    body = text[fm.end():] if fm else text
    n_body = len([l for l in body.splitlines() if l.strip()])
    if n_body > MAX_BODY_LINES:
        errors.append(f"body {n_body} lines > {MAX_BODY_LINES}")

    refs = skill_dir / "references"
    if not refs.is_dir():
        errors.append("references/ directory missing")
    else:
        linked = set(re.findall(r"references/([A-Za-z0-9_\-]+\.md)", body))
        for f in refs.glob("*.md"):
            if f.name not in linked:
                errors.append(f"reference {f.name} not linked from SKILL.md")

    scripts = skill_dir / "scripts"
    if not scripts.is_dir():
        errors.append("scripts/ directory missing")
    else:
        for py in sorted(scripts.glob("*.py")):
            if py.name.startswith("_"):
                continue
            r = subprocess.run([sys.executable, "-c", f"import ast; ast.parse(open({str(py)!r}).read())"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                errors.append(f"{py.name}: syntax error: {r.stderr.strip()}")

        # Run the robots parser offline: a disallowed path must FAIL.
        robots = scripts / "robots.py"
        if robots.is_file():
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
                tf.write("User-agent: *\nDisallow: /private/\n")
                tf.flush()
                r = subprocess.run([sys.executable, str(robots), "--file", tf.name, "--path", "/private/x"],
                                   capture_output=True, text=True)
                if r.returncode != 1:
                    errors.append("robots.py did not reject a disallowed path")
                Path(tf.name).unlink(missing_ok=True)
        else:
            errors.append("scripts/robots.py missing")

        # Run the WARC writer + validator offline: a round-trip must validate.
        warc = scripts / "warc_writer.py"
        val = scripts / "validate_warc.py"
        if warc.is_file() and val.is_file():
            with tempfile.TemporaryDirectory() as td:
                wf = Path(td) / "out.warc.gz"
                r = subprocess.run([sys.executable, str(warc), "--file", str(wf), "--type", "response",
                                    "--target-uri", "http://example.com/", "--payload", "hello"],
                                   capture_output=True, text=True)
                if r.returncode != 0:
                    errors.append(f"warc_writer.py failed: {r.stderr.strip()}")
                else:
                    r2 = subprocess.run([sys.executable, str(val), str(wf)], capture_output=True, text=True)
                    if r2.returncode != 0:
                        errors.append(f"validate_warc.py failed on a freshly written WARC: {r2.stderr.strip()}")
        else:
            errors.append("scripts/warc_writer.py or scripts/validate_warc.py missing")

    evals = refs / "EVALS.md"
    if evals.is_file():
        n = len(re.findall(r"^## E\d+ ", evals.read_text(encoding="utf-8"), re.MULTILINE))
        if n < MIN_EVALS:
            errors.append(f"EVALS.md has {n} evals, need >= {MIN_EVALS}")
    else:
        errors.append("references/EVALS.md missing")

    src = refs / "SOURCES.md"
    if src.is_file():
        t = src.read_text(encoding="utf-8")
        n_urls = len(re.findall(r"https?://\S+", t))
        if n_urls < MIN_SOURCES:
            errors.append(f"SOURCES.md has {n_urls} URLs, need >= {MIN_SOURCES}")
        if not re.search(r"Retrieved:\s*20\d{2}-\d{2}-\d{2}", t):
            errors.append("SOURCES.md missing retrieval dates")
    else:
        errors.append("references/SOURCES.md missing")

    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", default=str(Path(__file__).resolve().parents[1]))
    args = ap.parse_args()
    errors = validate(Path(args.skill))
    if not errors:
        print(f"PASS: {Path(args.skill).name} validates against the Agent Skills standard", file=sys.stderr)
        return 0
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)
    print(f"FAIL: {len(errors)} problem(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
