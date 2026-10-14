# HANDOFF — skills/agentic-data (R3, ten skills)

What was done in task `skills-agentic-data-r3-05` (evals, validation, cross-links,
handoff), what to re-verify before shipping, and ideas for the next ten skills.

## What this pass did

1. **Validator green for all ten.** `scripts/validate_skill.py` (per-skill, the
   agentskills.io standard) and `scripts/validate_skills.py` (the legacy whole-repo
   checker) both return exit 0 on all ten folders:
   `python3 scripts/validate_skill.py skills/agentic-data/<name>` and
   `python3 scripts/validate_skill.py --all`.
2. **Cross-links rewritten as machine-checked edges.** Every `## Related skills`
   section now uses `[name](../name/SKILL.md)` links, so
   `scripts/check_related_graph.py --skills skills/agentic-data` reads a real
   graph. The graph is acyclic (verified: 10 nodes, 0 cycle errors). The meta-skill
   `skill-authoring-evals` is the only sink.
3. **EVALS reviewed against each skill.** All ten `references/EVALS.md` already
   carry >=5 realistic prompts (`## E1..En`) and 3 near-miss prompts (`## N1..N3`);
   the near-misses were audited for trigger precision (they name the *neighbour*
   protocol and assert the skill must NOT fire). Counts: mcp 12/3, browser 11/3,
   computer-use 10/3, polite-crawling 11/3, dedup 12/3, deep-research 16/3,
   llm-judge 14/3, trajectory 14/3, verifiable-env 15/3, skill-authoring 17/3.
4. **Version facts re-verified live today (2026-10-14).** Re-fetched with curl
   (HTTP 200 everywhere): MCP 2026-07-28 changelog + SEP-2575 + SEP-2663,
   Playwright 1.64.0 on PyPI, datasketch 2.0.0 `affine32` note, RFC 9309 text,
   agentskills spec repo, Playwright class-page docs. No drift vs. the pinned
   values; `references/PASS5-R3-05-REVERIFY.md` was already up to date.
5. **README.md** written (one-line value per skill, install hints, layout).

## What to re-verify before shipping

- **MCP revision.** `2026-07-28` is pinned as primary. Re-fetch
  `https://modelcontextprotocol.io/specification/2026-07-28/changelog` after every
  new release tag; if a newer revision lands, the three fallback versions
  (2025-11-25, 2025-06-18) and the compat matrix in `mcp-2026-07-28/references/`
  need a re-check, and the skill's `compatibility:` line must be bumped.
- **Playwright / datasketch versions.** Both are pinned in
  `browser-agent-playwright` and `dedup-decontam`. PyPI is the live primary;
  re-check on the first run of the week.
- **RFC 9309 and WARC 1.1 (ISO 28500:2017).** RFC text is the working primary;
  `iso.org/standard/82833.html` is bot-blocked (403) and stays recorded as such.
- **EVALS prompt realism.** The prompts are written, not executed (this repo has no
  live agent harness). Re-read each `## E1..En` against its skill body and ask:
  would a competent agent who has *not* read the skill answer it the way the
  expected-behaviour column says? Where a script exists (see below), run it on a
  real input and paste the output into the eval as evidence.
- **Run the scripts that have tests.** `skills/agentic-data/tests/` exists; run
  `python3 -m pytest skills/agentic-data/tests -q` after any change to a skill's
  `scripts/` folder.
- **Bypass register.** `skill-authoring-evals` owns the bypass register for the
  confirm()/coordinate-scaling gates in `computer-use-drivers` and the verifier
  patterns in `verifiable-environments`. If those registers are empty, the skills
  are not yet trustworthy — that is a known gap, not a done item.

## Ideas for the next ten skills (with rationale)

Ordered by dependency: skills lower in the list may build on ones above.

1. **`data-pipeline-engineer`** — build the ingest/transform/quality-gate pipeline
   that feeds training and eval corpora *into* the dedup step.
   *Rationale:* `dedup-decontam` is a filter, not a pipeline; nothing in this set
   covers schema enforcement, sampling strategy, or quality gates before dedup.
2. **`vector-store-retrieval`** — embed, index and retrieve for RAG: chunking
   strategies, hybrid search, re-ranking, and eval of retrieval quality.
   *Rationale:* `dedup-decontam` mentions embeddings only for decontamination;
   retrieval is a first-class agent capability with its own failure modes.
3. **`prompt-injection-red-team`** — methodology for systematically probing a
   prompt (and a system prompt) for injection, with a planted-payload pass/fail
   register like the one in `dedup-decontam`.
   *Rationale:* `browser-agent-playwright` defends page content at one surface;
   red-teaming is the *method* that earns that defense, and it is currently
   unwritten.
4. **`agent-eval-harness`** — run an agent end-to-end on a fixed set of prompts,
   capture the trajectory, score it, and report the with_skill/without_skill
   baseline.
   *Rationale:* `llm-judge-calibration` calibrates the *judge*; `skill-authoring-evals`
   authors *prompts*; the harness that wires them together and records the run in
   `trajectory-ledger` is missing. Depends on all three.
5. **`agent-cost-budget`** — token/call/latency budgeting for a run: pre-flight
   estimates, hard caps, per-step cost ledger, and "stop and ask" thresholds.
   *Rationale:* `trajectory-ledger` records cost as a field; budgeting is the
   *decision surface* that uses it, and it has no skill.
6. **`agent-secrets`** — obtain, scope, rotate and redact credentials an agent may
   need, with the principle that secrets never enter the model context.
   *Rationale:* the safety rules forbid touching `.env`/keys, but no skill tells an
   agent *how* to get a secret safely when one is genuinely required.
7. **`agent-observability`** — live distributed tracing for agent runs
   (OpenTelemetry-shaped): spans, logs, metrics, and alerting on run-level SLOs.
   *Rationale:* `trajectory-ledger` is append-only *audit*; tracing is *live*
   debugging, and the two are often confused.
8. **`data-labeling`** — human-in-the-loop annotation pipelines: gold-set creation,
   inter-annotator agreement, disagreement resolution, and label quality audit.
   *Rationale:* `llm-judge-calibration` scores *with* a rubric; labeling *produces*
   the gold data the rubric is compared against. Distinct workflow, distinct tooling.
9. **`training-data-compliance`** — PII/PHI scrubbing, copyright and licence
   filtering, and jurisdiction-aware consent checks *before* dedup.
   *Rationale:* `dedup-decontam` handles test-set leakage, not legal compliance;
   the two are easy to conflate and both are commonly skipped.
10. **`agent-handoff`** — explicit agent-to-agent handoff contract: state
    serialization, resume tokens, capability negotiation, and the "who owns what
    now" protocol.
    *Rationale:* `browser-agent-playwright` has a browser↔code handoff; generalising
    to agent↔agent (and to `mcp-2026-07-28` tool consumers) is the natural next
    protocol-level skill, and it would sit beside `trajectory-ledger` as the
    provenance consumer.
