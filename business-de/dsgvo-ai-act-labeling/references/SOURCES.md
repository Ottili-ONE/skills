# SOURCES — dsgvo-ai-act-labeling

Retrieval date: **2026-10-13** (this pass). Every URL below was probed on that
date; the HTTP status is recorded per row. Version-sensitive facts are pinned in
`config/versions.json`; re-verify before relying on a fact.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| S1 | EU AI Act — Article 50 (official text) | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689 | 2026-10-13 | **202 OK** (re-probed; content served) | Primary. Art. 50(1)-(4) transparency duties for AI systems, including labelling of deepfakes and AI-generated content published to inform the public. |
| S2 | FGS — AI Act applicability from 2026-08-02 | https://www.fgs.de/news-and-insights/blog/detail/eu-ai-act-was-ab-dem-2-august-2026-gilt-und-was-verschoben-wurde | 2026-10-13 | **200 OK** | Confirms Art. 50 applied 2026-08-02; the Digital Omnibus (Regulation (EU) 2026/1744) postponed high-risk obligations but left Art. 50 unchanged; Art. 50(2) machine-readable marking duty for systems placed on the market before 2026-08-02 applies from 2026-12-02. |
| S3 | DQS — KI-Kennzeichnungspflicht | https://www.dqsglobal.com/de/entdecken/blog/ki-kennzeichnungspflicht-eu-ai-act | 2026-10-13 | **200 OK** | Practical reading of Art. 50(4): disclosure required unless the text underwent **human review or editorial control** AND a natural or legal person holds editorial responsibility. |
| S4 | IHK München — AI Act | https://www.ihk-muenchen.de/aiact/ | 2026-10-13 | **200 OK** | Chamber guidance corroborating the Art. 50(4) human-review exception and the deepfake labelling duty. |
| S5 | EU AI Act — Digital Omnibus | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32026R1744 | 2026-10-13 | **200 OK** | Regulation (EU) 2026/1744 postponing Annex III high-risk dates; confirms Art. 50 was **not** amended. |
| S6 | GDPR — official text | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679 | 2026-10-13 | **200 OK** | GDPR core: Art. 5 principles, Art. 6 lawfulness, Art. 12-14 transparency, Art. 30 processing register, Art. 25 data protection by design, Art. 35 DPIA. |
| S7 | European Data Protection Board — Guidelines | https://edpb.europa.eu/ | 2026-10-13 | **200 OK** | EDPB home; Guidelines 05/2025 on DPIA and the Art. 9 guidance are linked from here. |
| S8 | R3_VERIFIED_FACTS.md | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | — | starting point; re-verified 2026-10-13 for the Art. 50 applicability dates. |

## Conflicts / version-sensitive notes

- **Art. 50 effective date (2026-10-13):** all three 200-OK sources (S1, S2, S4) agree Art. 50 applies **since 2026-08-02**. No conflict.
- **Art. 50(2) marking duty:** S2 says the machine-readable marking duty for systems placed on the market before 2026-08-02 applies from **2026-12-02**. This is a secondary-source date; re-verify against the Omnibus recital before relying on it.
- **Human-review exception wording:** S3 and S4 phrase the exception slightly differently (S3: "human review or editorial control"; S4: "qualified human review"). The operative test is the conjunction in Art. 50(4): human review **and** named editorial responsibility. Have a lawyer confirm before a publication decision rests on this exception.
- **GDPR processing register:** no conflict; Art. 30 is unconditional for the controller. The retention-class defaults are taken from the gobd-archive skill (AO §147) and are re-verified there.

**Re-verification note:** re-fetch the Omnibus recitals before 2026-12-02; the Art. 50(2) marking date is the most date-sensitive fact in this skill.

## Re-verification 2026-10-13

All primary URLs re-probed with curl on 2026-10-13. Statuses recorded per row above. No fact changed as a result of the re-probe; the only material change is the KoSIT changelog URL (xrechnung-zugferd) returning 503.

