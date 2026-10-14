# SOURCES — skill-authoring-evals

Retrieval date 2026-10-12. Every URL below was fetched live on that date.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://agentskills.io/specification.md | The Agent Skills format specification: directory structure, SKILL.md frontmatter fields (name ≤64 chars lowercase-hyphenated, description ≤1024 chars, license, compatibility, metadata, allowed-tools), optional scripts//references//assets/, progressive disclosure, file-reference rules | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 2 | https://agentskills.io/skill-creation/optimizing-descriptions | How skill triggering works, writing effective descriptions (imperative phrasing, user intent not implementation, pushy-but-not-broad), trigger eval queries with should-trigger/should-not-trigger labels, train/validation split to avoid overfitting | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 3 | https://agentskills.io/skill-creation/evaluating-skills | Eval methodology: evals/evals.json shape (id, prompt, expected_output, files), running each case with_skill and without_skill for a baseline, workspace layout iteration-N/<eval>/with_skill|without_skill, timing.json, grading.json, benchmark.json, grading principles, human review loop | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 4 | https://agentskills.io/skill-creation/best-practices | Well-scoped, calibrated skills: progressive disclosure (name+description at startup, body on activation, referenced files on demand), scripts that are deterministic and offline, keeping SKILL.md under ~5,000 tokens | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 5 | https://agentskills.io/skill-creation/using-scripts | Bundling executable scripts in skills: paths relative to the skill root, shebang + executable bit, deterministic output, machine-readable to stdout / human detail to stderr, no network at validation time | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 6 | https://agentskills.io/clients.md | Client implementations that support the standard: confirms the field set is portable across Claude Code, Codex, Cursor, Gemini CLI, VS Code/Copilot | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 7 | https://github.com/anthropics/skills | Anthropic's reference skills repo: folder+SKILL.md layout, template-skill, document/pptx/xlsx skills as complex examples, Apache-2.0 licensing convention | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 8 | https://github.com/openai/skills | OpenAI's Codex skills repo (now deprecated, redirects to openai/plugins): confirms .system/.curated/.experimental tiers and the $skill-installer flow | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | the repo is deprecated; use openai/plugins for new work |
| 9 | https://fast.io/resources/awesome-claude-skills-directory-2026/ | Ecosystem size: ~24,400 repos with skill definitions (June 2026) — the reason generic skills are everywhere and Ottili skills must be specific and evidence-based | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 10 | https://agentskills.io/llms.txt | Documentation index used to discover the pages above; confirms the canonical URL layout (skill-creation/*.md, clients.md, specification.md) | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

## Version-sensitive facts
- The Agent Skills specification is the current standard as of 2026-10-12. The
  `allowed-tools` field is marked **experimental**; do not depend on it for gating.
- Description length limit is a hard 1024 characters; name limit is 64 characters with
  the lowercase-alphanumeric-hyphen rule (no leading/trailing hyphen, no `--`).
- The eval methodology (evals/evals.json, with_skill/without_skill baseline, iteration-N
  workspace) is the agentskills.io convention as of 2026-10-12; re-check on update.

## Conflicts
- Source 8 (openai/skills) is deprecated and redirects to openai/plugins; the field rules
  are identical, so it is retained as a historical reference only.
- No content conflicts between the specification and the four skill-creation guides.

## Sources added in EXPAND pass (2026-10-12)

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 11 | https://agentskills.io/skill-creation/evaluating-skills | The eval artefact contract: `evals.json` shape (id, prompt, should_fire, expected_output, files), the `benchmark.json` aggregation, the `iteration-N/<eval>/with_skill\|without_skill` layout, `timing.json` and `grading.json` | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 12 | https://agentskills.io/skill-creation/optimizing-descriptions | The trigger-eval methodology: should-trigger/should-not-trigger labels, train/validation split, precision and recall targets, the with_skill/without_skill baseline | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |

## Version-sensitive facts added
- The eval artefact contract is `evals.json` (cases) + a firing log per case +
  `benchmark.json` (aggregated precision, recall, output delta). A case with only a
  `with_skill/` directory has no baseline and the run is invalid.
- Precision = should-fire prompts that fired / (should-fire that fired + should-not-fire
  that fired). The denominator is the number of *fired* cases, not the number of correct
  negatives — `tn/(tn+fp)` is the common mistake.
- Targets are precision >= 0.9 and recall >= 0.9. Below 0.8 on either, rewrite the
  description, not the body.

