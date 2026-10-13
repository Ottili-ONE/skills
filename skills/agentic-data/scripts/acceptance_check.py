#!/usr/bin/env python3
"""skills-agentic-data-r3-01 acceptance checker.

Verifies the task-01 acceptance contract for the ten agentic-data skills:
  * RESEARCH.md exists and lists all ten skills
  * each skill has references/SOURCES.md with >=6 distinct primary URLs
  * each skill has references/DESIGN.md (trigger draft, procedure, scripts, 5 evals)
  * each skill has references/EVALS.md with >=5 eval prompts
  * each SKILL.md has valid YAML front matter (name == folder, description <=1024)
  * every references/ link resolves one level deep, no escapes
  * SKILL.md <=500 lines
Exit 0 only if every check passes.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = [
    "mcp-2026-07-28", "skill-authoring-evals", "computer-use-drivers",
    "browser-agent-playwright", "polite-crawling-warc", "dedup-decontam",
    "verifiable-environments", "llm-judge-calibration", "trajectory-ledger",
    "deep-research-method",
]
URL_RE = re.compile(r"https?://[A-Za-z0-9][A-Za-z0-9./?=_#&:+~-]*")
FAILS = []


def fail(msg):
    FAILS.append(msg)
    print("FAIL:", msg)


def ok(msg):
    print("ok  :", msg)


research = os.path.join(ROOT, "RESEARCH.md")
if not os.path.exists(research):
    fail("RESEARCH.md missing")
else:
    txt = open(research).read()
    missing = [s for s in SKILLS if s not in txt]
    if missing:
        fail("RESEARCH.md does not mention: %s" % ", ".join(missing))
    else:
        ok("RESEARCH.md lists all ten skills")

for s in SKILLS:
    base = os.path.join(ROOT, s)
    if not os.path.isdir(base):
        fail("%s: skill dir missing" % s)
        continue
    src = os.path.join(base, "references", "SOURCES.md")
    if not os.path.exists(src):
        fail("%s: references/SOURCES.md missing" % s)
    else:
        urls = set(URL_RE.findall(open(src).read()))
        if len(urls) < 6:
            fail("%s: only %d source URLs (need >=6)" % (s, len(urls)))
        else:
            ok("%s: %d source URLs" % (s, len(urls)))
    dsg = os.path.join(base, "references", "DESIGN.md")
    if not os.path.exists(dsg):
        fail("%s: references/DESIGN.md missing" % s)
    else:
        dt = open(dsg).read().lower()
        for kw in ["trigger", "procedure", "script", "eval"]:
            if kw not in dt:
                fail("%s: DESIGN.md lacks '%s'" % (s, kw))
            else:
                ok("%s: DESIGN.md has trigger/procedure/scripts/evals" % s)
                break
    ev = os.path.join(base, "references", "EVALS.md")
    if not os.path.exists(ev):
        fail("%s: references/EVALS.md missing" % s)
    else:
        et = open(ev).read()
        prompts = len(re.findall(
            r"(?im)^#{1,4}\s*(?:eval\s*#?\d+|scenario\s*\d+|q\d+|prompt\s*\d+|test\s*\d+|e\d+)[\s.:]",
            et))
        if prompts < 5:
            fail("%s: only %d eval prompts found (need >=5)" % (s, prompts))
        else:
            ok("%s: %d eval prompts" % (s, prompts))
    sk = os.path.join(base, "SKILL.md")
    if not os.path.exists(sk):
        fail("%s: SKILL.md missing" % s)
        continue
    lines = open(sk).read().splitlines()
    if len(lines) > 500:
        fail("%s: SKILL.md is %d lines (limit 500)" % (s, len(lines)))
    else:
        ok("%s: SKILL.md %d lines" % (s, len(lines)))
    fm = {}
    if lines and lines[0].strip() == "---":
        for l in lines[1:]:
            if l.strip() == "---":
                break
            if ":" in l:
                k, v = l.split(":", 1)
                fm[k.strip()] = v.strip()
    name = fm.get("name", "")
    if name != s:
        fail("%s: front-matter name '%s' != folder '%s'" % (s, name, s))
    else:
        ok("%s: name == folder" % s)
    desc = fm.get("description", "")
    if len(desc) > 1024:
        fail("%s: description %d chars (limit 1024)" % (s, len(desc)))
    elif not desc:
        fail("%s: description empty" % s)
    else:
        ok("%s: description %d chars" % (s, len(desc)))
    body = "\n".join(lines)
    bad = []
    for m in re.finditer(r"\]\(([^)]+)\)", body):
        tgt = m.group(1)
        if tgt.startswith(("http://", "https://", "mailto:", "#")):
            continue
        if ".." in tgt or tgt.count("/") > 1:
            bad.append(tgt)
    if bad:
        fail("%s: references link escapes: %s" % (s, bad[:3]))
    else:
        ok("%s: references links resolve one level deep" % s)

print()
if FAILS:
    print("ACCEPTANCE: FAIL (%d problems)" % len(FAILS))
    sys.exit(1)
print("ACCEPTANCE: PASS - all ten skills meet the task-01 contract")
