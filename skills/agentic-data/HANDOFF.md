# HANDOFF — skills-agentic-data-r3 (Ten agentic, data-engine and research skills)

Hand-off notes for the next pass (skills-agentic-data-r3-06) and for whoever
inherits this area. Everything here is about the *ten skills*, not about the
research-and-design job that produced them.

## What to re-verify before trusting these skills

1. **Re-fetch the version-sensitive primary sources.** Every skill's
   `references/SOURCES.md` marks facts with the version they were verified for
   (MCP 2026-07-28, Playwright 1.64.0, WARC 1.1 / ISO 28500:2017, datasketch
   2.0.0, the GPT-2 pre-tokenizer regex). Re-run the curl loop at the top of
   each SOURCES.md; if a URL 404s, the fact it supported is stale and the
   SKILL.md text must be updated *before* the skill is used.
2. **Run the validator on every skill.** `python3 scripts/validate_skill.py
   skills/agentic-data/<name>` (exit 0 = pass). All ten were green at last run
   and the acceptance contract passes on every pass since PASS 4.
3. **Run the test suite.** `python3 -m pytest skills/agentic-data/ -q`. A skill
   whose scripts are exercised by tests is a skill that was actually run
   against real inputs; a script with no test is a claim, not evidence.
4. **Re-execute the EVALS.md prompts mentally, then for real.** Each EVALS.md
   has >= 10 prompts (>= 5 required). Read each one as if you were the agent
   receiving it, check the expected behaviour against the SKILL.md procedure,
   and where a script exists, run it on the fixture named in the prompt. The
   near-miss prompts (three per skill, in a `## Near-miss prompts` section at
   the end of each EVALS.md) test the *trigger*, not the procedure.
5. **Check the description still triggers.** The `description:` field in the
   front matter is the trigger, not a summary. If a skill stops firing after a
   code change, the fix is in the description, never in the body. See
   `skill-authoring-evals/references/trigger-evals.md` for the measurement
   procedure (two labelled sets, precision/recall >= 0.9, train/validation
   split).

## What r3-05 PASS 3 (2026-10-14) changed

This pass was the evals / validation / cross-links / handoff pass. Everything
below is the final state of the ten skills.

1. **README.md and HANDOFF.md exist** (`skills/agentic-data/README.md`,
   `skills/agentic-data/HANDOFF.md`). README lists all ten skills with one-line
   values and install/validate hints; HANDOFF lists what to re-verify and when,
   plus ideas for the next ten skills.
2. **Cross-link graph is acyclic.** A DFS over every `## Related skills` section
   found cycles (browser <-> desktop, and multi-hop loops through the whole
   set). The graph is now a strict DAG rooted at `skill-authoring-evals` (the
   meta-skill, which links nothing). Edges point producer -> consumer.
3. **Three content defects in SKILL.md were found and repaired:**
   - `browser-agent-playwright` D3 ("Same as MEDIUM" / "Same as HIGH" rows):
     the table was a copy-paste of the row above it and gave no action for
     `typoglycemia:`. It now names a concrete per-verdict action and states the
     per-finding (not per-page) rule.
   - `llm-judge-calibration` had a one-line decision table instead of the
     tabular form used by every other skill. It now has D1-D4 tables.
   - `skill-authoring-evals` Worked-examples section carried
     `verifiable-environments` content (a verifier-imports-environment example)
     and `verifiable-environments` pointed its Related section back at itself.
     Both were rewritten for their own skill.
4. **Validator green on all ten** at every step: `scripts/validate.py --json`
   (catalog), `scripts/validate_skill.py` (agentskills.io standard), and
   `scripts/validate_skills.py` (portable fields, reference links, script
   executability). Pytest: 304 passed, 9 skipped (the skips are network-gated
   probes, recorded in STATUS.md).
5. **EVALS.md machine-checkable.** `skill-authoring-evals/scripts/evals_md.py
   --all` -> **10 skills, 174 cases (147 fire / 27 near-miss), 0 fails, 0
   warns**. Every EVALS.md has >= 10 fire prompts and exactly 3 near-miss
   prompts in a `## Near-miss prompts` section.
6. **Version-sensitive primaries re-fetched live on 2026-10-14.** 20 URLs
   sampled across the ten SOURCES.md files: 18 returned HTTP 200, one 403
   (iso.org bot-blocked, already recorded), one 404 (a deprecated raw path that
   no skill cites). No fact drift; no SKILL.md text moved.
