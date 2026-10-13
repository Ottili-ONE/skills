# Playwright A11y E2E — Full Procedure
Retrieval date: 2026-10-13. Host: Biest. SEARCH_ENDPOINT: none.

## Verified versions
| Artifact | Version | Verified |
|----------|---------|----------|
| @playwright/test | 1.54+ (current channel) | 2026-10-13 |
| @axe-core/playwright | 4.13.0 | 2026-10-13 |
| axe-core | 4.14.0 | 2026-10-13 |
| WCAG 2.2 | A/AA | 2026-10-13 |

## 1. Setup (do this first — ordering matters)
```bash
npm init -y
npm i -D @playwright/test @axe-core/playwright
npx playwright install chromium firefox webkit --with-deps
```
- Viewport loop: `[320, 768, 1024, 1440]`.
- Disable animations in `beforeEach`:
  `page.addStyleTag({content: '* { transition: none !important; animation: none !important; }'})`
  — flaky axe timing is the #1 false-positive source.
- Set `baseURL` via `PLAYwright_BASE_URL` or `config.webServer`. Always run
  `--headed=false` in CI and `--headed=true` locally for debug.
- Timeout default 30 s; raise to 60 s for slow pages via `config.use.actionTimeout`.
- **Common trap:** forgetting `webServer.start` causes a race on the first route. Always
  start the server before the browser context via `config.webServer.command` +
  `reuseExistingServer: true`.

## 2. Thresholds
| Check | Threshold | Fail signal |
|-------|-----------|-------------|
| axe A/AA violations | **0** across all routes and viewports | any violation |
| axe AAA | warn only (AAA is often infeasible per W3C guidance; do not silently downgrade) | — |
| Keyboard | every interactive element reachable via Tab within **≤5 Tab presses** per viewport | unreachable control |
| Responsive | no horizontal overflow beyond viewport width at any breakpoint | `scrollWidth - innerWidth > 0px` |
| Selector stability | flag any `nth-child` or CSS-class-attribute selector; require role/text alternative in the same PR | unstable selector |

## 3. Verification order (never reorder)
`setup -> axe -> keyboard -> responsive -> selector audit -> evidence commit`
- axe requires a stable DOM, which responsive layout may shift.
- selector audit requires final layout, which keyboard path may trigger focus changes for.
- Running selector audit before responsive misses layout-shifted selectors.
- Running keyboard check before axe misses `aria-hidden` content that blocks tab order.

## 4. Exact commands
```bash
npx playwright test --grep @a11y --reporter=json --output=tests/e2e/report.json
python3 scripts/check_audit_selectors.py tests/e2e/report.json
python3 scripts/check_keyboard.py tests/e2e/report.json
python3 scripts/check_workaround_markers.py src/
python3 scripts/check_axe_evidence.py tests/e2e/evidence/
```
All four must return exit code 0; otherwise the build is red with a summary printed to stdout
listing failing routes first, then failing viewports, then failing selectors, then missing
evidence files.

## 5. Evidence rule
Commit axe JSON under `tests/e2e/evidence/<route>.json` and screenshots under
`tests/e2e/screenshots/<route>-<viewport>.png` per route+viewport pair. Never delete evidence
after a failure without filing an issue referencing the failure ID.

## 6. Workaround marker convention
When a component cannot be made accessible immediately, mark it with
`<!-- a11y-wip reason="..." owner="..." date="YYYY-MM-DD" -->` inside the markup **and** file a
tracking issue before merge. Never ship an unmarked workaround as "done". The reason must be
≤80 chars; `reason="TBD"` without an owner blocks forever. The audit script fails the build if
any marker exists without a linked issue number matching `ISSUE-<digits>`.

## 7. Fault injection (optional but recommended)
Inject a focus trap into a modal component and assert the keyboard path still reaches the
close button via `Shift+Tab` reverse traversal (caught by `check_keyboard.py` reverse mode).

## 8. False-done detection heuristics
| Build state | Suspect |
|-------------|---------|
| green, no new evidence files committed | skipped routes |
| green, evidence JSON has zero routes tested | empty test suite |
| green, workaround markers present | hidden failures |

## 9. Handoff notes
When handing off to another lane, include: route list, viewport list, browser list, evidence
dir path, known workaround markers list, and the last failing route name — so the next agent
resumes from the failure point, not from the start. Resuming from the last failure saves ~70%
runtime on large suites.

## 10. Resuming after a failure
Delete evidence only for routes that will be re-run:
`rm -f tests/e2e/evidence/<route>.json` before re-running that route. Never `rm -rf` the
entire evidence dir unless a full re-run is intended — it destroys other lanes' committed
evidence on the shared tree. If multiple lanes write the same evidence dir concurrently, use
lane-specific subdirs `tests/e2e/evidence/<lane>/<route>.json` (configured via `EVIDENCE_LANE`,
defaulting to `git config user.name` sanitized, fallback `unknown`).
