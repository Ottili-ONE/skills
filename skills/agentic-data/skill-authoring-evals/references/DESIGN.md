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

## Five eval scenarios (expanded in `references/EVALS.md`)
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

## What existing public skills do (and what this one does differently)

Surveyed on 2026-10-12. The ecosystem has ~24,400 skill-definition repositories
(fast.io, verified live) and the directories are full of *content* skills
(frontend-design, paper-search, security) — but almost none about *authoring
skills itself*. `anthropics/skills` ships a `template-skill` and a README convention
(the "how to write a skill" page), and `openai/skills` (deprecated, redirects to
`openai/plugins`) documented the `.system/.curated/.experimental` tier flow. Neither
is a skill you can invoke to validate or evaluate a skill. The Fastio 2026 directory
dedicates one section ("What Goes in a SKILL.md File") to the same topic in prose.

This skill is the only one that turns authoring into a measurable, repeatable
procedure:
- **Description is the trigger, and it is measurable**: the skill ships
  should-fire / should-not-fire prompt sets and measures precision/recall. A skill
  that never fires or fires too often has a description problem, not a body problem.
- **Validation mirrors `skills-ref validate`** (name == folder name, description <=
  1024 chars, SKILL.md <= 500 lines, references well-formed one level deep, scripts
  deterministic and offline) but adds the checks the standard leaves to the author:
  progressive-disclosure depth, trigger-accuracy evals, and a report JSON.
- **Eval-driven iteration is a loop, not a checkbox**: rewrite the weakest section,
  re-run evals, re-validate. A skill whose evals were never run is not shipped.
- **`allowed-tools` is optional metadata**, never a hard failure — the standard
  lists it as optional and treating its absence as a failure rejects valid skills.

Public sources surveyed (2026-10-12, all HTTP 200):
| Source | What it has | Gap this skill fills |
|--------|-------------|---------------------|
| `anthropics/skills` (template-skill, README) | a convention | not an invocable skill; no validation or evals |
| `openai/skills` (deprecated) | tier flow docs | deprecated; no validation |
| `agentskills.io/specification` | the standard | a spec, not a procedure; no scripts |
