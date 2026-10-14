# Worked examples — skill-authoring-evals

Detection signal: what in the artefact tells you the standard was followed or
violated. Each example ends with the check that would have caught it.

## Good — folder and `name` field agree

`skills/my-skill/SKILL.md`:
```yaml
---
name: my-skill
description: "Use this skill when an agent must author an Agent Skill, audit an existing one, or measure whether a skill fires on the prompts it should."
---
```

Detection signal: `os.path.basename(folder) == front_matter['name']`.

## Bad — the most common silent failure

Folder `my-skill`, `name: my_skill`. The skill never registers; the platform
looks it up by folder name, finds nothing, and reports no error.

Detection signal: folder name != `name` field. Fix before anything else.

## Bad — description so broad it fires on everything

`description: "Helps with tasks."` Fires on every prompt; the skill's content
then has to do generic work it was not designed for.

Detection signal: a should-not-fire prompt in the eval set fires. Narrow the
description, do not widen the body.

## Bad — evals with no without_skill baseline

Only `with_skill/` outputs recorded. A skill that does nothing is
indistinguishable from a skill that works.

Detection signal: `benchmark.json` has no `without_skill` key. Every case must
run twice.

## Good — precision computed the right way

Should-fire: 8, fired: 7. Should-not-fire: 5, fired: 1.
Precision = tp/(tp+fp) = 7/(7+1) = 0.875.
The wrong formula tn/(tn+fp) = 4/5 = 0.80 reports a lower number for the same
 behaviour, which is why `scripts/eval_metrics.py` pins the formula.

Detection signal: precision denominator is the number of *fired* cases.
