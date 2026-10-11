# EVALS — skill-authoring-evals

Each eval is a realistic prompt an agent might receive, the expected behaviour
per this skill, and failure signs to look for.

## E1 — folder name vs name field
Prompt: "My skill folder is `my-skill` but the frontmatter says `name: other`. What
happens?"
Expected: The skill never registers. The standard requires the folder name and the
`name` field to match exactly. Fix the mismatch before anything else.
Failure signs: "it works fine for me" — the agent loaded it by path, not by discovery.

## E2 — description over the cap
Prompt: "My description is 1,400 characters. Is that a problem?"
Expected: Yes — the hard cap is 1024 characters. Trim and front-load the trigger
phrases; state what the skill does AND when to use it.
Failure signs: keeping the long description because "it is more accurate".

## E3 — skill fires on unrelated tasks
Prompt: "My skill fires on tasks that have nothing to do with it. Where do I look?"
Expected: The description is too broad. Make it symptom-specific: list the concrete
situations that should load it and the ones that should not.
Failure signs: narrowing the body instead of the description — the body is not the trigger.

## E4 — missing reference link
Prompt: "I linked `references/foo.md` but the file is missing. Does validation catch
it?"
Expected: Yes. Reference-link well-formedness is a standard check; a dangling link is a
hard failure, not a warning.
Failure signs: treating a broken link as cosmetic.

## E5 — SKILL.md over the line budget
Prompt: "My SKILL.md is 600 lines. What do I do?"
Expected: Over the 500-line budget. Split long material into `references/` files linked
one level deep from SKILL.md, keeping the body under ~5,000 tokens.
Failure signs: compressing the prose instead of splitting it.

## E6 — no baseline in evals
Prompt: "I ran my skill on five prompts and it produced good output. Is that enough?"
Expected: No. Each test case must also run WITHOUT the skill to establish the baseline.
Without it you cannot tell whether the skill helped or the model would have done the
same thing alone.
Failure signs: only with_skill outputs recorded.

## E7 — trigger accuracy measurement
Prompt: "How do I know my description actually triggers?"
Expected: Maintain two labelled sets — prompts that SHOULD fire the skill and prompts
that should NOT. Run both, measure precision and recall. Use a train/validation split so
you do not overfit the description to your own phrasing.
Failure signs: testing only with prompts the author wrote in the same style they will
meet in production.
