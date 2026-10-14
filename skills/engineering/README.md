# Engineering Playbook Skills

Ten opinionated, offline-checkable skills for Ottili engineering work. Each skill is a
folder under `skills/engineering/<name>/` with `SKILL.md` (quick reference), a
`references/` directory (procedure, EVALS, SOURCES), and a `scripts/` directory of
deterministic checkers. Install with:

```bash
./scripts/install.sh skills/engineering
```

or copy any skill folder into your agent's skills directory.

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

Validate every skill against the agentskills.io standard:

```bash
python3 scripts/validate_skills.py
```

Rebuild the index/catalog:

```bash
python3 scripts/build-index.py
```
