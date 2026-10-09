# SOURCES.md — skill-authoring-evals

All URLs retrieved 2026-10-07 unless marked otherwise. Primary sources first.

## 1. Agent Skills open standard — specification
- URL: https://agentskills.io/specification
- Retrieved: 2026-10-07
- Used: authoritative definition of the skill format (SKILL.md + YAML front matter + optional scripts/, references/, assets/), progressive-disclosure rules, the 1024-character description cap, and the recommended body budget (<5,000 tokens, <500 lines). Single source of truth for what a valid skill looks like.
- Version note: applies to the standard as published; re-check at each spec update.

## 2. Agent Skills standard — markdown skill definition (mdskills.ai)
- URL: https://www.mdskills.ai/specs/skill-md
- Retrieved: 2026-10-07
- Used: field-by-field rules for the front matter (name, description, license, compatibility, metadata, allowed-tools), the trigger/when-to-use semantics of the description, and the progressive-disclosure hierarchy (startup -> activation -> on-demand). Confirms the 1024-char description limit.

## 3. skills-ref — reference validator for Agent Skills
- URL: https://github.com/anthropics/skills (skills-ref tooling referenced in the ecosystem)
- Retrieved: 2026-10-07
- Used: the rule set that `skills-ref validate` applies: front-matter presence, name/folder match, description length, SKILL.md line limit, reference-link well-formedness, script determinism. Used as the pass/fail checklist for our own validation script. Note: this is a reference implementation; our `scripts/validate_skill.py` mirrors its checks so the skill is usable even when skills-ref is absent.

## 4. Anthropic Skills documentation — "Build custom skills"
- URL: https://docs.anthropic.com/en/docs/agents-and-tooling/agent-skills/overview
- Retrieved: 2026-10-07
- Used: guidance on description design (the description IS the trigger -- it must state what the skill does AND when to load it), progressive-disclosure patterns, and the common failure of "vague descriptions that never fire". Provides worked examples of good vs bad descriptions that this skill adapts.

## 5. OpenAI Skills documentation — skill format and evaluation
- URL: https://github.com/openai/skills (README + evaluation notes)
- Retrieved: 2026-10-07
- Used: the evaluation angle -- how skills are tested for trigger accuracy, description quality, and body usefulness. Confirms cross-platform portability (Codex, Claude Code, Cursor, Gemini CLI all read the same folder).

## 6. Awesome Claude Skills directory — ecosystem size and quality bar
- URL: https://fast.io/resources/awesome-claude-skills-directory-2026/
- Retrieved: 2026-10-07
- Used: ecosystem survey (~24,400 skill repos in June 2026). Establishes why generic skills are ubiquitous and why Ottili skills must be evidence-based, decision-procedure-driven, and better than the generic baseline. Justifies the "no filler, no generic advice" quality bar in DESIGN.md.

## 7. R3_VERIFIED_FACTS.md — section 8 (Agent Skills open standard)
- URL: /srv/ottili/repo/ottili-planning/inputs/R3_VERIFIED_FACTS.md
- Retrieved: 2026-10-07 (re-read)
- Used: starting point only; every fact above was re-verified against the primary spec sources on 2026-10-07. Confirms the 1024-char description cap, the <5,000-token / <500-line body budget, and the `skills-ref validate` tool.

## Conflicts between sources

- mdskills.ai lists `allowed-tools` as a standard field; the agentskills.io spec shows it as optional/metadata. Treat it as optional: include it only when the skill genuinely restricts tool use, and never as a hard validation failure if absent.
- Anthropic docs show a `.claude/skills/` path convention while OpenAI uses `.agents/skills/`; the standard itself is path-agnostic -- SKILL.md content is what matters. We pin the path in configuration, not in logic.

## Version-sensitive facts and re-verification

| Fact | Verified for | Re-verify |
|------|-------------|-----------|
| Description character cap | 1024 | at each spec update |
| Body token budget | 5,000 | at each spec update |
| SKILL.md line budget | 500 | at each spec update |
| skills-ref validate rule set | current | when skills-ref releases |
| Front matter fields | name, description, license, compatibility, metadata, allowed-tools | at each spec update |
