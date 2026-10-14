# PASS 6 (2026-10-14) — skills-business-de-r3-01 TEST + FIX

Task: `skills-business-de-r3-01` PASS 3 of 3 — prove and repair the ten skills.

## Method
1. `python3 ../scripts/validate.py` (catalog) + `python3 business-de/scripts/validate_skills.py` (standard rules).
2. `python3 -m pytest -q` in `business-de`.
3. Every script run on real inputs (smoke).
4. Each `references/EVALS.md` prompt read against its `SKILL.md`: would the skill change the outcome vs no skill?
5. Two random sources per skill re-fetched (curl) to confirm facts + no verbatim copy.
6. Front matter, links, file sizes re-checked.

## Status (first draft — being filled in below)
- Validators: see results below.
- Tests: see results below.
- Script smoke: see results below.
- EVALS grounding: see results below.
- Source re-fetch: see results below.
