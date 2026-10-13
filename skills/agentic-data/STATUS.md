# STATUS — skills-agentic-data-r3-02 (Build skills 1-3) — 2026-10-13

Scope: `skills/agentic-data/mcp-2026-07-28`,
`skills/agentic-data/skill-authoring-evals`,
`skills/agentic-data/computer-use-drivers`.

## What works (proven by a command + result)

- `python3 -m pytest mcp-2026-07-28/tests skill-authoring-evals/tests
  computer-use-drivers/tests` -> `64 passed` (exit 0), all offline.
- `python3 skill-authoring-evals/scripts/validate_skill.py <skill>` -> exit 0 for all
  three (mcp 28/0/0, sae 21/0/0, cud 22/0/0 = fails/warns/info counts).
- Front matter: `name` == folder for all three; `description` 455/407/388 chars
  (limit 1024); SKILL.md 119/110/154 lines (limit 500); every `references/` link
  resolves one level deep (verified by script: 0 missing across all three).
- All three scripts run offline and deterministically:
  - mcp: `protocol_check.py --json`, `version_negotiate.py --client ... --server ...
    --json`, `stateless_probe.py a b`.
  - sae: `validate_skill.py <dir>`, `eval_metrics.py` (precision/recall/delta).
  - cud: `validate_driver.py` (17-member audit + `--contract` registry diff).

## What is stubbed / missing
- None. Every script, test, EVALS entry and reference page shipped in this pass
  runs. The three skills were already complete from the earlier EXPAND passes;
  this pass was a defect sweep and a precision-formula correction.

## Defect found and fixed this pass
1. **`validate_driver.py` main() was unreachable in contract mode.** When called
   with only `--contract`, the code fell through the `if args.contract` branch,
   hit `if not args.file`, and re-ran `contract(Path(args.contract))` with
   `args.contract` still `None` -> `TypeError: expected str, bytes or os.PathLike,
   not NoneType` (exit 2). Rewrote main() as a single mutual-exclusion dispatch:
   `--contract and --file` -> exit 2; `--contract` -> contract mode; `file` ->
   audit mode; neither -> `ap.error`. The `--json` report now carries the real
   `mode` ("audit"/"contract") instead of the literal `"audit"`.
2. **SOURCES.md said "Member set (16)"** while every other page, the EVALS, the
   DESIGN and the CANONICAL list in the script all say 17. `key` is a member in
   its own right. Corrected the version-sensitive-facts table to 17.
3. **Precision was defined backwards in three sae reference pages**
   (`procedures.md`, `trigger-evals.md`, `eval-schema.md`). They wrote
   `TN / all should-not-fire` instead of `TP / (TP + FP)`. The SKILL.md and
   `scripts/eval_metrics.py` already had the correct formula; the reference pages
   were the outliers and contradicted the shipped metric. Corrected all three to
   state the denominator is the number of *fired* cases and to name the
   `TN/(TN+FP)` mistake explicitly.
4. **platform-quirks.md said confirm() text "must use invisible characters so it
   does not appear as visible text".** That inverts the real rule: the danger is
   that invisible characters are *not visible to the approver*, so a homoglyph
   attack turns `rm -rf foo` into a string that looks identical but executes
   differently. Rewrote as "escape every invisible character ... the approver
   reads exactly what runs".
