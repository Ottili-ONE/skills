# STATUS — skills-business-de-r3 (Ten Germ)

Last updated: 2026-10-14 (pass 6).

## Task: skills-business-de-r3-01 — Research and design of the ten skills
Acceptance: `RESEARCH.md` + `SOURCES.md` (>=6 primary URLs each) + `DESIGN.md` per skill.

## What works (evidence)
- `python3 ../scripts/validate_skill.py --all` on the 10 business-de skills -> all 10 `ok`, exit 0 (2026-10-14).
- `python3 ../scripts/validate_skills.py <10 dirs>` -> **0 findings** for all 10 (EVALS >=5 prompts, SOURCES links, trigger present, scripts referenced).
- All ten skills have SKILL.md + references/{SOURCES,DESIGN,EVALS}.md + scripts/ + tests/.
- `python3 -m pytest -q` in business-de -> **109 passed**, 0 failed (2026-10-14).
- 24 scripts across the ten skills; every DESIGN.md "Scripts planned" row now exists on disk.

## What is stubbed / missing
- DPD / GLS / Hermes / UPS carrier facts remain **unverified** — partner portals are JS-rendered or bot-protected and require a business contract. carrier-apis-de SOURCES.md marks these rows as "portal not reachable".
- The KoSIT validator JAR could not be fetched (503 on the changelog URL this pass); the element-name mapping in xrechnung-zugferd is the best available but not independently re-verified from source.
- The Art. 50(2) machine-readable marking date (2026-12-02) is a secondary-source date; re-verify against the Omnibus recital before relying on it.
- `scripts/validate.py`, `install.sh` and `build-index.py` at the repo root are owned by `skills-engineering-r3`; until they exist, validation is done with `../scripts/validate_skill.py`.

## This pass (2026-10-14)
- Built the scripts the four skills that had none were missing:
  `carrier-apis-de` (create_label / track_shipment / reconcile_charges),
  `webhooks-safe` (verify_webhook / dedup_event / webhook_forward),
  `publish-reconcile-wp-meta` (publish_post / reconcile_publish),
  `dsgvo-ai-act-labeling` (classify_content / label_check / processing_register).
- Added `## Scripts` sections to all ten SKILL.md so the script list is visible
  at activation time (progressive disclosure).
- Added `sha256_of` to `scripts/common.py` (gobd-archive scripts import it).
- Pinned `webhooks-safe`, `carrier-apis-de`, `publish-reconcile-wp-meta` and
  `dsgvo-ai-act-labeling` in `config/versions.json`.
- Fixed a real bug: `common.load_config` resolved the config path relative to
  the script's own directory instead of the repo root, so every script that
  ran from a sub-directory failed with FileNotFoundError.
- Synced dsgvo DESIGN/EVALS/procedures to the real script names
  (`label_check.py`, not the planned `ai_label_check.py`).
- No false 'done' found this pass; RESEARCH.md close-out table matches the
  filesystem.
