# Eval artefact schema — skill-authoring-evals

Verified 2026-10-12 against https://agentskills.io/skill-creation/evaluating-skills
(HTTP 200). The eval loop produces four artefacts. This file is the contract for
what each one must contain and how they fit together.

## `evals.json` (input — the test cases)

```json
[
  {
    "id": "E1",
    "prompt": "My skill folder is `my-skill` but the frontmatter says `name: other`. What happens?",
    "should_fire": true,
    "expected_output": "The skill never registers; the folder name and name field must match.",
    "files": ["SKILL.md"]
  }
]
```

| Field | Type | MUST | Notes |
|-------|------|------|-------|
| `id` | string | yes | unique within the file; referenced by benchmark.json |
| `prompt` | string | yes | realistic user phrasing, not the author's prose |
| `should_fire` | boolean | yes | the ground-truth label |
| `expected_output` | string | yes | the failure sign or the correct behaviour |
| `files` | array of strings | no | files the skill must touch |

## `benchmark.json` (output — aggregated metrics)

```json
{
  "skill": "my-skill",
  "date": "2026-10-12",
  "precision": 0.93,
  "recall": 0.87,
  "target_precision": 0.9,
  "target_recall": 0.9,
  "train_split": 0.7,
  "cases": [
    {"id": "E1", "should_fire": true, "fired": true, "delta_tokens": 412}
  ]
}
```

## Workspace layout per iteration

```
iteration-N/
  E1/
    with_skill/
      output.md
      timing.json
    without_skill/
      output.md
      timing.json
  benchmark.json
```

Every case gets both directories. A case with only `with_skill/` has no baseline.

## Metrics — exact formulas

| Metric | Formula | Target | Below target means |
|--------|---------|--------|--------------------|
| **Precision** | should-fire prompts that fired / (should-fire that fired + should-not-fire that fired) = TP / (TP + FP) | >= 0.9 | description too broad |
| **Recall** | should-fire prompts that DID fire / all should-fire | >= 0.9 | description too narrow |
| **Output delta** | tokens(with_skill) - tokens(without_skill), per case | > 0 for useful cases | skill changed nothing |

If precision and recall are both below 0.8, rewrite the description, not the body —
the body is not the trigger.

## Train/validation split

Split 70/30. Tune the description on the training set; measure on the validation set.
If train and validation scores diverge by more than 0.15, the description is overfit to
the training phrasing — recruit fresh prompts and re-split. Tuning until the validation
set passes makes the validation set part of the training set; re-split afterwards.

## Ordered procedure
1. Author `evals.json` with should-fire and should-not-fire cases.
2. Split 70/30 train/validation.
3. Run every case without the skill -> baseline in `without_skill/`.
4. Run every case with the skill -> `with_skill/`.
5. Compute precision, recall, output delta per case; aggregate in `benchmark.json`.
6. Identify the weakest section (lowest recall or lowest delta).
7. Rewrite that section; re-run evals; re-validate. Never ship untested.

## Near-miss triggers
- Only `with_skill/` directories present -> no baseline; a skill that does nothing
  looks identical to a skill that works.
- All prompts are the author's own phrasing -> overfit; recruit fresh prompts.
- A single eval set used for both tuning and declaring success -> re-split.
- Shipping because "it looks good" -> the evals were never run.
