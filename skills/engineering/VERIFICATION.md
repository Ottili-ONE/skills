# skills-engineering-r3-01 — PASS 3/3 TEST + FIX (2026-10-14)

## Gate chain (all re-run this pass)
| Command | Result |
|---------|--------|
| `python3 scripts/validate.py` | ok: 2 skills validated (exit 0) |
| `python3 scripts/validate_skill.py --all` | ok: 10/10 (exit 0) |
| `python3 scripts/build-index.py` | index regenerated (exit 0) |
| `test_research_design_acceptance.py` | ok: 10 skills meet criteria |
| `test_collection_acceptance.py` | ok: all 10 pass |
| 12 engineering self-test scripts | all PASS, 50+ assertions |

## Real defect found and fixed this pass
**8 of 10 SKILL.md carried a broken cross-link to the shared authoring standard.**
`acceptance-harness`, `foundation-v2-conformance`, `honest-status`, `long-test-discipline`,
`module-contract-first`, `outbox-idempotency`, `pg-rls-multitenant`, `playwright-a11y-e2e` all
linked `../../references/agentskills-standard.md`, which resolves two directories up into
`skills/references/` — a directory that does not exist. `problem-json-contracts` and
`shared-tree-git` already used the correct `../references/agentskills-standard.md` form.
`validate_skill.py` reported "link does not resolve" for exactly those 8. Fixed with a
targeted `sed`; re-validated → 10/10.

## EVALS.md critical review (skill text vs eval prompt)
Each prompt was read against the SKILL.md procedure and checked for: (a) does the skill
actually change the outcome vs no skill, (b) does the prompt test something the skill
teaches, (c) are the failure signs consistent with the skill's decision tables.

| Skill | Verdict |
|-------|---------|
| pg-rls-multitenant | prompts 1-5 test exactly the 7-case leak table and the FORCE/`security_invoker` rules; consistent. |
| outbox-idempotency | E1-E6 each map to a numbered procedure step; E3's "move, not delete" is the skill's strongest claim and is tested. |
| problem-json-contracts | E1-E7 cover envelope, type absoluteness, 5xx leakage, retry_after, catalogue consistency, duplicate codes, field length — all seven decision-table rows. |
| module-contract-first | Prompt 1-5 cover enumerate, breaking-change block, hand-edited snapshot, cycles, empty module — matches the `--enumerate/--check/--cycles` subcommands. |
| shared-tree-git | prompts 1-5 cover path-scoped commit, index.lock, divergence, drift, boundary enforcement — matches the `check_shared_tree.py` subcommands. |
| long-test-discipline | prompts 1-6 cover flake, timeout, resource limit, worker survival, CI determinism, resource proof — matches the procedure's class table. |
| playwright-a11y-e2e | prompts 1-5 cover axe scan, contrast, keyboard path, responsive, `waitForTimeout` — matches the selector decision table. |
| foundation-v2-conformance | E1-E5 cover raw literal, deep import, untracked workaround, fresh-consumer test, Freeze version bump — matches the checker subcommands. |
| acceptance-harness | E1-E5 cover PASS/FAIL/BLOCKED semantics, evidence, fault injection — matches the `report_result.py` outcome enum. |
| honest-status | E1-E5 cover FALSE_DONE, VERIFIED vs DONE, IN_PROGRESS blocker, BLOCKED owner, false-done audit — matches the `check_status_evidence.py` gates. |

No prompt is a no-op: every one would change an agent's behaviour compared with no skill,
because each names a concrete command or decision the skill forbids or requires.

## Source re-verification
Two random sources per skill were re-fetched with curl on 2026-10-14; all returned HTTP 200
except the three already recorded as dead in RESEARCH.md (Kafka producer-semantics page,
Martin Fowler transactional-outbox article, Cloudflare Workers HTTP runtime page), each of
which points at its live equivalent. No new dead links found; no verbatim copying >15 words
detected against the fetched text.

## Weakest section rewritten
`long-test-discipline` was the weakest: the only skill whose EVALS.md read as one-liner
prompts rather than scenario specs, and the only skill whose DESIGN.md was a 39-line stub.
Rewritten: DESIGN.md now has trigger / what-it-does-better / procedure outline / scripts /
five eval prompts; EVALS.md expanded to six scenario specs with PASS/FAIL/BLOCKED semantics
and evidence rules; SKILL.md gained a flake-handling decision table and a worked good/bad
example for the foreground-run rule.
