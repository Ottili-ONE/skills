# Engineering Playbook Skills (r3-05 quality pass)

Ten opinionated, offline-checkable Agent Skills for Ottili engineering work.
Each skill is a folder `skills/engineering/<name>/` with `SKILL.md` (quick reference),
`references/` (procedure, EVALS, SOURCES, DESIGN), and `scripts/` (deterministic checkers).

## Install

```bash
./scripts/install.sh --target codex --force pg-rls-multitenant outbox-idempotency ...
# or copy any skill folder into your agent's skills directory
```

## Skills

- **acceptance-harness** — Define PASS/FAIL/BLOCKED acceptance scenarios, collect per-scenario evidence, and inject faults to prove resilience.
- **foundation-v2-conformance** — Enforce token-only styling, named imports, tracked workaround markers, and fresh-consumer tests for Foundation v2 packages.
- **honest-status** — Write STATUS.md that separates done/verified/in-progress/blocked, detects false-done claims, and records runnable evidence pointers.
- **long-test-discipline** — Schedule long-running tests in the foreground with timeout wrappers, structured logs, resource limits, and deterministic reruns for flakes.
- **module-contract-first** — Design and enforce module contracts: public API surface, versioned schemas, drift tests against snapshots, boundary rules between siblings.
- **outbox-idempotency** — Implement the transactional outbox pattern with idempotency keys, poison-row handling, and replay that preserves the original key.
- **pg-rls-multitenant** — Enforce Postgres row-level security for multi-tenant workloads: tenant-key-first design, FORCE RLS, expand/contract migrations, automated leak tests.
- **playwright-a11y-e2e** — End-to-end browser tests with Playwright and axe-core: axe scans, keyboard-only navigation, responsive breakpoints, stable selectors.
- **problem-json-contracts** — RFC 9457 problem+json error contracts: error catalogue, retry semantics, versioned schemas, validators that fail on malformed responses.
- **shared-tree-git** — Commit by path with task-id prefixes in a multi-agent shared tree, recover `index.lock`, and verify commit isolation.

## Quick checks

```bash
python3 scripts/validate_skills.py   # agentskills.io rules + EVALS counts, exit 0
python3 scripts/validate.py          # catalog consistency, exit 0
for t in $(find skills/engineering -name '*_test.py' | sort); do python3 "$t" || exit 1; done
```

## r3-05 quality pass notes

- Every `references/EVALS.md` carries 5 primary prompts and 3 near-miss prompts (trigger-precision guard).
- Cross-links in every `## Related skills` section form an acyclic graph with `shared-tree-git` as the unique sink.
- Version-sensitive facts in SOURCES.md were re-verified against primary sources this pass.
