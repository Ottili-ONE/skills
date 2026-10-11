# SOURCES — skill-authoring-evals

Retrieval date 2026-10-12. Every URL below was fetched live on that date.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://agentskills.io/specification.md | The Agent Skills format specification: directory structure, SKILL.md frontmatter fields (name ≤64 chars lowercase-hyphenated, description ≤1024 chars, license, compatibility, metadata, allowed-tools), optional scripts//references//assets/, progressive disclosure, file-reference rules | fetched 2026-10-12 (HTTP 200) | none |
| 2 | https://agentskills.io/skill-creation/optimizing-descriptions | How skill triggering works, writing effective descriptions (imperative phrasing, user intent not implementation, pushy-but-not-broad), trigger eval queries with should-trigger/should-not-trigger labels, train/validation split to avoid overfitting | fetched 2026-10-12 (HTTP 200) | none |
| 3 | https://agentskills.io/skill-creation/evaluating-skills | Eval methodology: evals/evals.json shape (id, prompt, expected_output, files), running each case with_skill and without_skill for a baseline, workspace layout iteration-N/<eval>/with_skill|without_skill, timing.json, grading.json, benchmark.json, grading principles, human review loop | fetched 2026-10-12 (HTTP 200) | none |
| 4 | https://agentskills.io/skill-creation/best-practices | Well-scoped, calibrated skills: progressive disclosure (name+description at startup, body on activation, referenced files on demand), scripts that are deterministic and offline, keeping SKILL.md under ~5,000 tokens | fetched 2026-10-12 (HTTP 200) | none |
| 5 | https://agentskills.io/skill-creation/using-scripts | Bundling executable scripts in skills: paths relative to the skill root, shebang + executable bit, deterministic output, machine-readable to stdout / human detail to stderr, no network at validation time | fetched 2026-10-12 (HTTP 200) | none |
| 6 | https://agentskills.io/clients.md | Client implementations that support the standard: confirms the field set is portable across Claude Code, Codex, Cursor, Gemini CLI, VS Code/Copilot | fetched 2026-10-12 (HTTP 200) | none |
| 7 | https://github.com/anthropics/skills | Anthropic's reference skills repo: folder+SKILL.md layout, template-skill, document/pptx/xlsx skills as complex examples, Apache-2.0 licensing convention | fetched 2026-10-12 (HTTP 200) | none |
| 8 | https://github.com/openai/skills | OpenAI's Codex skills repo (now deprecated, redirects to openai/plugins): confirms .system/.curated/.experimental tiers and the $skill-installer flow | fetched 2026-10-12 (HTTP 200) | the repo is deprecated; use openai/plugins for new work |
| 9 | https://fast.io/resources/awesome-claude-skills-directory-2026/ | Ecosystem size: ~24,400 repos with skill definitions (June 2026) — the reason generic skills are everywhere and Ottili skills must be specific and evidence-based | fetched 2026-10-12 (HTTP 200) | none |
| 10 | https://agentskills.io/llms.txt | Documentation index used to discover the pages above; confirms the canonical URL layout (skill-creation/*.md, clients.md, specification.md) | fetched 2026-10-12 (HTTP 200) | none |

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
