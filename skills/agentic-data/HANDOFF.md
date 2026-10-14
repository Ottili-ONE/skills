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
