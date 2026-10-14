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
   SKILL.md text must be updated *before* the skill is used. The MCP 2026-07-28
   sources were re-verified live on 2026-10-14 (all HTTP 200); that is the
   newest verification in this area.
2. **Run the validator on every skill, not just the acceptance checker.**
   `python3 <skill>/scripts/validate_skill.py <skill>` (exit 0 = pass). The
   root `scripts/acceptance_check.py` counts URLs and lines but cannot see a
   dangling reference link or a non-slug folder name — the per-skill validator
   can. All ten were green at last run (31/22/20/29/24/29/22/22/20/25 oks, 0
   fails).
3. **Run the test suite.** `python3 -m pytest skills/agentic-data/ -q`. At the
   last full run 277 tests passed. A skill whose scripts are exercised by tests
   is a skill that was actually run against real inputs; a script with no test
   is a claim, not evidence.
4. **Re-execute the EVALS.md prompts mentally, then for real.** Each EVALS.md
   has >= 10 prompts (>= 5 required). Read each one as if you were the agent
   receiving it, check the expected behaviour against the SKILL.md procedure,
   and where a script exists, run it on the fixture named in the prompt. The
   prompts in `references/EVALS.md` are the minimum; the near-miss prompts
   added in this pass (three per skill, in a `## Near-miss prompts` section at
   the end of each EVALS.md) are the ones that test the *trigger*, not the
   procedure — they ask "would this skill fire on a request it should not
   handle?" and are the cheapest way to find a description that is too broad.
5. **Check the description still triggers.** The `description:` field in the
   front matter is the trigger, not a summary. If a skill stops firing after a
   code change, the fix is in the description (add the concrete symptom the
   agent actually typed), never in the body. See
   `skill-authoring-evals/references/trigger-evals.md` for the measurement
   procedure (two labelled sets, precision/recall >= 0.9, train/validation
   split).

## Ideas for the next ten skills (with rationale)

The ten skills here cover *data and research* work for agents. The obvious
next set is the complementary **operations / platform** set — the skills an
agent needs to actually *do* the work these skills measure. In rough priority
order:

1. **`ci-failure-triage`** — parse a failing CI run (log, stack trace, exit
   code), classify the failure class (flaky / dependency / test / code / env),
   and produce a ranked list of hypotheses with the exact command to
   reproduce. Rationale: agents burn the most time on CI failures, and the
   `trajectory-ledger` skill here provides the schema for recording the run.
2. **`secret-scanning-policy`** — scan a diff for secrets using regex +
   entropy + provider API patterns, with a policy file that says which
   findings are block-vs-warn. Rationale: agents routinely paste credentials
   into tool calls; this is the one place a *pre-commit* gate pays off.
3. **`cost-optimizer`** — given a workload (tokens, tool calls, wall time),
   recommend model/provider routing and batch sizing, with a cost ledger
   format compatible with `trajectory-ledger`. Rationale: `llm-judge-calibration`
   measures quality but nobody measures billable minutes.
4. **`offline-knowledge-base`** — build a RAG-able snapshot of a repository
   (tree, key files, symbols) that survives when the network is down.
   Rationale: `deep-research-method` assumes connectivity; agents in CI often
   do not have it.
5. **`incident-commander`** — run a structured incident loop (declare,
   hypothesise, test, update, resolve) with a status page and a decision
   log. Rationale: `trajectory-ledger` records runs; this one records *the
   human-visible state* during an incident.
6. **`data-contracts`** — define and validate JSON/Parquet schemas for data
   pipelines, with drift detection between consecutive runs. Rationale:
   `dedup-decontam` cleans data; this one keeps it honest over time.
7. **`eval-harness-builder`** — the *user-facing* wrapper around
   `verifiable-environments`: turn a spec into a runnable harness with a
   bypass register and calibration. Rationale: the skill here is for the
   *designer* of verifiers; most agents need the *operator* version.
8. **`web-research-orchestrator`** — parallelise `deep-research-method`
   across sub-questions, merge the scored sources, and produce a brief with
   a confidence ladder. Rationale: the single-threaded version is correct but
   slow; research questions are embarrassingly parallel.
9. **`skill-marketplace`** — search, compare and install skills from a
   registry, with a pre-install audit (front matter, reference links, script
   determinism). Rationale: `skill-authoring-evals` audits skills you wrote;
   this audits skills you *downloaded*.
10. **`agent-cost-guard`** — a per-run budget (tokens, USD, wall seconds)
    that warns at 50/80/100% and hard-stops at the cap, recorded in the
    `trajectory-ledger` cost ledger. Rationale: an agent that does not know
    its budget will use it all on the first sub-task.

If the next set is instead **security**, the strongest candidates are a
prompt-injection red-team skill (complementary to `browser-agent-playwright`
and `computer-use-drivers`, which already handle hostile page content) and a
supply-chain audit skill (SBOM, lockfile, provenance).
