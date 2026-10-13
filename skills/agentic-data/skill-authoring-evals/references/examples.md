# Worked examples — skill-authoring-evals

Verified 2026-10-13. Good and bad authoring, with the detection signal.
These examples are *original* text written for this skill; they are not
quotations from the SKILL.md body.

## Good — description that triggers

> "Use this skill when an agent must author, validate or evaluate an Agent Skill:
> the folder name and frontmatter `name` disagree, the description exceeds 1024
> characters, trigger evals have no without_skill baseline, or a skill fires on
> unrelated tasks."

Detection signal: it states what + when, is imperative, and names concrete
symptoms. `scripts/validate_skill.py` reports `0 0` on the skill folder.

## Bad — abstract summary

> "This skill helps with Agent Skill authoring."

Detection signal: no symptom, no "when", no imperative. It will never fire
reliably — widen it with concrete situations.

## Bad — name/folder mismatch

Folder `my-skill`, frontmatter `name: other`. The skill never registers.
Detection signal: `validate_skill.py` prints
`FAIL: name field 'other' != folder name 'my-skill'` and exits 1.

## Good — progressive disclosure

SKILL.md is 90 lines. Long procedures live in `references/procedures.md`,
linked one level deep. Activation cost stays under ~5,000 tokens.

## Bad — everything in the body

SKILL.md is 600 lines. Detection signal: `validate_skill.py` prints
`FAIL: SKILL.md over 500 lines (600)` and exits 1. Split into `references/`.

## Good — eval loop with baseline

`iteration-1/with_skill/` and `iteration-1/without_skill/` both exist for every
prompt; `benchmark.json` aggregates precision, recall and output delta.

## Bad — no baseline

Only `with_skill/` outputs recorded. A skill that does nothing looks identical
to a skill that works. Detection signal: `without_skill/` is absent for any prompt.

## Good — eval prompts that discriminate

A prompt set contains two labelled sets: prompts that SHOULD fire the skill and
prompts that should NOT. Keep them realistic — real users mention file paths,
error messages and concrete symptoms, not skill names.

## Bad — eval prompts that merely restate the description

Every prompt echoes the skill's own trigger sentence. The eval then measures
whether the agent can read, not whether the skill is useful. Detection signal:
>90% of prompts contain a substring of the description.

## Good — measurement that separates signal from noise

Precision, recall and output delta are computed per prompt and aggregated into
a benchmark file. A skill with precision 0.9 and recall 0.2 is doing something
right but missing most cases — the report makes that legible.

## Bad — a single pass/fail number

One "passed" bit per prompt hides whether the skill fired, fired wrongly or
did nothing. Detection signal: no per-prompt precision/recall columns.
