# Procedures — skill-authoring-evals

Verified 2026-10-12 against the agentskills.io specification and the four
skill-creation guides (SOURCES.md). Step-by-step instructions that SKILL.md
links to on demand.

## P1 — author a new skill

1. Pick the folder name first. It must be a slug: lowercase, alphanumeric and
   single hyphens, 1-64 chars, no leading/trailing hyphen, no `--`.
2. Write the `name` field in the frontmatter to match the folder name exactly.
   A mismatch means the skill never registers — this is the most common silent
   failure.
3. Write the description BEFORE the body. It is the trigger. State what the
   skill does AND the concrete symptoms that should load it. Imperative
   phrasing ("Use this skill when…"), user intent not implementation, pushy
   but not broad. Hard cap 1024 characters.
4. Write the body as a numbered procedure with decision tables, pitfalls and a
   verification checklist. Keep it under ~5,000 tokens and 500 lines.
5. Push long material into `references/` linked one level deep from SKILL.md.
   Scripts go in `scripts/` and must be deterministic and runnable offline.

## P2 — validate an existing skill

Run `scripts/validate_skill.py <skill-dir>` (or `--skill <path>`). It checks:

| Check | Severity |
|-------|----------|
| folder name is a valid slug | hard fail |
| `name` field present and == folder name | hard fail |
| `name` <= 64 chars | hard fail |
| `description` present and <= 1024 chars | hard fail |
| SKILL.md <= 500 lines | hard fail |
| every `references/*.md` link resolves | hard fail |
| scripts deterministic (no network) | warn |
| `allowed-tools` present | ignored (experimental) |

Machine-readable counts go to stdout as `oks fails warns`; detail lines are
prefixed `FAIL:`/`PASS:`/`WARN:`/`INFO:` and go to stderr. Exit 0 on success, 1
on any FAIL, 2 on usage/input errors. Pass `--json <path>` for a machine-readable
report.

## P3 — run trigger evals

1. Build two labelled sets: prompts that SHOULD fire the skill and prompts that
   should NOT. Keep them realistic — real users mention file paths, column
   names and personal context.
2. Split 70/30 train/validation. Tune the description on the training set; measure
   on the validation set. If the two sets score very differently the description
   is overfit to the training phrasing — recruit fresh prompts.
3. Run every prompt twice: once with the skill loaded, once without. The
   without_skill run is the baseline. Record outputs in
   `iteration-N/<eval>/with_skill/` and `without_skill/`, aggregated in
   `benchmark.json`.
4. Metrics: precision = should-not-fire prompts that did NOT fire / all
   should-not-fire; recall = should-fire prompts that DID fire / all should-fire.
   Target precision >= 0.9 and recall >= 0.9. Below 0.8 on either, rewrite the
   description, not the body.
5. Identify the weakest section (lowest recall or lowest output delta), rewrite
   it, re-run evals, re-validate. Never ship a skill whose evals were not run.

## P4 — iterate on a failing skill

A skill that never fires is a description problem: widen the trigger phrases.
A skill that fires on everything is a description problem: narrow to
symptom-specific situations. A skill that fires but produces poor output is a
body problem: rewrite the weakest section. Fix the description first in both
cases — the body is not the trigger.

## Near-miss triggers

- The folder slug and the frontmatter `name` field do not match -> the skill never
  registers, so fix that before touching anything else.
- All eval prompts are the author's own phrasing -> overfit; recruit fresh
  prompts.
- Only with_skill runs recorded -> no baseline; a skill that does nothing looks
  identical to a skill that works.
- Tuning the description until the validation set passes -> the validation set
  is now part of the training set; re-split.
- Shipping because "it looks good" -> the evals were never run.
