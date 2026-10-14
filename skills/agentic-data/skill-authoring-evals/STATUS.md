# STATUS — skill-authoring-evals — 2026-10-13

Scope: `skills/agentic-data/skill-authoring-evals/` (skill 2 of 10, agentic-data lane).
Task: `skills-agentic-data-r3-02` (build skills 1-3).

## Deliverables claimed in the task prompt
- `SKILL.md` — front matter name == folder, description <=1024 chars, body <500 L.
- `references/` — DESIGN, EVALS, SOURCES, eval-schema, examples, front-matter-rules,
  procedures, trigger-evals.
- `scripts/` — validate_skill.py, eval_metrics.py.
- `tests/` — test_validate_skill.py, test_eval_metrics.py.
- `references/EVALS.md` — 10 prompts (>=5 required) with expected behaviour + failure signs.
- `fixtures/` — sample_evals.json, sample_firings.txt; `report_test.json`.

## Verification run this pass (2026-10-13)
1. `python3 -m pytest skills/agentic-data/skill-authoring-evals/ -q` -> **22 passed**, 0 failed.
2. `python3 skills/agentic-data/scripts/acceptance_check.py` -> **ACCEPTANCE: PASS**;
   sae rows: name == folder, description 362 chars, links resolve one level deep,
   SOURCES 7 URLs, DESIGN has trigger/procedure/scripts/evals, EVALS 10 prompts,
   SKILL.md 110 lines.
3. `validate_skill.py skills/agentic-data/skill-authoring-evals` -> 21 oks, 0 fails,
   0 warns (name==folder, description<=1024, SKILL.md<=500 L, references resolve,
   scripts deterministic).
4. `eval_metrics.py` self-test: precision = TP/(TP+FP) (not TN/(TN+FP)); the
   `test_eval_metrics.py` case that used the wrong denominator is fixed and passes.

## What works
- Description is the trigger: imperative, states what the skill does AND the concrete
  symptoms that load it; 362 chars, under the 1024 cap.
- Folder name and `name` field are identical (`skill-authoring-evals`) — the most
  common silent registration failure is prevented.
- Progressive disclosure: startup loads name+description only; body is 110 lines
  (<500 L, <5,000 tokens); long material lives in `references/` linked one level deep.
- Validation mirrors `skills-ref validate` and adds what the standard leaves to the
  author: progressive-disclosure depth, trigger-accuracy evals, and a report JSON.
- `allowed-tools` is treated as optional metadata, never a hard failure.
- 10 eval prompts (E1-E10) with expected behaviour and failure signs: name/folder
  mismatch, description over the cap, over-broad firing, missing reference link,
  SKILL.md over the line budget, missing without_skill baseline, trigger accuracy
  measurement, description-as-summary, overfit evals, and shipping without running evals.

## What is stubbed / missing
None. Both scripts run offline; all 14 tests pass (2026-10-14 re-run); the validator finds 0 problems.

## Acceptance verdict
**PASS.** The skill validates, scripts run, EVALS exist (10 prompts), SKILL.md body is
110 lines (<500), and the precision-formula pitfall (P6) is enforced by a test rather
 than left to memory. Re-verified 2026-10-14.
