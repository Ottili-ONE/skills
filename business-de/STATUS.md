# STATUS — skills-business-de-r3 (Ten Germ)

Last updated: 2026-10-14 (pass 6).

## Task: skills-business-de-r3-01 — Research and design of the ten skills
Acceptance: `RESEARCH.md` + `SOURCES.md` (>=6 primary URLs each) + `DESIGN.md` per skill.

## What works (evidence)
- `python3 ../scripts/validate_skill.py --all` on the 10 business-de skills -> all 10 `ok`, exit 0 (2026-10-14).
- `python3 ../scripts/validate_skills.py <10 dirs>` -> 0 findings for all 10 (EVALS >=5 prompts, SOURCES links, trigger present).
- All ten skills have SKILL.md + references/{SOURCES,DESIGN,EVALS}.md + scripts/ + tests/.
- `python3 -m pytest -q` in business-de -> **result below** (running).

## What is stubbed / missing
- DPD / GLS / Hermes / UPS carrier facts remain **unverified** — partner portals are JS-rendered or bot-protected and require a business contract. carrier-apis-de SOURCES.md marks these rows as "portal not reachable".
- The KoSIT validator JAR could not be fetched (503 on the changelog URL this pass); the element-name mapping in xrechnung-zugferd is the best available but not independently re-verified from source.
- The Art. 50(2) machine-readable marking date (2026-12-02) is a secondary-source date; re-verify against the Omnibus recital before relying on it.
- `scripts/validate.py`, `install.sh` and `build-index.py` at the repo root are owned by `skills-engineering-r3`; until they exist, validation is done with `../scripts/validate_skill.py`.

## This pass (2026-10-14)
- Re-verified state: all ten skills pass standard validation + content validation.
- Running full test suite to confirm 212+ tests still green.
- No false 'done' found this pass; RESEARCH.md close-out table matches the filesystem.
