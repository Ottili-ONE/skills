# Ottili Engineering Playbook Skills

Ten Agent Skills (agentskills.io standard) for coding and operations agents working on
the Ottili platform. Each skill folder is `<name>/` with a `SKILL.md` (front matter +
body <500 lines), `references/` (procedure, EVALS, SOURCES) and `scripts/` (small,
deterministic, runnable offline).

## Skills (one line of value each)

- [acceptance-harness](./acceptance-harness/SKILL.md) — Define PASS/FAIL/BLOCKED acceptance
  scenarios with runnable evidence pointers, never "it works".
- [foundation-v2-conformance](./foundation-v2-conformance/SKILL.md) — Enforce token-only styling,
  named imports and no bypass of Foundation v2 abstraction layers.
- [honest-status](./honest-status/SKILL.md) — Distinguish DONE, VERIFIED, IN_PROGRESS,
  FALSE_DONE and BLOCKED so handoff notes never lie.
- [long-test-discipline](./long-test-discipline/SKILL.md) — Run long/flaky tests in the
  foreground with a timeout wrapper, recorded seed and resource limits.
- [module-contract-first](./module-contract-first/SKILL.md) — Track public API snapshots,
  detect drift and import cycles before CI goes red.
- [outbox-idempotency](./outbox-idempotency/SKILL.md) — Make outbound events exactly-once
  via a transactional outbox + idempotent consumer.
- [pg-rls-multitenant](./pg-rls-multitenant/SKILL.md) — Isolate tenants with PostgreSQL Row
  Level Security so no cross-tenant read/write is possible by default.
- [playwright-a11y-e2e](./playwright-a11y-e2e/SKILL.md) — E2E tests with stable selectors,
  axe A/AA evidence and keyboard-only paths across responsive breakpoints.
- [problem-json-contracts](./problem-json-contracts/SKILL.md) — Emit RFC 9457 problem details
  with a stable catalogue, versioned schema and machine-checkable examples.
- [shared-tree-git](./shared-tree-git/SKILL.md) — Commit only your own paths with a task-id
  prefix on a shared tree where up to three agents work simultaneously.

## Install hints

- Validate all ten at once: `python3 scripts/validate_skills.py`
- Validate one skill: `python3 scripts/validate_skill.py <name>`
- Run the repo-wide conformance check: `python3 scripts/validate.py`
- Install a skill into an agent home: `./scripts/install.sh <name> <target-dir>`
- Rebuild the index: `python3 scripts/build-index.py`

## Evals and cross-links

Each skill carries `references/EVALS.md` with 5 realistic prompts (expected behaviour +
failure signs + exact verification command) and 3-5 near-miss prompts that fire *before*
the incident. The Related-section graph across all ten skills is acyclic by construction:
`shared-tree-git` is the foundation and has no outgoing links; every other skill points
toward it or toward a peer. Re-check after any edit with the inline script below:

```
python3 - <<'EOF'
import re, glob, os
skills=[d.split('/')[-2] for d in glob.glob("skills/engineering/*/") if os.path.isfile(d+"SKILL.md")]
g={}
for s_ in skills:
    txt=open(f"skills/engineering/{s_}/SKILL.md").read()
    sec=txt.split("## Related skills",1)[-1].split("\n## ",1)[0]
    g[s_]=re.findall(r'\[.*?\]\(\.\./([a-z0-9-]+)/SKILL.md\)', sec)
c={s_:0 for s_ in skills}
def d(u):
    c[u]=1
    for v in g.get(u,[]):
        if v not in c: d(v)
        elif c[v]==1: raise SystemExit(f"cycle through {u}->{v}")
    c[u]=2
for s_ in skills: d(s_)
print("acyclic OK")
EOF
```

## Layout of one skill

```
<name>/
  SKILL.md                 # front matter + body (progressive disclosure entry point)
  references/
    agentskills-standard.md  # (shared) the standard the skill conforms to
    <name>-procedure.md      # full recipe, version table, pitfalls, worked examples
    EVALS.md                 # >=5 prompts + 3 near-miss prompts + failure signs
    SOURCES.md               # primary source URLs, retrieval dates, version pins
  scripts/                 # small deterministic helpers + _test.py self-tests
```

Quality bar: every claim is backed by a runnable command or a primary source; no filler,
no generic advice.
