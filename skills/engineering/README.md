# Ottili ONE — Engineering Playbook Skills

Ten domain-specific skills under `skills/engineering/<name>/`. Each is a self-contained
directory: `SKILL.md` (the instructions an agent reads), `references/` (EVALS, SOURCES,
examples, procedures) and `scripts/` (offline, deterministic checkers with `_test.py`
twins). Every `SKILL.md` stays under 500 lines; longer material lives in `references/`.

## One-line value per skill

| Skill | Value |
| --- | --- |
| [acceptance-harness](acceptance-harness/SKILL.md) | PASS/FAIL/BLOCKED outcomes backed by a runnable evidence pointer — never a prose claim. |
| [foundation-v2-conformance](foundation-v2-conformance/SKILL.md) | Blocks raw styling literals, deep imports and untracked workarounds in `@ottili/foundation-ui` v2. |
| [honest-status](honest-status/SKILL.md) | Status buckets (DONE / VERIFIED / IN_PROGRESS / BLOCKED / FALSE_DONE) with checkable evidence. |
| [long-test-discipline](long-test-discipline/SKILL.md) | Runs long/flaky tests in the foreground with a recorded seed, ulimit budget and log artifact. |
| [module-contract-first](module-contract-first/SKILL.md) | Enumerates a module's public API into a JSON snapshot; blocks merge on drift. |
| [outbox-idempotency](outbox-idempotency/SKILL.md) | Transactional outbox: `idempotency_key`, ordered poller, poison-move, key-preserving replay. |
| [pg-rls-multitenant](pg-rls-multitenant/SKILL.md) | FORCE RLS migrations, least-privilege grants and a leak test that runs green. |
| [playwright-a11y-e2e](playwright-a11y-e2e/SKILL.md) | `data-testid` selectors, axe evidence, keyboard + responsive checks that survive refactors. |
| [problem-json-contracts](problem-json-contracts/SKILL.md) | RFC 9457 `application/problem+json` envelopes with absolute type URIs and no 5xx leakage. |
| [shared-tree-git](shared-tree-git/SKILL.md) | The foundation: commit only your own paths with a task-id prefix; never rewrite shared history. |

## Install hints

Install a single skill, or every engineering skill, into the agent's skills directory:

```bash
# one skill
./scripts/install-skill.py skills/engineering/pg-rls-multitenant

# every engineering skill (dry run first)
./scripts/install-skill.py --all --dry-run skills/engineering
./scripts/install-skill.py --all skills/engineering
```

`install.sh` is the shell entry point; `build-index.py` regenerates `index/INDEX.md`
and `index/skills.json` after any change. Verify the tree after every edit:

```bash
python3 scripts/validate_skills.py     # agentskills.io rules + EVALS counts
python3 scripts/validate.py            # catalog consistency
```

## Layout of one skill

```
skills/engineering/<name>/
├── SKILL.md                 # trigger description, procedure, Related skills
├── references/
│   ├── EVALS.md             # 5 prompts + 3 near-miss prompts + verification checklist
│   ├── SOURCES.md           # URL + retrieval date for every version-sensitive fact
│   └── ...                  # procedures, examples, decision tables (one level deep)
└── scripts/
    ├── check_*.py           # offline, deterministic checker
    └── check_*_test.py      # twin test: python3 scripts/check_*_test.py
```

## Cross-links

Every `SKILL.md` ends with a `## Related skills` section. The graph is deliberately
acyclic: `shared-tree-git` is the foundation and therefore a pure sink — it has no
outgoing markdown links, only plain-text mentions of the skills that point back at it.
Run `python3 scripts/check_shared_tree.py graph` to confirm the graph stays acyclic.

## Evals

Every `references/EVALS.md` carries five numbered prompts (expected behaviour, failure
signs, exact verification command, worked good/bad examples) and three or more
near-miss prompts that fire *before* the incident. Example (acceptance-harness N1):
"The login works but I didn't capture a screenshot — is it still PASS?" → no, downgrade
to IN_PROGRESS until the evidence pointer resolves. Run the self-tests to re-check a
skill after editing it:

```bash
python3 skills/engineering/<name>/scripts/check_*_test.py
```