## Re-verification 2026-10-14 (PASS 4 re-run)

Live re-fetch of all 12 primary URLs recorded in this SOURCES.md, 2026-10-14, via curl (max-time 25 s, parallel workers=6). Machine-readable report: `../../scratch/skills/skills-agentic-data-r3/reverify_02.json`.

| URL | HTTP | Final URL |
|-----|------|-----------|
| https://agentskills.io/specification.md | 200 | https://agentskills.io/specification.md |
| https://agentskills.io/skill-creation/optimizing-descriptions | 200 | https://agentskills.io/skill-creation/optimizing-descriptions |
| https://agentskills.io/skill-creation/evaluating-skills | 200 | https://agentskills.io/skill-creation/evaluating-skills |
| https://agentskills.io/skill-creation/best-practices | 200 | https://agentskills.io/skill-creation/best-practices |
| https://agentskills.io/skill-creation/using-scripts | 200 | https://agentskills.io/skill-creation/using-scripts |
| https://agentskills.io/clients.md | 200 | https://agentskills.io/clients.md |
| https://github.com/anthropics/skills | 200 | https://github.com/anthropics/skills |
| https://github.com/openai/skills | 200 | https://github.com/openai/skills |
| https://fast.io/resources/awesome-claude-skills-directory-2026/ | 200 | https://fast.io/resources/awesome-claude-skills-directory-2026/ |
| https://agentskills.io/llms.txt | 200 | https://agentskills.io/llms.txt |
| https://www.iso.org/standard/82833.html | 403 | https://www.iso.org/standard/82833.html |
| https://api.github.com/repos/modelcontextprotocol/specification | 200 | https://api.github.com/repositories/862570523 |

**Dead / blocked on 2026-10-14:**

- `https://www.iso.org/standard/82833.html` -> HTTP 403. iso.org serves a 403 bot-block to curl; the WARC 1.1 spec text is the working primary and this page is corroborating only. Recorded as a known dead URL, not a fact drift.


## Re-verification 2026-10-14 (PASS 2 — skills-agentic-data-r3-02)
All primary URLs re-fetched live with curl on 2026-10-14. Every URL below
returned HTTP 200; no new dead links, no fact drift vs the 2026-10-13 record.

| URL | Code |
|-----|------|
| https://modelcontextprotocol.io/specification/2026-07-28/changelog | 200 |
| https://modelcontextprotocol.io/specification/2025-11-25/changelog | 200 |
| https://modelcontextprotocol.io/specification/2025-06-18/changelog | 200 |
| https://modelcontextprotocol.io/specification/2026-07-28/deprecated | 200 |
| https://github.com/modelcontextprotocol/specification/releases/tag/2026-07-28 | 200 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2575-stateless-mcp.md | 200 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2663-tasks-extension.md | 200 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/1686-tasks.md | 200 |
| https://github.com/modelcontextprotocol/python-sdk | 200 |
| https://api.github.com/repos/modelcontextprotocol/specification | 200 |
| https://agentskills.io/specification.md | 200 |
| https://agentskills.io/skill-creation/optimizing-descriptions | 200 |
| https://agentskills.io/skill-creation/evaluating-skills | 200 |
| https://agentskills.io/skill-creation/best-practices | 200 |
| https://agentskills.io/skill-creation/using-scripts | 200 |
| https://agentskills.io/clients.md | 200 |
| https://agentskills.io/llms.txt | 200 |
| https://github.com/anthropics/skills | 200 |
| https://github.com/openai/skills | 200 |
| https://docs.anthropic.com/en/docs/agents-and-tools/computer-use | 200 |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer_toolset_20260801.json | 200 |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/computer-toolset.md | 200 |

**Version-sensitive fact re-confirmed on 2026-10-14:** the live
`computer_toolset_20260801.json` still carries exactly **17 members**
(`key`, `hold_key`, `type`, `cursor_position`, `mouse_move`, `left_mouse_down`,
`left_mouse_up`, `left_click`, `left_click_drag`, `right_click`,
`middle_click`, `double_click`, `triple_click`, `scroll`, `wait`,
`screenshot`, `zoom`) with `default_disabled: []`. The vendored fixture
`fixtures/registry_20260801.json` matches it member-for-member, so the 17-member
registry in the skill is current and the 16-member drift trap in EVALS E7 is a
real near-miss, not a hypothetical.
