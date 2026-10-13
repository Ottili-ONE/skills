# DESIGN: llm-judge-calibration

## Why this skill exists
A single judge run produces a number, and a number is not evidence. The
difference between a score you can cite and a score you cannot is whether the
judge was separated from the generator, whether the rubric was written before
any scoring happened, and whether the agreement was measured on a set the
rubric was never tuned on. Most "calibrated" judges fail at least one of
those three, usually silently. This skill makes the three conditions a gate.

## Trigger description (SKILL.md description draft, <=1024 chars)
"Calibrate LLM judges: rubrics, calibration sets, inter-annotator agreement, drift
detection and judge/teacher separation. Use when an agent must build or audit an
LLM-as-judge scoring pipeline; not for building a single rubric from scratch."

## The three hard decisions

### 1. Judge/teacher separation is not a nicety
The scoring model must not be the generator, and ideally not even share a
prompt. A judge that grades its own outputs is circular by construction: it
will agree with itself, and the agreement number will look excellent. Record
the judge model, the generator model and both prompt hashes in every report —
if the hashes are not recorded, the score is unverifiable even in principle.

### 2. The rubric is written before any scoring
Each score point gets a definition and at least one example of each level.
Points without examples are ambiguous, and ambiguity shows up as 20+ point
spread on re-annotation: two annotators reading the same rubric land on
different scales and the agreement number is garbage. The rubric is also
linted before calibration (`scripts/rubric_lint.py` rejects rubrics whose
definitions, examples or anti-examples are missing, whose scores are not
strictly increasing, or whose scale does not start at 1).

### 3. The calibration set is held out, and the threshold is derived from it
The pass threshold is the value that yields the target pass rate *on the
calibration set*. It is never fitted to make a specific agent pass — fitting
the threshold to an agent is the same error as fitting a test to a result,
and it destroys the meaning of the pass rate. The calibration set is
versioned so drift can be measured against it.

## Thresholds (from the SKILL.md decision table)
- **Agreement** (Fleiss' kappa / Krippendorff's alpha): >=0.6 usable;
  0.4-0.6 fix the rubric; <0.4 unusable.
- **Drift**: mean shift 0-0.2 = stable; 0.2-0.3 = watch; >0.3 = re-calibrate
  or retire. Agreement drop >0.1 also triggers re-calibration.
- **Position bias**: 0-0.3 acceptable; >0.5 on a 5-point scale = aggregate
  scores across shuffles.

## Scripts shipped
- `scripts/calibrate_judge.py` — given a rubric, a calibration set with gold
  labels and judge outputs, reports agreement, position bias, drift and the
  derived threshold.
- `scripts/rubric_lint.py` — rejects rubrics that are missing definitions,
  examples or anti-examples, or whose scores are not strictly increasing.
- `scripts/gen_rubric.py` — scaffold a rubric from a set of example outputs.

## What this skill does better than a generic agent
A generic agent trusts a single judge run. This skill separates judge from
teacher, requires per-level rubric examples, measures agreement on a held-out
set, checks position bias by shuffling, and schedules drift re-checks. It
prevents the common incident of a "calibrated" judge whose agreement was
measured on the very set the rubric was tuned on.

## What existing public skills do (and what this one does differently)

Surveyed on 2026-10-12. `anthropics/skills` ships no evaluation skill. The
Fastio 2026 directory lists `Code-Reviewer` (severity-tagged findings) and
`Design Auditor`, which are *judges of artefacts*, not calibrated judges of
agent output. `skills.cat` carries no judge-calibration entry. The public
material that exists (OpenAI evals repo, DeepSeek's JudgeLM, Prometheus/GLEAM
papers) is research code, not a skill.

This skill is the only one that treats the judge itself as an instrument that
must be calibrated:
- **Judge/teacher separation**: the judge is never the system under test and
  never self-judges. A judge that grades its own outputs is circular by
  construction.
- **Rubric lint before calibration**: `scripts/rubric_lint.py` rejects
  rubrics whose definitions, examples or anti-examples are missing, whose
  scores are not strictly increasing, or whose scale does not start at 1.
- **Calibration set with known ground truth**: `scripts/calibrate_judge.py`
  computes agreement against human-labelled rows and reports pass/fail
  against the thresholds above.
- **Drift control**: the calibration set is versioned; a judge whose scores
  drift against it is re-calibrated or retired, not trusted.
- **Robustness probes**: `references/robustness.md` defines the perturbation
  battery (paraphrase, reorder, negate, insert noise) a judge must survive to
  be usable.

## Near-miss triggers
- Judge and generator are the same model -> agreement is circular.
- Rubric has no per-level examples -> ambiguous, low agreement.
- Calibration set is the training set -> overfit, does not transfer.
- Agreement measured on a set the rubric was tuned on -> inflated.
- A score moves when neighbours change -> position bias present.
- Drift >0.3 or agreement drops >0.1 since last week -> re-calibrate.
- Threshold fitted to make a specific agent pass -> the pass rate is meaningless.
