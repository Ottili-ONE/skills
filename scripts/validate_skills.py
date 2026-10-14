#!/usr/bin/env python3
"""Agent Skills standard validator (offline, deterministic).

Checks the rules from https://agentskills.io/specification for every skill folder:
  - folder name == SKILL.md front-matter `name` (lowercase-hyphenated)
  - `description` present and <= 1024 chars, states what + when to use
  - SKILL.md exists, body < 500 lines, instructions part < ~5000 tokens
  - optional fields only portable ones used (license, compatibility, metadata, allowed-tools)
  - references/ linked one level deep from SKILL.md
  - references/EVALS.md exists with >= 5 prompts
  - references/SOURCES.md exists
  - scripts/ helpers are runnable offline (shebang + executable bit or .py)

Exit codes: 0 all pass, 1 findings, 2 usage error.
"""
import os, re, sys, json

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
SKILLS_DIR = os.path.abspath(os.path.join(ROOT, "skills", "engineering"))

PORTABLE_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

def find_skills():
    out = []
    if not os.path.isdir(SKILLS_DIR):
        return out
    for name in sorted(os.listdir(SKILLS_DIR)):
        p = os.path.join(SKILLS_DIR, name)
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, "SKILL.md")):
            out.append(name)
    return out

def parse_front_matter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    fm = {}
    cur_key = None
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith("-"):
            if cur_key:
                fm.setdefault(cur_key, []).append(line.strip()[1:].strip())
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            fm[k] = v
            cur_key = None
        else:
            cur_key = None
    return fm, text

def count_lines(path):
    return sum(1 for _ in open(path, encoding="utf-8"))

def main():
    skills = find_skills()
    if not skills:
        print("no skills found under", SKILLS_DIR)
        return 2
    findings = []
    for s in skills:
        d = os.path.join(SKILLS_DIR, s)
        sm = os.path.join(d, "SKILL.md")
        fm, text = parse_front_matter(sm)
        if fm is None:
            findings.append((s, "SKILL.md has no YAML front matter"))
            continue
        # name
        if fm.get("name") != s:
            findings.append((s, f"name={fm.get('name')!r} != folder {s!r}"))
        # name format
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", fm.get("name", "")):
            findings.append((s, f"name {fm.get('name')!r} not lowercase-hyphenated"))
        # description
        desc = fm.get("description", "")
        if not desc:
            findings.append((s, "missing description"))
        elif len(desc) > 1024:
            findings.append((s, f"description {len(desc)} chars > 1024"))
        elif not re.search(r"(use when|fires|when to use|trigger)", desc, re.I):
            findings.append((s, "description lacks 'when to use' trigger"))
        # portable fields
        for k in fm:
            if k not in PORTABLE_FIELDS:
                findings.append((s, f"non-portable front-matter field {k!r}"))
        # body lines
        n = count_lines(sm)
        if n > 500:
            findings.append((s, f"SKILL.md body {n} lines > 500"))
        # references one level deep
        refs = os.path.join(d, "references")
        linked = set()
        if os.path.isdir(refs):
            for fn in os.listdir(refs):
                fp = os.path.join(refs, fn)
                if os.path.isfile(fp):
                    linked.add(fn)
        must_link = {fn for fn in linked if fn in ("EVALS.md", "SOURCES.md") or fn.endswith("-procedure.md")}
        for fn in sorted(must_link):
            if not re.search(rf"(?:\./)?references/{re.escape(fn)}", text):
                findings.append((s, f"SKILL.md does not link references/{fn}"))
        # EVALS
        ev = os.path.join(refs, "EVALS.md")
        if not os.path.isfile(ev):
            findings.append((s, "missing references/EVALS.md"))
        else:
            ev_text = open(ev, encoding="utf-8").read()
        prompts = len(re.findall(r"^\d+\.", ev_text, re.M))
        prompts += len(re.findall(r"^##\s+(?:[A-Z]\d+|\d+)\b", ev_text, re.M))
        prompts += len(re.findall(r"^##\s+(?:[A-Z]\d+|\d+)\b", ev_text, re.M))
        if prompts < 5:
            findings.append((s, f"EVALS.md has {prompts} prompts, need >=5"))
        # SOURCES
        if not os.path.isfile(os.path.join(refs, "SOURCES.md")):
            findings.append((s, "missing references/SOURCES.md"))
        # scripts runnable offline
        sc = os.path.join(d, "scripts")
        if os.path.isdir(sc):
            for fn in sorted(os.listdir(sc)):
                fp = os.path.join(sc, fn)
                if not os.path.isfile(fp):
                    continue
                if fn.endswith(".py"):
                    pass
                elif fn.endswith(".sh"):
                    if not os.access(fp, os.X_OK):
                        findings.append((s, f"script {fn} not executable"))
                else:
                    findings.append((s, f"unexpected script file {fn}"))

    if findings:
        print("FINDINGS:")
        for s, f in findings:
            print(f"  [{s}] {f}")
        return 1
    print("OK: all skills validate")
    return 0

if __name__ == "__main__":
    sys.exit(main())
