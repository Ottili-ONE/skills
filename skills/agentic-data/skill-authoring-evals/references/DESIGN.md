# DESIGN: skill-authoring-evals

## Trigger description (SKILL.md description draft, <=1024 chars)
"Write, validate and evaluate Agent Skills against the open standard: description
design that actually triggers, progressive disclosure, front-matter validation, and
eval-driven iteration. Use when an agent must author a skill, audit an existing one for
standard compliance, or measure whether a skill fires when it should; not for writing
prose documentation."

## Procedure outline
1. Design the description FIRST — it is the trigger. State what the skill does AND the
   concrete symptoms that should load it. Keep it <=1024 characters and front-load the
   trigger phrases.
2. Name the folder and the `name` field identically (slug, <=64 chars). A mismatch means
   the skill never registers.
3. Progressive disclosure: startup loads name+description only; activation loads the
   body (<5,000 tokens recommended, SKILL.md under 500 lines); references/scripts load
   on demand. Move long material into `references/` linked one level deep.
4. Validate front matter: `name`, `description` present; `description` <=1024 chars;
   SKILL.md <=500 lines; every `references/` link well-formed; scripts deterministic
   and runnable offline. Treat `allowed-tools` as optional metadata, never a hard
   failure when absent.
5. Evaluate trigger accuracy: run the skill against a set of prompts that SHOULD fire
   it and a set that should NOT. Measure precision/recall. A skill that never fires or
   fires too often is a description problem, not a body problem — fix the description.
6. Iterate: rewrite the weakest section, re-run evals, re-validate. Never ship a skill
   whose evals were not run.

## What this skill does better than a generic agent
A generic agent writes a SKILL.md and hopes it loads. This skill treats the description
as a measurable trigger, ships a validation checklist mirroring `skills-ref validate`,
and adds trigger-accuracy evals (should-fire vs should-not-fire prompts). It prevents the
common incident of a well-written skill that never registers because the folder name and
the `name` field disagree, or a description so vague it never fires.

## Five eval prompts (mirrored in `references/EVALS.md`)
1. "My skill's folder is `my-skill` but the frontmatter says `name: other`. What
   happens?" -> It never registers; make them identical.
2. "My description is 1,400 characters. Is that a problem?" -> Yes: over the 1024 cap;
   front-load the trigger phrases and trim.
3. "The skill fires on unrelated tasks. Where do I look?" -> The description is too broad;
   make it symptom-specific.
4. "I linked `references/foo.md` but the file is missing. Does validation catch it?" ->
   Yes: reference-link well-formedness is a standard check.
5. "My SKILL.md is 600 lines. What do I do?" -> Over the 500-line budget; split into
   `references/` files linked one level deep.
