# SOURCES.md — browser-agent-playwright

All URLs retrieved 2026-10-08 unless marked otherwise.

## 1. Playwright API reference — Page
- URL: https://playwright.dev/docs/api/class-page
- Retrieved: 2026-10-08
- Used: locator methods, evaluate/evaluateHandle, goto, frames, downloads.
- Version note: verified against Playwright docs as rendered 2026-10-08; API stable
  1.49–1.55. Re-check on each driver release.

## 2. Playwright Locators
- URL: https://playwright.dev/docs/locators
- Retrieved: 2026-10-08
- Used: locator strategy order (role, label, testid, text), `or()`, web-first assertions.

## 3. Playwright Frame API
- URL: https://playwright.dev/docs/api/class-frame
- Retrieved: 2026-10-08
- Used: frame.locator, mainFrame, frameLocator.

## 4. Playwright BrowserContext
- URL: https://playwright.dev/docs/api/class-browsercontext
- Retrieved: 2026-10-08
- Used: newContext isolation, javaScriptEnabled, downloads path.

## 5. OWASP LLM Prompt Injection Prevention Cheat Sheet
- URL: https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.md
- Retrieved: 2026-10-08
- Used: attack taxonomy (direct/remote/encoding/typoglycemia/BoN/multimodal/RAG/
  agent-specific), detection patterns, output validation, HITL, least privilege.

## 6. OWASP LLM Risk Top 10 (2025) — LLM01 Prompt Injection
- URL: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- Retrieved: 2026-10-08
- Used: confirms LLM01 as the top risk; mitigation guidance.

## 7. OWASP Top Ten 2025 (web app context)
- URL: https://owasp.org/www-project-top-ten/
- Retrieved: 2026-10-08
- Used: general injection context (A03:2025 Injection) as background.

## Conflicts between sources
- None material. The OWASP cheat sheet is the authoritative taxonomy for LLM
  injection; Playwright docs are authoritative for browser API.

## Version-sensitive facts and re-verification
| Fact | Verified for | Re-verify |
|------|-------------|-----------|
| Playwright locator API | 1.55 docs, 2026-10-08 | each driver release |
| `page.evaluate` discouraged for extraction | 1.55 docs | each driver release |
| OWASP LLM Top 10 | 2025 v1.0 | next revision |
| Prompt injection cheat sheet | master branch 2026-10-08 | when updated |
