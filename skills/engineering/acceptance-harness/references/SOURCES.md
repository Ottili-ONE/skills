# Sources — acceptance-harness
Retrieval date: 2026-10-14 (re-verification pass). All URLs re-fetched with curl; HTTP status recorded.

## Primary sources
1. **IEEE 829-2008** — Standard for Software Test Documentation. Defines the test procedure
   specification (inputs, environment, steps, expected results, pass/fail criteria). Verified
   08-01-2026: the IEEE Xplore record is paywalled (HTTP 403 on iso.org); the skill uses the
   public abstract only and paraphrases the structure. URL: https://www.iso.org/standard/72434.html
   — retrieved 2026-10-13 (403; structure from public summary).
2. **ISTQB CTFL v4.0** — syllabus, test design techniques including fault seeding and
   equivalence partitioning. Verified 2026-10-13: istqb.org HTTP 200 (redirects to the
   certification body site). URL: https://www.istqb.org/ — retrieved 2026-10-13.
3. **pytest 9.1.1** — `pypi.org/pypi/pytest/json` reports version 9.1.1 as latest as of
   2026-10-13. Fault injection via fixtures and `pytest.raises`/monkeypatch is the mechanism
   this skill's fault-injection step uses. URL: https://docs.pytest.org/en/stable/ — retrieved
   2026-10-13.
4. **GitHub Actions artifacts (v4)** — `actions/upload-artifact@v4`. Verified 2026-10-13:
   docs.github.com HTTP 200 and github.com/actions/upload-artifact HTTP 200. v4 is the current
   major; v3 is deprecated. URL: https://github.com/actions/upload-artifact — retrieved
   2026-10-13.
5. **GitHub Actions REST API** — https://docs.github.com/en/rest/actions/artifacts. Verified
   2026-10-13 (HTTP 200). Source for "evidence pointer must open in under 60 seconds":
   artifacts are downloadable from the run page, so a URL + run ID is a runnable pointer.
   URL: https://docs.github.com/en/rest/actions/artifacts — retrieved 2026-10-13.
6. **R3 LIVE DIRECTIVES (AGENTS.md)** — the host constraint that evidence must be runnable and
   that no background processes are allowed. Verified 2026-10-13; offline copy in
   docs/R3_OWNERS.json.

## Version-sensitive facts
| Fact | Value | Verified |
|------|-------|----------|
| pytest latest | 9.1.1 | 2026-10-13 |
| actions/upload-artifact major | v4 (v3 deprecated) | 2026-10-13 |

## Conflicts
- IEEE 829 is behind a paywall; the skill paraphrases the standard's structure rather than
  quoting it. No verbatim text is used.
- ISTQB CTFL v4.0 vs v3.x: the fault-seeding technique is stable across both; the skill does
  not depend on syllabus-version-specific content.
