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

## E8 — description is a trigger, not a summary
Prompt: "I wrote a one-sentence description that says what the skill does in the
abstract. It never fires. Why?"
Expected: The description must state the concrete symptoms that should load it,
in imperative phrasing ("Use this skill when…"), and front-load the trigger phrases.
Abstract summaries are not triggers.
Failure signs: "the description is accurate" without a single symptom phrase.

## E9 — overfit evals
Prompt: "My evals all pass but the skill fails in the wild. What went wrong?"
Expected: The eval prompts were the author's own phrasing. Recruit fresh prompts,
use a train/validation split, and re-measure on the validation set. If train and
validation scores diverge, the description is overfit.
Failure signs: all prompts written by the author in the same style they will meet
in production.

## E10 — shipped without running evals
Prompt: "My skill is done and looks good. Should I run the evals?"
Expected: No. Never ship a skill whose evals were not run. The eval loop is the
only way to know whether the description triggers and whether the body changes
the output at all.
Failure signs: "it looks good" as a substitute for measurement.

## E11 — the allowed-tools trap
Prompt: "My SKILL.md has no `allowed-tools` field. Is that a problem?"
Expected: No. `allowed-tools` is experimental metadata, not a required field, and the
validator must never treat its absence as a failure. It is information for clients that
support it, not a gate. Do not add it to make validation pass.
Failure signs: adding `allowed-tools: []` to every skill; treating a missing field as
a validation error.

## E12 — the train/validation drift
Prompt: "I tuned my description until every eval passed, then shipped it. What did I
miss?"
Expected: You tuned on the validation set, so the validation set is now part of the
training set. Re-split, recruit fresh prompts, and re-measure. If train and validation
scores diverge after the re-split, the description is still overfit.
Failure signs: a single eval set used for both tuning and declaring success.

## E13 — the metrics target
Prompt: "My skill scored precision 0.6 and recall 0.7. Is that good enough?"
Expected: No. The targets are precision >= 0.9 and recall >= 0.9. Below 0.8 on
either, rewrite the description, not the body — the body is not the trigger.
Detection: `scripts/eval_metrics.py` prints `FAIL: precision 0.6 (target 0.9)`.
Failure signs: "the description is accurate" as a substitute for measurement.

## E14 — the eval artefact contract
Prompt: "What files must my eval loop produce?"
Expected: `evals.json` (the cases, with `should_fire` ground truth), a `firing log`
per case, and `benchmark.json` aggregating precision, recall and output delta. Each
case runs twice — `iteration-N/<id>/with_skill/` and `without_skill/` — and a case
with only `with_skill/` has no baseline.
Failure signs: only with_skill directories; benchmark.json absent.

## E15 — the missing-baseline trap
Prompt: "I ran my skill on ten prompts and it produced great output. Should I ship?"
Expected: No. Without a without_skill baseline you cannot tell whether the skill
helped or the model would have done the same thing alone. Run the baseline first,
then compare. A skill that produces identical output to the baseline did nothing;
a skill that makes output worse is worse than no skill.
Failure signs: only with_skill outputs recorded; "it looks good" as a substitute.

## E16 — the identical-output trap
Prompt: "My skill's output is exactly the same as the baseline on every case. Is
that a good result?"
Expected: No. Identical output means the skill did nothing — the model would have
produced the same answer without it. A skill that makes output worse is worse than
no skill at all. Detection: `scripts/eval_metrics.py delta with_skill without_skill`
prints `FAIL: case X output identical to baseline`.
Failure signs: declaring victory because "the output is correct".

## E17 — tuned and declared on the same set
Prompt: "I tuned my description until every eval passed, then shipped it. What did
I miss?"
Expected: You tuned on the validation set, so the validation set is now part of the
training set. Every case must carry a `split` field (`train` or `val`), and both
splits must be non-empty. Re-split, recruit fresh prompts, re-measure. If train and
validation scores diverge after the re-split, the description is still overfit.
Detection: `scripts/eval_metrics.py split evals.json` prints `FAIL: no case carries
a split field` when the field is absent.
Failure signs: a single eval set used for both tuning and declaring success.

## Near-miss prompts (trigger precision — these should NOT fire this skill)

## N1 — writing a package README
Prompt: "Write a README for my new Python package."
Expected: No. This skill is about *Agent Skills* — folders with `SKILL.md`, YAML front matter, the agentskills.io standard. A README is ordinary documentation; it has no front matter, no trigger description, no eval loop. Use a doc skill or write it directly.
Failure signs: adding YAML front matter to a README; running `validate_skill.py` on it; writing eval prompts for documentation.

## N2 — tuning a model's system prompt
Prompt: "My model's answers are too verbose. Help me rewrite its system prompt."
Expected: No. That is prompt engineering for a single task, not skill authoring. A skill changes *which instructions load*, not the model's base behaviour; if the same instructions should apply to every task, they belong in the system prompt, not in a skill.
Failure signs: putting task-specific instructions into a SKILL.md body and wondering why it fires everywhere.

## N3 — profiling a skill's runtime
Prompt: "My skill's script takes 40 seconds. Can we profile it?"
Expected: No. That is performance debugging of a Python script — `cProfile`, `py-spy`, a profiler. This skill audits *standard compliance and trigger accuracy*, not speed. The determinism rule forbids timing-dependent behaviour, but measuring it is a different discipline.
Failure signs: adding timing assertions to `validate_skill.py`; treating a slow script as a standard violation.
