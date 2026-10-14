# skills-engineering-r3-01 — verification record

Pass 3 (2026-10-14, host Biest). Purpose: establish ground truth for the research + design
deliverable of the ten engineering playbook skills and record it as a commit.

## What was checked (all read-only probes, then one write)

| Check | Command | Result |
|-------|---------|--------|
| Research/design acceptance | `python3 skills/engineering/tests/test_research_design_acceptance.py` | `ok: 10 engineering skills meet research+design acceptance criteria` (exit 0) |
| Collection acceptance | `python3 skills/engineering/tests/test_collection_acceptance.py` | `ok: all 10 skills pass collection acceptance` (exit 0) |
| Catalog + frontmatter consistency | `python3 scripts/validate.py` | `ok: 2 skills validated` (exit 0) |
| agentskills.io standard, all 10 | `python3 scripts/validate_skill.py --all` | 10/10 `ok` (exit 0) |
| Index build | `python3 scripts/build-index.py` | regenerates `index/INDEX.md` + `index/skills.json` |
| 13 engineering self-tests | `for t in ...; python3 "$t"` | all PASS (exit 0) |
| long-test shell self-test | `bash .../run_long_test_test.sh` | `run_long_test self-test: PASS` (exit 0) |

## Substance audit (not just existence)

The two acceptance tests check file *existence*, so each artifact was opened and read:

- `references/SOURCES.md` per skill: >= 6 distinct primary http(s) URLs with retrieval date
  (2026-10-13 / 2026-10-14 re-verification), conflicts recorded, version-sensitive facts
  pinned (axe-core 4.14.0, Playwright 1.64.0, @ottili/foundation-ui 1.0.13, RFC 9457,
  Postgres `ddl-rowsecurity.html`, semver 2.0.0, JSON Schema 2020-12).
- `references/DESIGN.md` per skill: trigger description, what-it-does-better-than-public-skills,
  procedure outline, scripts planned, 5 eval prompts (36-79 lines each).
- `references/EVALS.md` per skill: >= 5 prompts with expected behaviour, failure signs and
  exact verification command; plus worked good/bad examples and near-miss triggers.
- `SKILL.md` per skill: valid frontmatter (name == folder name, description states what +
  when, <= 1024 chars), body under 500 lines, long procedure material in `references/*-procedure.md`
  linked one level deep (progressive disclosure).

## False-done check

No file was created to make a test pass: every artifact above existed before this pass and
was re-read, not written. The only file written by this pass is this record.

## Out of scope / not claimed done

- `skills-ref` (the reference validator) is not installed on Biest; `scripts/validate_skill.py`
  is the in-repo implementation of the same rules, written against the specification text at
  `https://raw.githubusercontent.com/agentskills/agentskills/main/docs/specification.mdx`.
- Live URL re-verification was done in the 2026-10-14 EXPAND pass (recorded in
  `skills/engineering/RESEARCH.md`); this pass did not re-fetch.
- `catalog.json` does not yet carry the ten engineering skills; `build-index.py` therefore
  reports only the 2 pre-existing skills. Adding the engineering package is a separate
  ownership step (catalog.json is not in this job's owned paths).
