# Ottili Platform & Architecture — Master Blueprint v2

| Field | Value |
|---|---|
| **Document ID** | `OTTILI_PLATFORM_ARCHITECTURE_BLUEPRINT_V2` |
| **Version** | 2.0.0-draft.1 |
| **Date** | 2026-10-19 |
| **Status** | 📝 Draft for review by Willi. Not approved. Contains decided items (✅), proposals (🟠) and open items (🔴). |
| **Author** | Claude, for Willi (founder, Ottili) |
| **Type** | Normative target architecture for Ottili Platform and the architecture rules every Ottili product obeys |
| **Language** | English (technical document). Decision and strategy documents for Willi are German. |
| **Replaces** | `OTTILI_VNEXT_FOUNDATION_V2_MASTER_BLUEPRINT.md` and `OTTILI_PLATFORM_INFRASTRUCTURE_MASTER_BLUEPRINT.md` (both archived unchanged first; see Appendix G for the section-by-section target map) |
| **Built from** | `OTTILI_KONSOLIDIERTE_GRUNDLAGE_2026-10-18` (Doc 1), `OTTILI_ANALYSE_GAPS_BEWERTUNGEN_2026-10-18` (Doc 2), `OTTILI_GERMO_PACK_URTEIL_2026-10-18` (Doc 3), the founder's voice dump of 2026-10-17, the two replaced blueprints, the repo report R14 (2026-10-14) |
| **Companion blueprints** | HQ v2, LD3 v2, alran v2, Research Labs v2 (this document is the architecture authority they all consume) |

> **One-sentence thesis.** *Ottili adapts to the company, not the other way round:* one platform on which a company does almost everything (HQ), that either plugs into the stack the company already has (integrations, provider binding) or replaces it step by step (apps + import), and over which an agent (alran) co-operates the company **inside limits the company sets** — every action typed, authorised, budgeted, verified and receipted.

### Contents

| Part | Chapters |
|---|---|
| **A · Frame** | 0 Document control · 1 Purpose and scope · 2 Landscape and ownership · 3 Principles and architecture rules · 4 System context, layers, zones |
| **B · Identity and structure** | 5 Identity and auth · 6 Companies, tenancy, policy · 7 Registry, apps, extensions, skills |
| **C · Acting** | 8 Actions · 9 Autonomy T0–T5 · 10 Approvals and Channel Port · 11 Operations · 12 Flows · 13 Integrations and provider binding · 14 Ottili MCP |
| **D · AI** | 15 AI Gateway · 16 Agent governance · 17 Browser and CAPTCHA |
| **E · Platform services** | 18 Events and jobs · 19 Data, files, search, lifecycle · 20 Credits and billing · 21 Notifications and settings · 22 Audit |
| **F · Trust** | 23 Legal and privacy · 24 Security |
| **G · Surfaces and contracts** | 25 Experience foundation (incl. Ottili Console) · 26 API conventions |
| **H · Running it** | 27 Infrastructure and delivery · 28 Reliability and recovery |
| **I · Getting there** | 29 Beta profile (M1–M6, BP-0…BP-6, G1–G8) · 30 Migration · 31 Acceptance catalogue · 32 Risks, decisions, ADRs |
| **Appendices** | A Glossary · B Events · C Seed actions · D Error codes · E Decision traceability · F Source register · G Map of the replaced blueprints |

---

## 0. Document control

### 0.1 Authority and precedence

1. If this document and Doc 1 (`KONSOLIDIERTE_GRUNDLAGE`) disagree, **Doc 1 §5 (decision register) wins** until this document is corrected.
2. This document wins over the two replaced blueprints, over the HQ/LD3/alran blueprints of the previous generation, and over any GERMO plan that contradicts it. A GERMO plan that contradicts this document is a defect of the plan (see Doc 3), not of this document.
3. Product blueprints (HQ, LD3, alran, Research Labs) define **domain** behaviour. This blueprint defines the **shared runtime guarantees and mechanisms** those products consume (principle P6). A product blueprint MUST NOT redefine a Platform mechanism; it MAY add domain semantics on top.
4. Market and competitor statements in this document are **hypotheses** until verified by REA/clean-room analysis (Doc 1 §0). Legal, tax and license points are **hints, not advice** (Doc 1 §0).

### 0.2 Normative language

**MUST / MUST NOT / SHOULD / SHOULD NOT / MAY** have RFC 2119 force. A statement without such a word is descriptive.

### 0.3 Status and evidence tags

| Tag | Meaning |
|---|---|
| ✅ | **Decided** by Willi (decision ID `D-xx` from Doc 1 §5.1) |
| 🟢 | **Evidence** — stated in a named source (blueprint, plan job, repo report, external source) |
| 🟡 | **Derived** — follows from evidence; it is my conclusion |
| 🟠 | **Proposal / hypothesis** — binding only after Willi's decision |
| 🔴 | **Open** — needs a decision or a check; listed in §32 |

### 0.4 Identifier conventions

| Prefix | Meaning | Defined in |
|---|---|---|
| `P1`…`P12` | Guiding principles | §3.1 (Doc 1 §1.3) |
| `AR-nn` | Architecture rule (testable) | §3.2 |
| `D-nn` | Founder decision | Doc 1 §5 |
| `R-nn`, `W-nn`, `Q-nn` | Gap, contradiction, report deviation | Doc 2 §5, §6 |
| `PAT-<area>-nn` | Platform acceptance test | end of each chapter, index in §31 |
| `ADR-P-nn` | Open architecture decision needing evidence | §32.3 |
| `BP-0`…`BP-6` | **Build stage** (a block of related work with its own acceptance; not a choice between paths) | §29 |
| `G1`…`G8` | Beta gates | §29 |
| `M1`…`M6` | Beta reference missions | §29 |
| `T0`…`T5` | Autonomy levels | §9 |
| `PLT-W1-nn` etc. | GERMO plan job IDs (traceability only) | Doc 3 |

### 0.5 Writing rules for implementers

- Code, identifiers, API paths, event names, error codes and GERMO plans/prompts are **English**. Every user-visible string goes through i18n message catalogs (`de`, `en` are release-gated, §25.9).
- Every shipped capability is complete in the sense of P8: contract, authorization, empty/error/degraded states, audit, journey test. No half features.
- Where a number or fact comes from an external source it carries its source in Appendix F (source register); a number without a source is a target to be measured, never a claim.

---

## 1. Purpose, scope and non-goals

### 1.1 Purpose

Ottili Platform is the **control plane** under every Ottili product. It exists so that

1. a company can run **almost everything in one place** (HQ, LD3, apps) with one navigation, one permission model and one set of links between records (promise 1);
2. a company **keeps its stack if it wants to** — every business capability is either *native* (Ottili is the system of record) or *bound* (the customer's system is) — and can **migrate step by step** (promise 2);
3. an **agent operates the company** — alran, an external MCP client, a Flow or a human use the **same typed actions** with the same validation, rights, approvals and audit (promise 3).

### 1.2 What this blueprint governs

| In scope | Where |
|---|---|
| Identity, sessions, machine identity, API keys | §5 |
| Company, tenancy, roles, policy, entitlements | §6 |
| Registry, manifests, apps, extension runtime, skills | §7 |
| Action architecture, autonomy T0–T5, approvals, Channel Port | §8–§10 |
| Operations (business case + inbox), Flows | §11–§12 |
| Integrations and provider binding, Ottili MCP | §13–§14 |
| AI Gateway, model policy, credits and metering | §15, §20 |
| Agent governance contracts (agent principal, missions, context service, watcher), browser/CAPTCHA policy | §16–§17 |
| Events, jobs, data, files, search, lifecycle, privacy | §18–§19, §21 |
| Audit, observability, legal/compliance architecture, security | §22–§24 |
| Experience foundation (tokens, components, bootstrap), API conventions | §25–§26 |
| Infrastructure, deployment, reliability, DR | §27–§28 |
| Beta profile, migration, acceptance, risks | §29–§32 |

### 1.3 What it does not govern

- Domain behaviour of HQ, LD3, apps — see the companion blueprints.
- alran's product behaviour and harness adapters — alran v2 blueprint. This document only fixes the **contracts** alran must satisfy (agent principal, missions, MCP, gateway, receipts).
- Ottili Research Labs and model training — Research Labs v2 blueprint. The Platform treats own models as "just another provider" behind the AI Gateway (§15).
- Business plans, pricing numbers and go-to-market. This document defines the **mechanisms** (one plan/price registry, hard credit caps) not the numbers.
- GERMO (the internal build factory). It is described only where it constrains the architecture (branch model §27.8, supply chain §24.7).

### 1.4 Non-goals

The target explicitly does **not** require (carried over from the replaced Infrastructure blueprint, extended):

- an AWS clone, Kubernetes at tiny scale, Kafka without measured event pressure, a service mesh for ordinary HTTP calls;
- databases exposed as APIs, cross-service table sharing, mutable production checkouts as the release mechanism;
- multi-region active-active before single-site recovery is proven;
- one process per conceptual service (logical owners stay explicit; deployables are grouped, §27.3);
- an **own agent core** — mission/run/checkpoint runtimes are replaced by harness adapters (D-05 ✅, §16);
- per-tenant forks of code; tenant-private behaviour is data + extensions (§7);
- self-hosting in 2026 (D-15 🟠) — but no cloud-only assumptions that would make it impossible later;
- desktop and mobile app clients in the beta (D-01 ✅). The **API-first** rule (AR-02) keeps them possible.

### 1.5 Scale and enterprise stance (founder requirement)

Everything is designed **scalable and enterprise-ready from the start**, without building the large topology first:

- **Scalable:** stateless services, explicit partition keys (`company_id`, aggregate id), bounded synchronous work with `202 + job`, idempotency everywhere, pooled DB connections, measured bottlenecks before added technology (§27.9).
- **Enterprise-ready:** OIDC/SAML federation for customer IdPs (via Keycloak identity brokering, §5.4), RBAC + attribute rules, immutable audit with export, data-class and region flags, deletion/export sagas, SLO/error-budget discipline, signed artifacts + SBOM, step-up and four-eyes approvals, kill switch for every autonomous capability.
- **Not yet:** SCIM provisioning, customer-managed keys, multi-region. Each has a contract slot (§5.8, §19.9, §27.10) and a `🟠` post-beta marker.

---

## 2. Product, repository and ownership landscape

### 2.1 Product tree ✅ D-04

```text
OTTILI (umbrella brand)
│
├── Ottili ONE ───────── company software · MAIN FOCUS (VD: "global software for a whole company")
│     ├── HQ    core (CRM + ERP basis) + bundled (finance, DATEV) + apps + integrations + flows + alran
│     └── LD3   content: discover → verify → create → review → publish → keep current
│
├── alran ────────────── AI product family · complement AND standalone product
│     ├── alran AI            chat + work in one product (harness: bytedance/deer-flow, MIT)
│     ├── alran Code          harness: openai/codex (Apache-2.0), own parallel track
│     ├── alran API & Console model access with its own console (face of the AI Gateway)
│     └── alran in HQ/LD3     native panel; no hard dependency on alran.ai
│
├── Ottili Platform ──── control plane under everything (this document)
│     └── Ottili Console    admin UI of the Platform
│
├── Ottili Research Labs  one research line (ORL+BRL+RRL); models Pico/Vale/Cairn/Spire; not part of the beta
└── GERMO                 internal build factory; not a customer product
```

`Ottili Console` (platform administration) and `alran Console` (part of alran API & Console, model access) are different products and MUST NOT share a name in UI, docs or code.

### 2.2 Product and module identifiers 🟠 (D-04 ✅ names; identifier spelling 🟠)

| Level | Identifier | Notes |
|---|---|---|
| Product family | `ottili` | brand |
| Product | `platform` · `one` · `alran` | |
| Module | `one.hq` · `one.ld3` · `alran.ai` · `alran.code` · `alran.api` | module IDs are the stable vocabulary for entitlements, routes, events, MCP namespaces |
| Platform surface (not installable, not a tenant App) | `platform.console` · `platform.auth` · `platform.developer` · `platform.status` · `platform.lab` | declared through `PlatformSurfaceManifest` (§7.3) |
| App (installable per company) | `app.<name>` (first-party) · `<publisher>.<name>` (third-party/private) | |

Legacy identifiers `platform.ld3`, `rooke.*`, `login.ottili.one` are **dead names** and MUST NOT appear in new code (R-53, W-13 resolved).

### 2.3 Repository map 🟢 (state of 2026-10-18) / 🟠 (target roles)

Eight repositories exist today (Doc 3 §3 / task 1 repo check pending). Their architectural role:

| Repository | Role | Owns | Consumes | In beta |
|---|---|---|---|---|
| `ottili-platform` | Platform services, gateway, Auth integration, Foundation package family (`foundation-*`), SDKs, generated contracts, Flows, Actions, Approvals, Operations, Integrations engine, AI Gateway, Ottili MCP, Credits/Billing, Events/Jobs, Files, Search, Registry, Legal, Observability contracts | all Platform capabilities (§2.4) | nothing from products except through contracts | ✅ |
| `console-v2` | **Ottili Console** (admin UI of the Platform) | admin surfaces only; no business logic | Platform APIs/SDK, Foundation UI | ✅ (after shrink, `CON-W0-04`) |
| `hq-v2` | **Ottili HQ** domain services + UI | HQ business entities and domain actions | Platform contracts | ✅ |
| `ld3-v2` | **Ottili LD3** domain services + UI | LD3 content entities and domain actions | Platform contracts | ✅ |
| `ottili-apps` | First-party apps and connectors (Shopify, Stripe, DATEV, mail/calendar, WordPress, newsletter, Meta, GitHub, dropshipping …) | per-app domain mapping only | Platform Integrations engine, Actions, Flows | ✅ |
| `alranbot`, `synth` | Research/data line (datasets, synthetic data, training pipelines) | data products | AI Gateway as a provider consumer | ✖ not beta (Research Labs) |
| `skills` | GERMO build-factory skills (developer skills, **not** operational skills) | GERMO tooling | – | tool only |
| *(new)* `alran` 🟠 | alran AI/Code adapters, alran API & Console UI, alran-specific UI semantics | harness adapters, alran runtime wiring | Platform contracts, Ottili MCP | ✅ (BP-5) — name/repo split is decided in the alran blueprint |

Rules: a repository MUST NOT import another repository's private source, migrations, models, Redis keys or DB tables. Sharing happens through **versioned packages** (`@ottili/*` on the private registry), **generated SDKs**, **schemas** and **events** (AR-01, §2.5).

### 2.4 Capability ownership matrix (principle P6) 🟢

Cross-cutting capabilities belong to the Platform. Products **register with** and **consume** them. A cross-cutting re-implementation inside HQ/LD3/apps is a defect, not a feature (R-19, R-51).

| Capability | Owner | Consumers | Section |
|---|---|---|---|
| Login, sessions, SSO, step-up | Platform **Auth** (engine: Keycloak behind `auth.ottili.one`, D-12 ✅) | all | §5 |
| Company, membership, roles, policy, entitlements | Platform **Company/Policy** | all | §6 |
| Product/app registry, manifests, extension host, marketplace, skills catalog | Platform **Registry** | products, apps | §7 |
| Actions (registry + pipeline), grants, receipts, tool export | Platform **Actions** | products *register*; UI, Flows, alran, MCP *invoke* | §8 |
| Autonomy ceiling, regulator, kill switch | Platform **Policy** (+ UI in Ottili Console) | all | §9 |
| Approvals | Platform **Approvals** | HQ, LD3, alran, Flows | §10 |
| Channel Port (web inbox mandatory; Slack, Discord, Telegram adapters) | Platform **Notifications/Approvals** | all | §10.3 |
| Operations (business case + inbox) | Platform **Operations** (D-30 ✅) | HQ, LD3, alran, Flows | §11 |
| Flows (automation engine) | Platform **Flows** | HQ/LD3/apps contribute triggers, nodes, templates | §12 |
| Integrations mechanics, provider binding, business-graph views | Platform **Integrations** | apps, connectors, HQ | §13 |
| Domain mapping of an external system | the app/connector or HQ domain | – | §13 |
| Ottili MCP (one per company) | Platform **Actions/Gateway** (D-29 ✅) | external clients, alran | §14 |
| AI Gateway: model access, routing, budgets, data classes, MCP registry | Platform **AI Gateway** | alran, HQ, LD3, apps | §15 |
| Missions, agent principals, context service, watcher | Platform **Agent Governance** | alran runtime | §16 |
| Credits, billing, usage, plan/price registry | Platform **Commerce control** | all | §20 |
| Events, jobs, schedules, outbox, event catalog | Platform **Events/Jobs** | all | §18 |
| Files, search, notifications, settings | Platform | all | §19, §21 |
| Audit, receipts, security events | Platform **Audit** | all | §22 |
| Signals/anomalies (OOIE) | Platform (consumer of the event layer) | HQ, alran (perception), inbox | §18.7 |
| Legal documents, acceptance, subprocessors, privacy requests, AI inventory | Platform **Legal/Privacy** | all | §23 |
| Business entities (organization, product, stock, order, invoice …) | **HQ** or the bound system | LD3 (read), apps, alran | HQ blueprint |
| Content entities (source, topic, claim, evidence, version, publication) | **LD3** | HQ (read), alran | LD3 blueprint |
| Agent runtime, sandboxes, harness | **alran runtime** (adapters over DeerFlow/Codex) | alran AI, panels | alran blueprint |
| Admin UI (members, companies, rights, billing, apps, developer, privacy, autonomy ceiling) | **Ottili Console** | admins | §25.10 |
| Model access console (keys, usage, budgets, routing, billing for model customers) | **alran API & Console** on the AI Gateway | developers, companies | alran blueprint |
| Deployment/runtime control (builds, artifacts, releases, nodes) | Platform **Cloud/Deploy control** | Platform itself, later customers | §27 |

### 2.5 Dependency rules

1. **Backend sharing** = APIs, generated SDKs, schemas, events. **Frontend sharing** = versioned `foundation-*` packages installed from packed artifacts.
2. Direct imports across repositories, shared tables, implicit Valkey key contracts, filesystem handoffs, subprocess coupling and SSH-based service calls are **forbidden** (migration-only anti-patterns, each with a telemetry hook and a removal gate).
3. A package moves into Foundation only if **at least two products** use the same *semantics* (not merely similar pixels) and a dependency-boundary review passes.
4. Dependency direction: `Experience → Agent → Control plane → Domain → Data → Infra`; a layer calls only the layer directly beneath it and never bypasses Gateway/Policy (§4.2).
5. The dependency registry (machine-readable) lists every producer → consumer edge; CI computes affected consumers for every contract change and tests at least the latest supported and the next candidate version (consumer conformance, §26.6).

### 2.6 Naming map (old → valid) 🟢 Doc 1 Anhang A

| Old | Valid | Note |
|---|---|---|
| Rooke, Alrun, Allran | **alran** | final; history Rooke → Alrun → alran |
| Rooke AI, Rooke Work, alran Chat, alran Work | **alran AI** | one product, all agent functions |
| Rooke Code | **alran Code** | |
| "Platform" on the alran side | **alran API & Console** | |
| "Console" | **Ottili Console** (platform admin) · **alran Console** (model access) | never confuse |
| Otily | Ottili | voice-recognition artifact |
| "Bimbo(s)" | **agent(s)** | old word for "agent"; replacement artifact in old documents |
| "beta paths" BP-0…BP-6 | **build stages** | all inside the beta |

### 2.7 Acceptance tests — landscape

| ID | Test | Evidence |
|---|---|---|
| PAT-ARC-01 | A repository-boundary linter fails CI when any repo imports another repo's private path, migration or table name | lint report bound to commit |
| PAT-ARC-02 | Every producer→consumer edge appears in the dependency registry; an unregistered edge fails CI | registry diff |
| PAT-ARC-03 | Fresh-consumer test: each `foundation-*` package installs from a packed artifact in an empty consumer for Next.js web, Node service and TUI; workspace links do not count | pack + install log |
| PAT-ARC-04 | Grep gate: no occurrence of dead names (`platform.ld3`, `rooke.`, `login.ottili.one`) in code, manifests, routes, docs of any repo | CI scan |
| PAT-ARC-05 | UI string audit: "Ottili Console" and "alran Console" never appear for the same surface | i18n catalog check |

---

## 3. Principles and architecture rules

### 3.1 The twelve guiding principles (Doc 1 §1.3) and what enforces them

| # | Principle | Architectural consequence | Enforced by |
|---|---|---|---|
| **P1** | **Ottili adapts to the company** | Every capability runs *native* or *bound*; import/export from day one | provider binding §13, import/export §13.9 |
| **P2** | **One action architecture, many clients** | UI, API, Flows, alran, external MCP clients call the same actions; no special path "for the AI" | §8, parity tests PAT-ACT-* |
| **P3** | **Autonomy is a regulator** | T0–T5, default T3, company ceiling, enforced outside the model | §9 |
| **P4** | **Build what makes Ottili Ottili — use what exists** | harnesses, OSS apps, existing connectors; own build for tenancy, governance, business graph, integration layer, UX | D-31 check (AR-28) |
| **P5** | **Connection ladder** | native → official API → external MCP → Ottili adapter MCP → skill → browser/CUA (last resort, policy-gated) | §13.7 |
| **P6** | **One owner per capability and per entity** | ownership matrix §2.4; system of record per entity and field group | §2.4, §13.2 |
| **P7** | **Evidence instead of assertion** | receipts, verification, tests against real DB and real UI; measurements and conclusions separated | §8.4, §22 |
| **P8** | **Complete, not stripped** | no half features, no half product; one pipeline is not a product | §29 |
| **P9** | **Fail closed; tenants separated** | missing right/budget/evidence ⇒ the action stops; no cross-tenant access, not even through the AI | §6, §24 |
| **P10** | **Simple despite breadth** | usable default view without configuration, explained numbers, exceptions inbox instead of widget wasteland (lesson from SAP) | §11, §25 |
| **P11** | **Honest claims** | only claim what the product can prove; unverified legal/tax points configurable as `UNVERIFIED` | §23 |
| **P12** | **Research separate from product** | Research Labs is its own line, outside the beta | §1.3 |

### 3.2 Architecture rules (testable)

Each rule has an enforcement mechanism; the rule index with test IDs is in §31.2.

| ID | Rule |
|---|---|
| **AR-01** | **One canonical owner per capability and per entity.** There is exactly one system of record (SoR) per entity and field group, recorded in the binding (§13.2). |
| **AR-02** | **All business mutations enter through Actions** — from UI, API, Flows, alran, MCP. No side doors, no direct database writes from another service, no "AI path". |
| **AR-03** | **Authorization is server-side, deny-by-default** and evaluated at preflight **and again at execution time**. UI hiding is never authorization. |
| **AR-04** | **Tenant context is mandatory.** `company_id` is derived from verified context, never from an untrusted body alone; it is carried by every tenant-owned row, cache key, event, job, object key, search document, API key, webhook and usage record. Missing tenant context on a tenant-required operation is an error, not "default company". |
| **AR-05** | **Autonomy is enforced outside the model** (grants, budgets, approvals, sandboxes). A model's output never confers authority. |
| **AR-06** | **External content is data, never instruction** — web pages, mail bodies, product titles, tool outputs, channel messages, app-provided text. |
| **AR-07** | **Events derive from committed truth** via a transactional outbox; consumers are idempotent by event id. |
| **AR-08** | **Long work is a durable job** (lease + fencing). No business-critical state lives in process memory or Valkey. |
| **AR-09** | **Effects are verified.** An operation is reported successful only with verification evidence; ambiguous outcomes become `unknown_external_result` and are reconciled. |
| **AR-10** | **Fail closed** on policy, budget, evidence, manifest/signature verification, tenant context and model eligibility. |
| **AR-11** | **Secrets never appear** in prompts, sandboxes, browser file systems, logs, traces, manifests or flow definitions. Only `SecretRef`s resolved just-in-time by the owner. |
| **AR-12** | **Model access only through the AI Gateway.** No product or app calls a model provider SDK directly. |
| **AR-13** | **A data class travels with every model request**; the gateway filters by model eligibility first and by cost second. |
| **AR-14** | **Canonical actions are independent of the system of record.** The binding router resolves native vs. bound; `external_refs[]` on every record that mirrors an external object. |
| **AR-15** | **Import and export are first-class.** Every company's data is exportable in a machine-readable format through an open API (EU Data Act relevance 🟢 D5). |
| **AR-16** | **Harnesses are adapters:** no fork, pinned versions, thin boundary (tools only through Ottili MCP/Actions; models only through the AI Gateway; missions, receipts, grants in the Platform), exit strategy defined before adoption (D-05 ✅). |
| **AR-17** | **Isolation before density** for agent runtimes: few companies per runtime instance until isolation tests prove pooling safe. |
| **AR-18** | **Artifacts are built once and promoted by digest.** No mutable checkout is a production release mechanism. |
| **AR-19** | **A backup counts only with a restore proof.** A successful backup command is not recovery evidence. |
| **AR-20** | **Observed effects MUST NOT exceed declared effects.** A violation fails closed and opens a security event. |
| **AR-21** | **Parity:** everything a user can do in the UI exists as an action; every action is exportable as a tool definition (OpenAI/Anthropic/MCP). |
| **AR-22** | **One event layer, one event catalog, one product-identifier vocabulary.** |
| **AR-23** | **Facts and conclusions are separated** in all reports and receipts (`observed` / `inferred` / `hypothesis`). |
| **AR-24** | **No visible string outside message catalogs**; code and identifiers are English. |
| **AR-25** | **Scale-ready by construction:** stateless services, partition keys, bounded synchronous work, idempotency, pooled connections. Single-node assumptions are defects even while only one node exists. |
| **AR-26** | **Cost is a first-class constraint.** Every expensive operation preflights a budget reservation; the free beta has hard per-company credit caps (G6). |
| **AR-27** | **Every autonomous capability has an admin kill switch** effective within seconds and audited. |
| **AR-28** | **Build-vs-use check first** (D-31 ✅): the first task of any own-build job is a short review of license, maturity, multi-tenancy and operating cost of existing options. |
| **AR-29** | **No half features:** a capability is "done" only with owner, API/event/job/data contracts, migration, security, observability, backup/restore semantics, deployment manifest, tests and runbook. |
| **AR-30** | **A destructive or irreversible action is never T4 by default;** only per action and with step-up (§9.5). |

### 3.3 The three promises → architecture

| Promise | Architectural carriers |
|---|---|
| **1 · Everything in one place** | Product/App registry and extension host (§7), shared navigation and Bootstrap read model (§25), core + bundled + app packaging (HQ blueprint), global search (§19.6), Files (§19.5), single permission model (§6) |
| **2 · Your stack stays, if you want** | Provider binding with four modes (§13), connection ladder, import/export, `external_refs[]`, maturity levels 0–3, connector contract |
| **3 · Operation by agents** | Action architecture (§8), autonomy regulator (§9), approvals + Channel Port (§10), operations inbox (§11), Flows (§12), Ottili MCP (§14), AI Gateway (§15), agent governance (§16) |

---

## 4. System context, layers and zones

### 4.1 System context

```text
 Users · company admins · agents (alran) · external MCP clients (ChatGPT, Claude, …)
        │                       │                          │
   Web (HQ · LD3 · alran AI · Ottili Console · alran Console)         MCP / REST / webhooks
        │                       │                          │
 ───────┴───────────────────────┴──────────────────────────┴────────  PUBLIC EDGE
                  Cloudflare (DNS · CDN · WAF)  →  Caddy (L7 ingress)
 ─────────────────────────────────────────────────────────────────  CONTROL PLANE
        Platform Gateway ── Auth (Keycloak behind auth.ottili.one) ── Policy/Entitlements
              │
   Actions · Approvals · Flows · Operations · Integrations · AI Gateway · Ottili MCP
   Credits/Billing · Events/Jobs · Files · Search · Registry · Audit · Legal/Privacy
              │
 ─────────────────────────────────────────────────────────────────  DOMAIN
        HQ (core · bundled · apps) · LD3 · connectors/adapters · alran runtime (DeerFlow/Codex adapters)
              │                                   │
 ─────────────┴───────────────────────────────────┴──────────────────  DATA / EXECUTION
   PostgreSQL (truth · RLS) · Valkey (cache/coordination) · object storage · outbox/events
   Agent sandboxes (per mission) · browser sandboxes · worker pools
              │
 ─────────────────────────────────────────────────────────────────  EXTERNAL
   Model providers (OpenRouter EU …) · Shopify · Stripe · DATEV · Microsoft 365 · WordPress · suppliers · channels
 ─────────────────────────────────────────────────────────────────  ADMIN / MANAGEMENT
   Tailscale ACL + strong operator auth + break-glass · Infisical · Verdaccio · observability stack
```

### 4.2 Layer model

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│ EXPERIENCE  HQ shell · LD3 UI · alran (AI · Code · API & Console) · Ottili Console│
│             channels (inbox, Slack, Discord …) · MCP clients                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ AGENT       alran runtime = harness adapters (DeerFlow · Codex)                  │
│             + Ottili governance: autonomy · grants · budgets · verification      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ CONTROL     Gateway · Auth · Company · Policy · Actions · Approvals · Flows ·    │
│ PLANE       Operations · Integrations · AI Gateway · Credits · Audit ·           │
│             Events/Jobs · Files · Search · Registry/Extension host               │
├─────────────────────────────────────────────────────────────────────────────────┤
│ DOMAIN      HQ core · apps · LD3 · connectors/adapters · (Connector Agent on-prem)│
├─────────────────────────────────────────────────────────────────────────────────┤
│ DATA        PostgreSQL (truth · RLS · company_id) · object store · Valkey · outbox│
├─────────────────────────────────────────────────────────────────────────────────┤
│ INFRA       ottiliserver01 (basement) · ottiliserver02 (Hetzner) · Cloudflare ·  │
│             Caddy · Tailscale · Infisical · Verdaccio                             │
└─────────────────────────────────────────────────────────────────────────────────┘
Rule: each layer calls only the layer directly beneath it — never around Gateway/Policy.
```

### 4.3 Trust zones

Logical zones exist even while several share a host. Network policy defaults to **deny between zones** except declared dependencies; product containers get no Docker socket and no host-repo mounts.

| Zone | Contents | Notes |
|---|---|---|
| `edge` | Cloudflare, Caddy | only public ingress |
| `control` | Gateway, Auth, Platform services | verified identity + company context required |
| `data` | PostgreSQL, backup repo, object store control | private |
| `worker` | job workers, LD3/Flows/Files workers, connector runtimes | private; outbound allowlisted |
| `agent` 🟠 | **agent sandboxes and browser sandboxes** (one per mission/company) | **no credentials inside**; egress per domain policy (§17); never in the control zone |
| `mgmt` | Tailscale-only admin, Infisical, break-glass | admin identity separate from customer identity |
| `obs` | metrics/logs/traces/alerting, off-site probe | independent failure domain from what it reports |

The `agent` zone is new (the old blueprint had no equivalent). Reason: DeerFlow-style harnesses execute model-driven code and browsing; their documented skill restrictions are **not** a security boundary (🟢 D1), so isolation is a network and process property of the Platform (AR-17).

### 4.4 Request lifecycle

```text
Client ─► Edge ─► Gateway
                    ├─ verify identity (session / API key / workload token / MCP OAuth)
                    ├─ resolve company + policy + entitlement context  → PlatformContext
                    ├─ rate / idempotency / size / deadline guard
                    ├─ route to owning API (no business logic in the Gateway)
                    └─ synchronous response  OR  202 Accepted + job_id/status URL
```

SSE/WebSocket streams use the same identity/company/policy context, bounded connection quotas and resumable cursors.

### 4.5 `PlatformContext` (propagated on every internal call, job, event)

| Field | Meaning |
|---|---|
| `company_id` | immutable tenant key (slug is routing metadata only) |
| `actor_chain[]` | ordered: **initiator** (user / external MCP client / webhook) → **agent or skill** (if any) → **service principal** |
| `request_id`, `trace_id`, `correlation_id`, `causation_id` | observability and event lineage |
| `deadline` | absolute time; callee MUST stop work after it |
| `idempotency_key` | required on mutating calls |
| `policy_revision` | revision used for the decision; execution re-evaluates |
| `autonomy` | `{selected, ceiling, effective}` for the current operation (§9.3) |
| `data_class` | highest data class touched so far (`public` < `internal` < `personal` < `secret`) |
| `mission_id` | if running inside an agent mission |
| `locale`, `timezone`, `currency` | company formatting context; storage stays UTC |

### 4.6 Actor chain

Authorization uses the **intersection** of the initiator's rights and the acting agent's grants. A skill or service never widens it. The receipt stores the whole chain (§8.5). Background work captures both the initiating actor and the effective service actor.

### 4.7 Acceptance tests — context

| ID | Test | Evidence |
|---|---|---|
| PAT-CTX-01 | A request without verified company context to a tenant-required endpoint returns an error; no default company is ever substituted | integration test |
| PAT-CTX-02 | `PlatformContext` is present and unchanged in a request → job → event → consumer chain (trace shows the same `company_id`, `actor_chain`, `correlation_id`) | trace assertion |
| PAT-CTX-03 | A call that exceeds `deadline` is cancelled by the callee and reported as `deadline_exceeded`, not retried blindly | fault-injection test |
| PAT-CTX-04 | An agent acting for user U can never exceed U's rights even if the agent holds a broader grant | negative test matrix |
| PAT-ZON-01 | Network policy test: from the `agent` zone, the control-zone database, Valkey and internal admin endpoints are unreachable | network probe |
| PAT-ZON-02 | Public exposure scan: only `edge` accepts inbound from the internet; all other zone ports are closed externally | scan report |

---
## 5. Identity, authentication and sessions

### 5.1 Authority and engine ✅ D-12

`auth.ottili.one` is the **single human authentication authority**. **Keycloak is the identity engine behind it** (credentials, passkeys/WebAuthn, TOTP, OIDC/SAML provider, identity brokering). Fine-grained authorization (who may do what on which object) stays in the Platform Policy service (§6), not in Keycloak roles.

| Concern | Owner |
|---|---|
| Credential storage, WebAuthn/passkey ceremonies, TOTP, external IdP brokering, OIDC/SAML endpoints, discovery, JWKS | Keycloak (engine) |
| Session records and revocation truth, step-up challenges, recent-auth, device list, security events, token policy, client registry, consent UI, account switch semantics | **Ottili Auth service** (PostgreSQL-backed) |
| Company membership, roles, product grants, entitlements | Platform Company/Policy (§6) |

**Exit strategy.** Ottili code MUST depend on standard OIDC/OAuth 2.1 semantics only. All Keycloak-specific calls live in one package (`auth-engine-adapter`). Replacing the engine must not change any product, app or SDK contract. 🟡 (consequence of AR-16 applied to Auth.)

`login.ottili.one` is removed after a redirect/deprecation window; no new code may use it.

### 5.2 Interactive flow

- Authorization Code + **PKCE S256**; `state`, OIDC `nonce`, exact redirect-URI match, single-use short-TTL authorization codes, issuer/audience validation, RP-initiated logout, client revocation.
- Products and apps are **OAuth/OIDC clients**, never alternate issuers, never owners of a password/passkey table. Browser clients use a **BFF**: the browser holds only an `HttpOnly`, `Secure`, `SameSite` session cookie bound to the product origin. Access tokens are short-lived and **never** readable root-domain cookies.
- Return targets are signed, relative and allow-listed. PKCE state is checked **before** provider error content is trusted.

### 5.3 Session model

| Property | Rule |
|---|---|
| Storage | durable in PostgreSQL; Valkey may cache lookup/revocation hints but is never the only revocation truth |
| Expiry | absolute and idle expiry; invalid expiry data fails closed |
| Refresh | opaque, hashed at rest, **single-use, rotated** in token families; reuse invalidates the family and emits a security event |
| Generation | every refresh carries the session generation it started from and MUST NOT revive a `signed_out`, `revoked` or newer generation |
| Strength | each session records authentication strength (`acr`/`amr`: password, passkey, MFA) and last-authentication time |
| Devices | the user can list and revoke sessions/devices; company/security admins see permitted metadata only |
| Propagation | sign-out, revocation, session revision and account switch propagate across tabs and devices |

**Step-up** is a first-class challenge with a *resume intent* (the original action, bound to its digest), not a generic "session expired" screen. Default recent-auth window 🟠 5 minutes; per-action override from the action definition (§8.2).

**Recovery** is its own high-risk state machine: verified email or approved method, rate limits, review of recent security events, one-time artifacts, session invalidation after sensitive reset, full audit. Recovery MUST NOT silently weaken a company's MFA policy.

### 5.4 Enterprise federation 🟠

- Company-specific IdPs (OIDC or SAML) are connected through Keycloak **identity brokering**; home-realm discovery by verified email domain.
- Federated sign-in **never creates company membership by itself.** Membership is Platform truth: by invitation, or by an admin-approved domain rule.
- Company policies: enforce MFA, restrict methods, session lifetime, allowed IP ranges (later), step-up thresholds.
- **SCIM provisioning** is a contract slot (`directory.sync.v1`), post-beta.

### 5.5 Machine and agent identity

| Identity | Credential | Scope |
|---|---|---|
| **Workload** (service, worker, job) | short-lived signed service JWT from Platform Auth to registered workloads; audience + service + environment (+ company where applicable) | long-lived shared internal tokens are migration-only with expiry telemetry |
| **Developer API key** | company-owned; prefix/ID + secret shown once; hash at rest; scopes; environment; product/module grants; expiry; last-used metadata; rotation; revocation | never bypasses entitlement or policy checks |
| **OAuth client for MCP / external apps** | OAuth 2.1 with PKCE, per-company consent; tokens carry company binding | §14 |
| **Agent principal** | an identity with lifecycle (create, pause, revoke), owner, grants, budget, autonomy selection | §16.2; **separate token audience** from humans and service accounts |
| **Platform operator** | separate operator identity + Tailscale ACL + strong auth; break-glass is audited | §6.7 |

Background jobs carry **both** the machine actor and the initiating user/company provenance.

### 5.6 "Sign in with Ottili" (OIDC provider) 🟠

Ottili can act as an OIDC provider for third parties and first-party apps (VD-39). The mechanism is part of the OAuth client registry (`PLT-W1-03`); consent scopes map to Platform permissions; public availability is **after the beta** (Doc 1 Anhang B #20). Authenticator functions needed by users (passkeys, TOTP, recovery codes) are native; a standalone authenticator app is an app-client topic, not a beta item.

### 5.7 Security events

Auth emits typed events (`platform.auth.login_succeeded.v1`, `…login_failed.v1`, `…token_reuse_detected.v1`, `…session_revoked.v1`, `…stepup_completed.v1`, `…mfa_changed.v1`, `…recovery_started.v1`). They feed audit (§22), anomaly signals (§18.7) and per-company security views in the Ottili Console.

### 5.8 Acceptance tests — Auth

| ID | Test |
|---|---|
| PAT-AUTH-01 | End-to-end: password login, passkey login, TOTP step-up, refresh rotation, logout, session revocation pass in a real browser against a real Keycloak |
| PAT-AUTH-02 | **Refresh-token reuse** invalidates the whole family and emits `token_reuse_detected`; the legitimate client must re-authenticate |
| PAT-AUTH-03 | State-machine/race tests: a late refresh cannot revive a signed-out or revoked session generation; concurrent refreshes yield exactly one winner |
| PAT-AUTH-04 | Redirect handling: unregistered, partially matching or non-allow-listed return targets are rejected; PKCE downgrade is rejected |
| PAT-AUTH-05 | Revocation survives a Valkey flush: revoked sessions stay revoked |
| PAT-AUTH-06 | Recovery cannot bypass a company MFA policy; recovery invalidates other sessions |
| PAT-AUTH-07 | API keys: secret shown once; stored hashed; scope violation → 403; revoked key → immediate 401; usage attributed to key id and company |
| PAT-AUTH-08 | Replacing the Keycloak adapter with a stub OIDC provider leaves all contract tests green (exit-strategy proof) |
| PAT-AUTH-09 | Federated sign-in from an unknown company IdP does not create membership |
| PAT-AUTH-10 | Step-up challenge resumes exactly the original action digest; a changed input after step-up is rejected |

---

## 6. Companies, tenancy, policy and entitlements

### 6.1 Company model

- `company` is the tenant. `company_id` is an immutable UUID; the human slug is routing metadata only.
- Users belong to **one or many companies** through `membership` (states: invited, active, suspended, removed). A session has exactly one *selected company*; switching company cancels in-flight company-scoped work, drops scoped caches and issues a new Bootstrap revision (§25.4).
- Company lifecycle: `active → suspended → deletion_pending → deleted` (deletion is a saga, §19.9).
- Company-level settings that the Platform enforces: autonomy ceiling (§9), allowed channels (§10), data-class/model policy flags (§15.4), credit caps (§20), MFA and session policy (§5.4), enabled products/apps (§7).

### 6.2 Roles and permissions

- Permission vocabulary: `<module>.<resource>.<verb>` — e.g. `hq.contacts.read`, `hq.orders.approve`, `ld3.sources.manage`, `platform.company.manage`, `platform.autonomy.set_ceiling`.
- **Built-in role templates** (per product, versioned): Owner, Admin, Member, plus domain roles (Sales, Warehouse, Purchasing, Finance, Editor, Reviewer). Custom roles are allowed; a role is a named set of permissions plus optional **attribute constraints** (e.g. "approve purchase orders up to 500 EUR").
- Separation of duties is expressible (requester ≠ approver) and enforced by Approvals (§10).
- Permissions and entitlements and feature flags are three **different** decisions: *may this actor do this on this resource* / *has this company bought this capability* / *is this code path rolled out*.

### 6.3 Policy decision contract

A single Platform Policy library/service defines inputs and outputs; UI caches are hints, never authority.

```ts
interface PolicyRequest {
  actor_chain: ActorLink[];            // initiator ∩ agent ∩ service
  company_id: string;
  module: string;                      // e.g. one.hq
  action_id?: string;                  // §8
  resource?: { type: string; id: string; attributes?: Record<string, unknown>; revision?: string };
  environment: string;
  risk?: "low" | "medium" | "high" | "critical";
  autonomy?: { selected: AutonomyLevel; ceiling: AutonomyLevel };
}
interface PolicyDecision {
  effect: "allow" | "deny" | "challenge" | "approval_required";
  policy_revision: string;
  reason_code: string;                 // stable, machine-readable
  obligations?: Obligation[];          // e.g. step_up, redact_fields, require_budget, four_eyes
}
```

Authorization chain (each layer is independently observable and testable):

```text
authenticated principal → active company membership → permission/policy decision
→ module/app entitlement → resource/object authorization → quota/budget/preflight
```

Decisions are **deny by default**, logged with `policy_revision` and `reason_code`, and **re-evaluated at execution time** for sensitive actions.

### 6.4 Entitlements

Entitlements answer "may this company use capability X?" and derive from the active plan version, add-ons, grants, trials/promotions, account state and explicit administrative grants. Products ask for **stable capability IDs** (from the Registry), never plan names. The durable evaluator is PostgreSQL-backed; snapshots are cached; changes emit `platform.entitlement.changed.v1` so long-running jobs can re-check before a costly next step. In the free beta every test company receives the beta plan grant with **hard credit caps** (§20.5, G6).

### 6.5 Tenancy enforcement — five layers

1. **Application policy** (this chapter) — always.
2. **Repository/query scoping** — every query is company-scoped by construction (typed repository API; no raw cross-tenant query helpers in product code).
3. **PostgreSQL row-level security** — on all shared tenant tables; transaction-local verified context (`SET LOCAL app.company_id = …`); application DB roles **cannot bypass RLS**.
4. **Namespaced infrastructure** — cache keys, queues, search documents, object keys, event partitions and metrics carry company scope (metrics avoid per-company high-cardinality labels; use logs/traces for drill-down).
5. **Test-time proof** — cross-tenant property tests and adversarial suites (§6.9) are release gates.

**RLS adoption is migration-gated:** table inventory → owner/backfill → `NOT NULL` company key → policies → negative tests → restricted DB role → production canary. Superadmin and batch paths use separately authenticated roles and are audited. The tenant key is part of primary/unique/index definitions where data is multi-tenant. 🟢 BP-Infra §12, BP-Foundation §63.

### 6.6 Search, caches, vectors

Embedding and vector stores follow the same tenant isolation as relational data: tenant filter **before** retrieval **and** verification **after** retrieval; no shared mutable caches across companies; tenant-less events and cross-tenant defaults are **release blockers**.

### 6.7 Platform operator context

Cross-company operations (support, repair, migration) are a **separate privileged action type** with: operator identity (not a customer identity), stated purpose, target company, scope, time limit, approval where required, and a customer-visible audit entry. 🟠 Customers can grant a time-limited **support access grant** from the Ottili Console; absent a grant, operators see metadata only.

### 6.8 Company deletion and export

See §19.9 (lifecycle) and §13.9 (export). Company deletion is a saga covering primary stores, files, search, caches, analytics, backups (with separate expiry), subprocessors, legal-hold exceptions, and completion evidence.

### 6.9 Tenant-isolation test suite (release gate)

| Attack | Expectation |
|---|---|
| Substitute another company's object ID in API, MCP tool args, flow input, webhook | deny at policy/query/RLS layers; security event |
| Cross-tenant search and facets | zero foreign documents or counts |
| Cache poisoning / key collision across companies | impossible by key namespace; test with colliding IDs |
| Job payload swap or event replay into another company | rejected by context check |
| File path / signed-URL guessing | opaque keys; URLs bound to company + audience; short-lived |
| Agent retrieval of another company's data through context service or Ottili MCP | denied; retrieval fixtures per release |
| Operator without grant reading customer content | denied; metadata only |
| Missing `company_id` on a tenant-required job/event | rejected, dead-lettered, alert |

### 6.10 Acceptance tests — tenancy, policy, entitlements

| ID | Test |
|---|---|
| PAT-TEN-01 | Two test companies cannot read each other's API rows, files, jobs, search results, usage or billing records (property + integration + adversarial) |
| PAT-TEN-02 | The application DB role cannot read a foreign tenant row even with a crafted query; RLS policies exist on every inventoried tenant table (inventory diff) |
| PAT-TEN-03 | Company switch cancels in-flight work of the previous company, drops scoped caches and yields a new Bootstrap revision |
| PAT-POL-01 | Every policy decision stores `policy_revision` + `reason_code`; unknown action/resource → `deny` |
| PAT-POL-02 | A sensitive action allowed at preflight is re-evaluated at execution; lowering rights between the two steps blocks it |
| PAT-POL-03 | Entitlement withdrawal mid-job: the next costly step re-checks and stops with a typed reason |
| PAT-POL-04 | Operator access without a support grant returns metadata only; with a grant, content access is time-limited and audited |
| PAT-POL-05 | Permission, entitlement and feature flag are three distinct code paths: disabling a flag does not grant/revoke a permission and vice versa |

---

## 7. Registry, manifests, apps, extensions and skills

### 7.1 One Registry

One versioned **Product Registry** is the source of truth for product/module/surface/capability identity, API namespaces, entitlement keys, release compatibility and discovery metadata. Public websites, docs, status, changelog, downloads and legal pages are **projections** of signed Registry/Release/Status/Legal data. **No second registry** (Cloud, marketing, console) may exist.

### 7.2 Packaging — core, bundled, app ✅ D-03

Every HQ module declares one packaging class in its manifest:

| Class | Meaning | Deactivatable | Beta |
|---|---|---|---|
| `core` | always on: CRM (contacts, leads, deals), quote → order → invoice → payment, products + stock, purchasing, tasks, base documents, roles/rights, import/export, BOM-lite | no | complete |
| `bundled` | shipped and on by default, can be switched off: finance/accounting + DATEV (default on in DACH) | **yes** | complete |
| `app` | installable per company: manufacturing/WMS, office, dropshipping, restaurant, shop … | yes | as required by missions M1–M6 and integrations |

"Slim core" and "maximal feature set" are therefore one setting, not a contradiction (W-01 resolved). A company can deactivate unneeded bundled parts and add apps (VD-15, VD-16).

### 7.3 Manifests

Three manifest schemas, separate on purpose.

**Product manifest** (Ottili-owned products/modules; signed):

```yaml
schema_version: ottili.product/v3
manifest_version: 3.0.0
product_family_id: ottili
product_id: one
module_id: one.hq
module_version: 3.0.0-alpha.1
packaging: core            # core | bundled | app
host: { surface_id: one.hq.web, route_base: /hq }
display: { name_key: products.hq.name, accent_token: product.hq.accent }
routes:
  - { id: hq.orders, path: /orders, required_permissions: [hq.orders.read] }
capabilities:
  files: { mode: embedded }
  flows: { node_namespace: hq }
actions: { catalog_ref: contract://hq/actions/v3 }          # every UI function is an action (AR-21)
mcp: { toolsets: [hq_read, hq_sales_draft, hq_purchasing_with_approval], namespace: hq_ }
binding:                                                      # §13
  provides_entities: [organization, contact, product, stock, order, invoice]
  default_mode: native
data_classes: [customer_content, personal_data, financial_record]
events: [hq.order.created.v1, hq.stock.moved.v1]
legal_profile: one-hq-eu-v3
ai_profile: hq-assistant-v3
autonomy: { default_ceiling: T3, action_overrides: {} }
compatibility: { foundation: ">=3.0.0-alpha.1 <4", platform: ">=3 <4" }
integrity: { digest: sha256:…, signature: { key_id: one-release-2026, algorithm: ed25519, value: … } }
```

**App manifest** (installable per company; first- or third-party; see §7.5): `ottili.app/v3` — adds `trust_tier`, `entrypoints` (cross-origin iframe UI, HTTPS service), `permissions.requested`, `contributions`, `network.allowed_origins`, `data.retention_on_uninstall`, lifecycle actions, `binding` capability declaration and maturity level (§13.5).

**Platform surface manifest** (non-installable surfaces: Auth, Console, Developer Portal, Status, Lab): `ottili.platform-surface/v1`, so these surfaces are not cast as Products or tenant Apps.

The Registry validates signature, owner, schema, route-base ownership, route collisions, permission vocabulary, legal profile, compatibility and rollout. Manifests are immutable by `(product_id, product_version, module_id, module_version, digest)`. Unknown fields, invalid arrays, trailing semver junk, unsigned required bundles or missing origins are **validation errors, not warnings**.

### 7.4 Install lifecycle

```text
submitted → automated_review → human_review → approved → signed
→ install_pending → installed_disabled → enable_pending → enabled
enabled → update_pending → enabled(new revision) | rollback_pending → enabled(old revision)
enabled/disabled → suspend_pending → suspended → reinstatement_review
installed_* → uninstall_pending → data_export_or_retention → uninstalled
any executable state → emergency_suspended
```

Every transition has actor, policy, expected revision, timeout, idempotency key, compensation and receipt. Updates never mutate the active revision in place. Uninstall preserves customer export and legal-hold duties and removes tokens, subscriptions and grants **before** data expiry. Reviewed first-party release deployment runs schema migrations once per environment; **company installation only creates tenant-scoped configuration/data through versioned Actions and MUST NOT execute ad-hoc DDL.**

### 7.5 Extension runtime (fail closed)

- Publisher identity binds to a versioned **signing key** (`ed25519`); canonical JSON bytes (RFC 8785), manifest digest, bundle digest and signature are verified **before review and again before execution**. Revoked key/bundle dominates tenant state and produces an auditable suspension. Kill switch, signature revocation and publisher suspension override tenant enablement.
- **Third-party web UI** runs only in a **cross-origin sandboxed iframe** with exact origin, bridge-protocol version and message-schema checks. Web Components share the host JS realm and are allowed only for reviewed first-party code. Background browser logic uses restricted workers.
- **Third-party server code** never runs inside Platform processes: HTTPS/webhook, or a managed isolated app runtime (WASM vs. microVM/container: `ADR-P-04`).
- Every requested permission needs company-admin consent; grants may be narrower than requested. High-risk permissions (payments, secrets, export, deletion, unrestricted network, AI training) require manual review and explicit UI disclosure.
- CSP forbids same-origin privilege, top navigation, downloads and network destinations not declared in the manifest. The bridge limits message size/rate, correlates request/response ids, validates source window/origin, and terminates unresponsive frames.
- **Closed contribution vocabulary**, each with a transactional owner:

| Contribution | Owner |
|---|---|
| route, navigation, command | Foundation Registry |
| action, AI tool | Action Registry |
| widget, record section, custom field, report | product/app contribution registry |
| Flow node, trigger | Flows node registry |
| file view | Files contribution registry |
| search index definition (`search_contribution`) | Search registry (§19.6) |
| import/export adapter | Data lifecycle registry |
| webhook/event subscription | Developer Platform / Event registry |
| connector capability declaration | Integrations registry (§13) |
| channel adapter | Channel Port registry (§10.3) |

An unrecognised contribution is an error. Activation prepares all handlers and commits **one installation revision** or compensates every prepared registration.

### 7.6 Tenant-private apps ✅ D-27 timing / 🟠 design (VD-19)

Scenario: a shop needs an exotic supplier no one else integrates. Options: use the supplier's API through the generic connector mechanism (§13.8), **or** write a custom app and upload it so **only that company** (not other tenants) has it.

| Aspect | 2026 (beta) | Q1–Q2 2027 |
|---|---|---|
| Data model | `app_listing.visibility ∈ {public, private}`, `app_listing.allowed_company_ids[]`, `publisher.owner_company_id`, company-scoped publisher keys | – |
| Upload and review | – | developer tenant, SDK, local host simulator, review classes (automated for low-risk contributions, human for high-risk) |
| Runtime | first-party lifecycle only | third-party isolated runtime (`ADR-P-04`) |

Private apps use the **same** install lifecycle, permissions, kill switch and receipts as every other app. 🟢 Gap R-06: the current GERMO pack has no job for it → job family `FS-02`.

### 7.7 Marketplace

Marketplace owns discovery, commercial metadata and lifecycle orchestration. It **does not execute app code**. Required surfaces: listing/version/publisher registry; automated static and contract checks; human review with decision evidence; compatibility matrix and staged rollout; install/update/rollback/uninstall; license, billing, refunds and entitlement mapping; privacy/security/data-use disclosure; vulnerability notification and emergency suspension; ratings/support only after the operational lifecycle is reliable. Every listing links exact terms, privacy policy, subprocessors, requested permissions, retention and support owner. Third-party listing is **not** part of the 2026 beta; the registry + lifecycle ship for first-party apps.

### 7.8 Open-source apps inside the ecosystem (VD-33) 🟠 D-23

Goal: customers do not have to leave the Ottili ecosystem. Office, design, notes, files, mail and calendar tools are delivered **as apps**; where permissively licensed open-source tools are good enough they are **embedded** (MIT/Apache and similar) through the extension host, not rebuilt. Rules:

1. License and maintenance review per candidate before adoption (D-23, D-31): license, maturity, multi-tenancy, operating cost, security posture.
2. Embedded OSS runs as an isolated app (iframe/service) integrated through Files, Auth (OIDC), Search, Notifications and Actions — never by copying code into Platform packages.
3. Commercial equivalents (e.g. proprietary office/design suites) are **inspiration only** via REA/clean-room (D-25); no code, assets or trade dress.
4. SBOM and license inventory are generated per release (§24.7).
5. Timing: office/design/notes/chat/meetings apps are **2027** (Doc 1 §2.1); the *mechanism* ships in the beta.
6. A **command terminal app** (VD-34) is a command interpreter over Actions (each command maps to an action, same policy/receipts) — not a Linux VM; 🟠 post-beta.

### 7.9 Skills

A **skill** is versioned guidance + capability metadata bound to executable Actions. It carries intent, inputs, required context, action references, examples, safety/approval behaviour, expected outputs and verification — **never credentials or hidden authority.**

```yaml
schema_version: ottili.skill/v1
skill_id: ld3.publish_verified_article
version: 1.0.0
owner: one.ld3
intents: [publish verified article]
requires_context: [company, ld3.content_package]
actions:
  - { id: ld3.article.preflight_publish, version_range: ^3.0.0 }
  - { id: ld3.article.publish,            version_range: ^3.0.0 }
action_bundle_digest: sha256:…
data_use_profile: ld3.editorial.default/v1
approval_policy: ld3.editorial.publish
verification: [ld3.article.publication_receipt]
signature: { key_id: …, algorithm: Ed25519, value: … }
```

Two skill families that must not be confused: **operational skills** (this section; bound to actions; used by alran at runtime, also as lightweight integrations — connection ladder step 5) and **developer skills** (the `skills` repository used by GERMO; not shipped to customers). Browser skills (e.g. Playwright-based) exist only as policy-gated fallbacks (§17). `allowed-tools` in a harness skill file is **not** a security boundary (🟢 D1); enforcement stays in the Action layer.

### 7.10 Acceptance tests — registry and extensions

| ID | Test |
|---|---|
| PAT-REG-01 | Manifests validate fail-closed: unknown field, bad semver, missing origin, unsigned bundle, route collision each reject registration |
| PAT-REG-02 | A deactivatable bundled module can be switched off per company without breaking `core` journeys; `core` modules cannot be switched off |
| PAT-REG-03 | One Registry: a repository scan finds no second product/capability registry (marketing, console, cloud) |
| PAT-EXT-01 | Activation is transactional: a missing handler for one contribution aborts activation and rolls back all prepared registrations |
| PAT-EXT-02 | Revoked publisher key suspends all of its bundles within the revocation SLA; execution is blocked |
| PAT-EXT-03 | Iframe sandbox: a test app cannot read host cookies/storage, navigate top, download, or reach undeclared origins |
| PAT-EXT-04 | Update creates a new revision; rollback restores the previous revision and receipts exist for both |
| PAT-EXT-05 | Uninstall removes tokens/subscriptions/grants before data expiry and still allows export |
| PAT-EXT-06 | Private-app visibility: company A's private listing is invisible and uninstallable for company B (data model test in 2026) |
| PAT-SKL-01 | A skill referencing an action outside its `action_bundle_digest`, or whose signature fails, is rejected |
| PAT-SKL-02 | A skill cannot carry credentials: manifest scanner rejects secret-like material |

---
## 8. Action architecture

### 8.1 Concept

A **command** is a discoverable UX entry (palette, menu). An **action** is an executable, typed, versioned capability. Both are machine-readable so that alran and external clients discover and invoke them **without screenshots**.

> **P2 / AR-02:** UI, API, Flows, alran and external MCP clients call the **same** actions with the same validation, rights, approvals and audit. Actions are thin typed shells over domain services. **Business logic stays in the domain** (HQ, LD3, apps); there is no second rulebook "for the AI". 🟢 Doc 1 §3.2

Action id format: `<area>.<object>.<verb>` — e.g. `crm.customer.create`, `inventory.stock.reserve`, `purchasing.po.submit`, `catalog.product.publish`, `ld3.content.publish`, `flows.pipeline.execute`, `notifications.send`. The id is stable; the definition has a semantic version.

### 8.2 `ActionDefinition` (v3)

```ts
type EffectClass = "read" | "draft" | "internal_change" | "external_change" | "destructive";
type AutonomyLevel = "T0" | "T1" | "T2" | "T3" | "T4" | "T5";

interface ActionDefinition<I, O> {
  id: string;                         // crm.customer.create
  version: string;                    // semver
  owner: string;                      // module that implements it, e.g. one.hq
  input_schema: JsonSchema<I>;
  output_schema: JsonSchema<O>;
  required_permissions: string[];
  required_entitlements?: string[];

  effect_class: EffectClass;          // drives the autonomy matrix (§9.3)
  effects: {
    mutation: "none" | "create" | "update" | "delete" | "mixed";
    externality: "none" | "ottili" | "third_party" | "public";
    reversibility: "reversible" | "compensatable" | "irreversible";
    reads: DataClass[]; writes: DataClass[]; destinations: DataDestination[];
  };
  risk_class: "low" | "medium" | "high" | "critical";   // typed risk classes fight approval fatigue
  max_autonomy_default?: AutonomyLevel;                 // e.g. destructive → "T3" unless the company raises it per action
  step_up?: { required: boolean; max_age_seconds?: number };

  supports_dry_run: boolean;
  idempotency: "required" | "supported" | "none";
  revision_precondition?: "required" | "supported";     // optimistic concurrency (If-Match)
  timeout_seconds: number;
  cancellation: "cooperative" | "transactional" | "unsupported";
  retry_safety: "safe" | "idempotency_key_required" | "unsafe";

  cost_class: "free" | "metered" | "expensive";
  cost_budget_schema?: JsonSchema<CostBudget>;
  secret_refs?: SecretRequirement[];                    // references only, never values
  provider_data_use_profile?: string;                   // §15.5
  approval?: { policy: string; expires_in_seconds: number };

  binding?: { entity: string; mode_aware: true };       // §13: router resolves native vs bound handler
  verification: { mode: "read_back" | "provider_receipt" | "none"; hook?: string }; // "none" only for read
  compensation_action?: { id: string; version_range: string };
  effect_summary_schema: JsonSchema<unknown>;           // plan/effect disclosure shown to humans
  kill_switch_group: string;                            // §9.6
  tool_export: { name: string; description_i18n_key: string; hidden_params?: string[] };
}
```

A control-plane mutation is never labelled read-only. An action whose **observed** effect exceeds its **declared** effect fails closed and opens a security event (AR-20).

### 8.3 Execution pipeline

```text
caller (UI · API · Flow · alran · MCP)
   │  invoke(action_id, input, PlatformContext)
   ▼
RESOLVE  action + version, caller identity, binding for the touched entity
   ▼
PREFLIGHT  (a) schema validation  (b) permissions ∩ grants  (c) entitlement  (d) tenant check
           (e) revision guard   (f) data-class / destination / model-eligibility check
           (g) credit/budget RESERVATION  (h) effective autonomy resolution (§9.3)
   ▼
DRY-RUN (if supported/requested)  →  PLAN & EFFECT DISCLOSURE
   ▼
APPROVAL / STEP-UP  if the effective level requires it (§9.3, §10) — bound to the exact digest
   ▼
EXECUTION-TIME RE-AUTHORIZATION  (policy + autonomy + kill switch + budget re-checked)
   ▼
EXECUTE  → binding router → native handler | connector (§13)
   ▼
VERIFY  (read-back / provider receipt)  →  on failure: COMPENSATE or mark unknown_external_result
   ▼
RECEIPT (append-only, hash-chained)  →  OUTBOX events  →  CAPTURE / RELEASE reserved credits
```

Sensitive reads, any external egress and any mutation require preflight and a **policy-visible plan**, even when no data changes.

### 8.4 Outcome model (P7)

| Outcome | Meaning |
|---|---|
| `succeeded` | executed **and** verified |
| `partial` | some of the declared effects verified, others not |
| `failed` | not executed or fully compensated; error class attached |
| `unknown_external_result` | outcome of an external call is unclear (timeout after send) → reconciliation job or human; **never reported as success** |
| `awaiting_approval` / `awaiting_step_up` | pipeline paused durably, no worker held |
| `blocked_policy` | policy/autonomy/kill switch/budget refused |

Error classes: `retryable`, `permanent`, `unknown_external_result`, `policy_denied`, `approval_required`, `step_up_required`, `budget_exhausted`, `conflict` (revision mismatch), `unsupported_by_provider` (degrade to a human task, §13.5).

### 8.5 Receipt

Append-only, hash-chained per company (tamper evidence), never contains secrets or unrestricted personal snapshots.

| Field group | Content |
|---|---|
| Identity | `receipt_id`, `action_id`, `action_version`, `action_digest`, `input_digest`, `output_digest`, schema digests |
| Actors | full `actor_chain` (initiator · agent/skill · service principal); `mission_id`, `run_id`, `task_id` if any |
| Decision | `policy_revision`, autonomy `{selected, ceiling, effective}`, approval ids, step-up evidence |
| Effects | **declared** effects, **observed** effects, destinations, data classes, provider data-use profile |
| Cost | credits reserved/captured/released, model/provider cost lines |
| State | resource revisions before/after, idempotency key, verification result, compensation record |
| Trace | `trace_id`, `correlation_id`, `causation_id`, timestamps |
| Epistemics | evidence is tagged `observed` / `inferred` / `hypothesis` (AR-23); the model's chain of thought is **not** stored — receipts, not hidden reasoning |

### 8.6 Grants

```ts
interface Grant {
  id: string; company_id: string;
  subject: { type: "user" | "agent" | "skill" | "service"; id: string };
  action_pattern: string;                           // "crm.*", "purchasing.po.submit"
  constraints?: {
    input_predicates?: Predicate[];                 // e.g. total_amount <= 200 EUR
    max_cost?: Money; max_cost_period?: "call" | "day" | "month";
    max_count?: number; time_window?: TimeWindow;
    channels?: string[]; destinations?: string[];
    expires_at?: string;
  };
  status: "active" | "paused" | "revoked"; created_by: ActorLink;
}
```

Effective capability = initiator's rights **∩** agent/skill grants. Revocation is effective immediately (no cache longer than the revocation SLA). Autonomy templates (§9) are **policy templates over grants, approval policy and budget** — not a separate flag that could be bypassed.

### 8.7 Tool export

Every registered action is exported automatically as an OpenAI function tool, an Anthropic tool and an MCP tool definition, filtered by `caller rights ∩ agent grants ∩ toolset`. "Every tool is steerable by alran" is therefore a by-product of registration. Exports include stable names, JSON Schema, effect class and approval hints in the description, hide internal parameters, and are version-pinned (§14).

### 8.8 Product obligations and parity

1. **Every UI function is an action** (target set by Doc 1 §4.2; the first ≈30–40 actions that carry M1–M6 are listed in Appendix C).
2. The product UI calls the action layer (or an SDK generated from the same schema); a bespoke UI endpoint that mutates data without an action is a defect.
3. **Parity matrix:** for each action, the same validation and error cases hold on the UI path and the action path; tests exist per action.
4. Registration is part of the product manifest (`actions.catalog_ref`); an unregistered mutation fails the contract gate.

### 8.9 Idempotency and resumption

- Mutating calls carry an idempotency key; `(company_id, action_id, idempotency_key)` stores the result for a TTL so a retry returns the stored outcome.
- Mission steps use `(mission_id, step_id, input_digest)` and perform a **receipt lookup before executing**, so resuming after a crash never repeats an action (§16.3).
- External calls use `(action, input_digest, resource_revision)` as outbound idempotency basis; inbound webhooks use `(company, binding, entity, external_event_id)` (§13.6).

### 8.10 Acceptance tests — actions

| ID | Test |
|---|---|
| PAT-ACT-01 | **Parity:** for every registered action the UI path and action path return the same validation errors and enforce the same rights (generated matrix) |
| PAT-ACT-02 | Preflight blocks: missing permission, missing entitlement, wrong tenant, stale revision, ineligible destination/model, exhausted budget — each with its own reason code |
| PAT-ACT-03 | A declared-`read` action that writes (observed > declared) fails closed and opens a security event |
| PAT-ACT-04 | Verification failure after a write yields `partial`/`failed` plus compensation or `unknown_external_result`, never `succeeded` |
| PAT-ACT-05 | Idempotent retry returns the stored receipt; no second effect |
| PAT-ACT-06 | Receipts are hash-chained; tampering with one receipt breaks verification |
| PAT-ACT-07 | Tool export for a caller shows only tools within `rights ∩ grants ∩ toolset`; names are stable across patch versions |
| PAT-ACT-08 | Grant revoked between two calls: the second call is blocked within the revocation SLA |
| PAT-ACT-09 | An unregistered mutating endpoint is detected by the contract gate (route inventory vs. action registry) |

---

## 9. Autonomy: levels T0–T5 ✅ D-11

### 9.1 Levels

Autonomy is a **regulator**, enforced **outside the model** by grants, approval policy, budget reservation and sandboxes.

| Level | Name | The agent may … | Enforcement |
|---|---|---|---|
| **T0** | Observe | read, analyse, report | grants limited to effect class `read` |
| **T1** | Suggest | produce drafts/proposals with no effect | `draft` actions only; output lands as a normal **draft record / inbox proposal** |
| **T2** | Execute internally | make reversible internal changes **inside rules** (amounts, quantities, objects) | grants with input predicates; receipt + verification |
| **T3** | External with approval — **default** | perform external/consequential actions **only after approval** of the exact action | approval binding (Channel Port), step-up for high risk |
| **T4** | External within hard limits | external actions **without individual approval** inside amount · count · time · channel · expiry limits | grants with `max_cost`, `max_count`, `time_window`, `channels`, `expires_at`; credit reservation; anomaly stop; kill switch; post-review |
| **T5** | Fully autonomous (opt-in) | everything inside platform rules, **without** company-set limits | only the **Owner**; fresh login (step-up) + liability notice; the five guardrails still apply |

### 9.2 Selection and ceiling

- **Company ceiling:** the maximum level the company allows (admin, Ottili Console, permission `platform.autonomy.set_ceiling`). 🟠 Default ceiling **T3** — nothing external runs unattended until an admin raises it deliberately. Per-action-type ceilings are allowed ("purchasing never above T3").
- **Selection:** users, agents and missions choose a level **at or below** the ceiling. **Default selection is T3.**
- **Most specific wins:** `mission×action_type` > `mission` > `agent×action_type` > `agent` > `user×action_type` > `user` > company default.
- **Overrides by action type** are first-class: "purchasing up to 200 EUR without approval, above that approval through the Channel Port" (the iPhone example, variant A/B, VD-28).
- **Resolution (pseudo-code):**

```text
selected  = most_specific_selection(context) ?? T3
cap_co    = company_ceiling(action_type)                       # company can only lower via ceiling
cap_act   = action.max_autonomy_default (unless the company raised it for this action, with step-up)
effective = min(selected, cap_co, cap_act)
if kill_switch(active for action.kill_switch_group or company) → blocked
```

- **Resolved twice:** at preflight and again at execution, so a lowered ceiling also hits executions already waiting.

### 9.3 Behaviour matrix (effective level × effect class)

Legend: **A** = executes automatically (inside grant constraints) · **P** = becomes a *proposal/approval request* for a human in the inbox · **X** = refused (`blocked_policy`, reason `autonomy_too_low`) · **S** = approval **and** step-up.

| Effect class | T0 | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|---|
| `read` | A | A | A | A | A | A |
| `draft` | X | A | A | A | A | A |
| `internal_change` (reversible) | X | P | A (within rules) | A (within rules; else P) | A | A |
| `external_change` | X | P | P | P (approval) | A (within hard limits; else P) | A |
| `destructive` / irreversible | X | P | P | S | S unless explicitly enabled per action with step-up | A, but only Owner-enabled; trash-first |

A request the actor is *rights-wise allowed* to make but the effective level does not permit becomes **P** (a decision in the inbox) rather than a silent failure — except at T0, which only observes.

### 9.4 T4 — the hard limits

T4 is available only through grants that carry **all** of: `max_cost` (per call and per period), `max_count`, `time_window`, `channels/destinations`, `expires_at`. Mechanics: credit reservation per execution; **anomaly stop** (rate, amount, destination novelty); automatic **fall-back to T3** on any breach; after-the-fact review items for every autonomous execution; a **shadow phase** (proposals measured without effect) before T4 is enabled for a company (family `FB-13`). A temporary "approve similar for N hours within limits" decision creates a time-boxed T4 grant; for high-risk classes it requires step-up.

### 9.5 T5 and the destructive rule (AR-30)

T5 is activatable only by the Owner after step-up and a liability notice whose **version is written into every receipt**. The wording is a legal task (D-28 🔴; hint, not advice). Destructive/irreversible actions are never T4 by default; enabling that requires an explicit per-action decision with step-up.

### 9.6 The five guardrails (valid on every level, T5 included) ✅ D-11

1. **Kill switch** for every admin, effective in seconds, per action group or company-wide, audited.
2. **Audit and recoverability:** deleted things go to a trash first; the audit log is append-only.
3. **T5 only by the Owner** with fresh login and liability notice.
4. **Credits stay:** if the balance is empty, alran stops.
5. **Platform rules win:** an agent can neither raise its own rights nor touch audit, backups or another tenant.

### 9.7 The regulator in the product

Label (English base string, German via i18n): **"Choose how autonomous alran can do actions"** (`autonomy.regulator.label`). Present in alran AI and in the alran panels of HQ and LD3. Levels above the ceiling are locked; T5 sits behind a confirmation. The ceiling and per-action overrides are administered in the Ottili Console.

### 9.8 Mapping to harness approval/sandbox modes (indicative 🟠)

| Level | Codex-style (alran Code) | DeerFlow-style (alran AI) |
|---|---|---|
| T0/T1 | `read-only` sandbox, approvals `on-request` | tools limited to read/draft Ottili toolsets |
| T2 | `workspace-write`, approvals `on-request` | internal toolsets within grants |
| T3 | `workspace-write`, approvals `on-request` for network/outside workspace | external toolsets only through approval-bound actions |
| T4 | `workspace-write`, `granular`/limited auto-approval inside limits | grants with limits |
| T5 | `danger-full-access`, `never` | full toolset per Owner decision |

The mapping is a **contract-tested adapter feature**, not an assumption: approval values and `wire_api` are version-dependent (🔴 `wire_api` unverified, Doc 2 §9.2 #1). DeerFlow has no native tenant-aware approval model, so the Action layer enforces everything.

### 9.9 Acceptance tests — autonomy

| ID | Test |
|---|---|
| PAT-AUT-01 | The behaviour matrix (§9.3) holds for a generated cross-product of levels × effect classes × grants |
| PAT-AUT-02 | Company ceiling always wins: a mission selecting T4 under a T3 ceiling executes as T3 |
| PAT-AUT-03 | Lowering the ceiling while an execution waits blocks it at execution-time re-resolution |
| PAT-AUT-04 | T4: a purchase of 199 EUR runs unattended; 201 EUR becomes an approval; a 4th purchase beyond `max_count` becomes an approval; after `expires_at` the grant is dead |
| PAT-AUT-05 | Kill switch: group- and company-wide, effective within the SLA, for running missions and queued actions |
| PAT-AUT-06 | T5 cannot be enabled by a non-Owner, without step-up, or without recording the liability-notice version |
| PAT-AUT-07 | An agent cannot raise its own grants or ceiling, nor read audit/backups/other tenants (guardrail 5) |
| PAT-AUT-08 | Empty credit balance stops all agent actions with `budget_exhausted` (guardrail 4) |
| PAT-AUT-09 | Destructive action at T4 without an explicit per-action enablement is refused/escalated to approval + step-up |
| PAT-AUT-10 | Shadow mode records what T4 *would* have done without effect and produces the review report |

---

## 10. Approvals and the Channel Port ✅ D-10

### 10.1 Approval object

Approvals are durable, auditable Platform objects (`PLT-W1-17`, one approval service for humans **and** agents):

| Field | Content |
|---|---|
| Target | `action_id`, `action_version`, `input_digest`, `resource_revision(s)`, effect disclosure (plan), risk class |
| Parties | requester (actor chain), approver policy (users/roles, four-eyes, separation of duties, thresholds) |
| Time | `expires_at`; reminders; escalation chain |
| State | `pending → approved | rejected | expired | superseded → executed | execution_failed` |
| Evidence | decision maker, channel, timestamp, step-up evidence, comment |

Rules: **a changed input invalidates the approval** (new digest ⇒ `superseded`). Approving does not perform the action inside the approval transaction; a follow-up **idempotent job** executes the approved intent after execution-time re-authorization. An agent can never approve its own requests (SoD). HQ thresholds (discount, four-eyes, company thresholds) and LD3 review gates are **rules and views** on this one service, not separate approval systems (W-18, R-49).

### 10.2 Delegation and escalation

Delegation (with period and scope), out-of-office, reminders, escalation to next role, and finally the **web inbox** as the guaranteed end of every chain.

### 10.3 Channel Port

**Approvals, notifications and questions flow through one port. Channels are adapters, not architecture.** Telegram was only a test harness. ✅ D-10

```ts
interface ChannelAdapter {
  id: string;                                     // "web_inbox" | "slack" | "discord" | "telegram" | …
  capabilities: { interactive_buttons: boolean; threads: boolean; attachments: boolean; delivery_receipts: boolean };
  deliver(intent: DeliveryIntent): Promise<DeliveryReceipt>;     // idempotent
  handleCallback(req: SignedCallback): Promise<ChannelEvent>;    // verifies provider signature + our token
  linkAccount(flow: LinkFlow): Promise<ChannelIdentity>;         // only via confirmed login
  health(): ChannelHealth;
}
```

| Adapter | Role | Time |
|---|---|---|
| **Web inbox** (Operations inbox in the Ottili ONE dashboard) | **mandatory**; fallback for all others | beta |
| Slack | adapter (app per company, interactive messages) | beta 🟠 |
| Discord | adapter (bot per company) | beta 🟠 |
| Telegram | adapter (company bots, signed inline buttons; exists as `PLT-W1-33`) | beta |
| WhatsApp | adapter | later; needs a verified Meta business account and approved message templates (🔴 unverified, Doc 2 §9.2 #15) |
| Own mobile app | adapter | long-term, with app clients |

**Rules for every adapter:**

1. **An approval is the exact action.** Each button carries a signed token bound to `approval_id`, `action_id`, `input_digest`, `resource_revision`, `expires_at`, a nonce and the decision; **single use**. A channel approval never replaces the execution-time policy check.
2. **Step-up on the web for high risk** (large amounts, T4/T5 changes, deletion): the channel button is not enough; re-login/MFA on the web.
3. **Account linking** only via a confirmed login. Unknown senders can trigger nothing; inbound channel text is **untrusted data** (AR-06).
4. **Per-company configuration:** enabled channels, categories → channel, quiet hours, **digests** instead of single messages at volume.
5. **Data minimisation:** messages contain the minimum plus a deep link; no secrets; personal data sparingly (the channel provider is a processor, G2).
6. **Delivery is evidenced:** idempotent, retried, delivery receipt in audit; an unanswered approval walks the escalation chain, ending in the web inbox.
7. **Auto-publish (LD3) is opt-in per project;** the default is approval through the port.
8. Harness-native channels (e.g. DeerFlow's) are **not** operated in parallel (§16.4).

Human work orders — e.g. "assemble this phone" (VD-28) — are delivered the same way: a task/notification intent to the employee on his preferred channel, with a deep link to the task.

### 10.4 Notification intents

Domain events create **durable notification intents**; the notification service owns preferences, inbox state, delivery attempts, deduplication, retries and provider receipts. Products emit typed intents and never send arbitrary email or chat messages directly.

### 10.5 Acceptance tests — approvals and channels

| ID | Test |
|---|---|
| PAT-APR-01 | An approval token cannot be reused, replayed after expiry, or applied to a changed input/revision |
| PAT-APR-02 | A modified input after approval ⇒ approval `superseded`; execution refused |
| PAT-APR-03 | An agent cannot approve its own request; requester ≠ approver is enforced when policy says so |
| PAT-APR-04 | Escalation: an unanswered approval escalates per chain and surfaces in the web inbox; nothing is lost |
| PAT-APR-05 | Approval executes through a separate idempotent job; a crash between approval and execution leads to exactly one execution |
| PAT-CHN-01 | **Adapter conformance suite** passes for web inbox, Slack, Discord, Telegram (delivery idempotency, signature verification, linking, callback replay rejection) |
| PAT-CHN-02 | An unknown/unlinked channel sender can neither approve nor trigger anything; its text never reaches a model as instruction |
| PAT-CHN-03 | High-risk approval via channel requires web step-up; the channel button alone is rejected |
| PAT-CHN-04 | Digest mode batches N intents into one message with deep links; quiet hours delay non-critical intents |

---

## 11. Operations: business case and inbox ✅ D-30

### 11.1 Why

Automation tools show **runs per workflow.** A company thinks in **business cases:** "order #1234" — with the shop order, the HQ sales order, the stock reservation, the purchase of a missing battery, the supplier mail, the customer mail, the employee task and alran's research. The Platform makes such a case visible, explainable and steerable, so that daily life is *"it runs; you only see what needs attention."* (P10)

### 11.2 `business_case`

(English in code; UI label from i18n — "Vorgang" in German. Namespaced `case_type` avoids collision with LD3's `RevalidationCase` and Privacy cases, which are *domain* objects the case can link to.)

| Field | Meaning |
|---|---|
| `id`, `company_id`, `case_type` | type registered by a module manifest (`hq.order_fulfilment`, `hq.replenishment`, `hq.return`, `ld3.publication`, …) |
| `state` | `running` · `waiting_human` · `waiting_external` · `failed` · `compensated` · `done` · `cancelled` |
| `owner`, `due_at`, `priority` | accountable person/role; SLA aging |
| `entity_refs[]` | `{ system, entity_type, id, external_ref? }` across native and bound systems |
| `timeline[]` | flow steps, actions, approvals, messages, signals — derived from events/receipts |
| `receipts[]`, `approvals[]`, `flow_run_ids[]`, `mission_ids[]` | links, not copies |
| `cost` | aggregated credits/model cost |
| `parent_case_id`, `tags` | decomposition (e.g. replenishment child of order case) |

The case id is the **correlation root** for events, jobs, flow runs, missions and receipts belonging to it.

### 11.3 Inbox

One queue for four kinds of items:

| Kind | Source | Resolve by |
|---|---|---|
| `decision` | approvals, step-up requests, T3 proposals | approve / reject / change |
| `exception` | failed flow step, dead-letter, stuck case, reconciliation difference, connector error, budget stop | retry / skip / compensate (each guarded and audited) / reassign |
| `proposal` | alran suggestions, OOIE signals, staleness findings | accept → creates a real action (through the pipeline) / dismiss |
| `draft` | T1 outputs (quote draft, mail draft, product draft) | edit → submit → pipeline |

Capabilities: assign, snooze, aging/priority, bulk actions (→ job with receipt), digests by channel or mail, deep links, "why is this here" explanation. The web inbox is the **mandatory** Channel Port adapter and a core dashboard widget in HQ and LD3.

### 11.4 Explainability

`GET /cases/{id}/explain` returns the causal chain (event → flow step → action → receipt → external effect → verification) so "why was X not updated?" has an answer. Repair actions on a case (`retry`, `skip`, `compensate`) are themselves actions with policy, optional approval and receipts.

### 11.5 Dashboard — the morning view (VD-32)

Opening HQ shows, without configuration: new orders, revenue, open deliveries, critical stock, tasks due, automations executed, **failed processes, decisions waiting**, open approvals. Role and installed apps shape the view. 🟠 Role presets: owner/management, sales, warehouse/logistics, accounting — plus the inbox for everyone (Doc 1 Anhang B #9, open). Every number carries unit, period, comparison and an explanation; empty states say *why* they are empty (SAP lesson, §25.6).

### 11.6 Implementation

A new Platform service **Operations**, built on Flows/Jobs/Approvals/Audit and the event layer; HQ, LD3 and apps contribute case types, timeline projections and views through manifests. It owns no domain data.

### 11.7 Acceptance tests — operations

| ID | Test |
|---|---|
| PAT-OPS-01 | A shop order creates one case that links the HQ order, reservation, purchase, mails and task; the timeline is complete and ordered |
| PAT-OPS-02 | `explain` returns the causal chain for an injected failure (e.g. missed webhook) and names the failing step |
| PAT-OPS-03 | An exception item offers retry/skip/compensate; each repair is an action with receipt and, where configured, approval |
| PAT-OPS-04 | Inbox bulk action creates one job with a per-item receipt; partial failure is visible per item |
| PAT-OPS-05 | A case in `waiting_human` does not hold a worker (durable wait) and survives a restart |
| PAT-OPS-06 | Case/inbox queries obey tenancy and permissions: a user sees only items they may act on |
| PAT-OPS-07 | The default dashboard renders useful content with demo data and no configuration; empty widgets state their reason |

---
## 12. Flows — the central automation engine

### 12.1 Role

Flows is the **generic, durable automation engine of the Platform** (PLT-W1-16). It is what turns "when a customer orders, do this and that" (VD-28) into configuration, in the spirit of n8n/Power Automate (inspiration only, via clean-room; D-25) — but as a durable runtime, not a collection of sleeping processes. **Flows is for the known; alran is for the unknown** (Doc 1 §1.2 #3). HQ, LD3 and apps contribute triggers, nodes and templates with domain semantics; they own no engine.

### 12.2 FlowSpec

A `FlowSpec` is **versioned and immutable**; editing creates a draft; activation pins one version; a running execution continues against the version it started with unless an explicit migration is defined.

| Node type | Purpose |
|---|---|
| `trigger` | domain event (outbox), schedule, inbound webhook (via Integrations), manual start, OOIE signal |
| `action` | invokes an **Action** through the full pipeline (§8) — Flows never bypasses it |
| `condition` / `branch` / `parallel` / `join` | control flow; bounded loops only |
| `wait` | for a time, an event or a human; **a wait is data plus a scheduler wake-up**, never a sleeping thread |
| `approval` | suspends durably on an Approval (§10); no worker is held |
| `mission` | delegates an open-ended step to alran with a result contract and budget (§16); the flow resumes on completion |
| `notify` | notification intent through the Channel Port |
| `transform` | pure, side-effect-free mapping |
| `error_handler` / `compensate` | failure and compensation edges |

Every node declares: input/output schema, required permission, side effects, idempotency, retry safety, cost class, timeout, data classes and observability fields. A visual success path is insufficient: **pause, retry, partial failure, compensation, replay and deletion are defined for every flow.**

### 12.3 Execution semantics

- Each run stores: current step, input/output references, wait condition and deadline, retry policy, approvals, provider calls, compensation state, trace and cost context. Restart of worker or host resumes from durable state.
- **Retry:** bounded exponential backoff with jitter, only for `retryable` error classes; side-effecting nodes require idempotency keys.
- **Compensation (saga):** a failure after side-effecting steps follows the node's `compensate` edge in reverse order, or the flow's `partial_failure_policy ∈ {stop, continue, compensate}`. Compensation is an Action (`compensation_action`), so it also has policy, receipts and, if configured, approval. *(Closes R-11 / W-17; the previous plan explicitly lacked this.)*
- **Replay:** from a chosen step, with a dry-run option, audited; replay never repeats external effects whose receipts exist (receipt lookup, §8.9).
- **Concurrency keys and rate limits** per flow and per target system; **budget** per run (credits reservation, §20).
- **`unknown_external_result`** inside a flow routes to a reconciliation node or an inbox exception — never to "success".

### 12.4 Flows and autonomy

A flow executes actions under a **flow principal** whose grants come from the activating user's rights ∩ the company policy. The autonomy level of an activated flow is chosen at activation and clamped by the same ceiling (§9). A flow with external effects at T3 pauses at each approval node; at T4 it runs within the grant limits. Activation of a flow that contains external effects is itself an `internal_change` that requires the activating user's rights (and approval where the company requires it).

### 12.5 Editor and templates

- **Flow editor** (family `FB-01`): graph editor, node palette fed by contributions, drafts/versions/activate, test run in dry-run mode, run timeline with per-step receipts. **"alran drafts, a human reviews":** alran may generate a FlowSpec draft; it can never activate one above its autonomy.
- **Templates and recipes** are immutable versions with variables and compatibility; they may not embed secrets or fixed tenant IDs. A recipe returns a **plan before mutation**.
- **Reference templates** shipped with HQ: *lead-to-cash* and the *iPhone order process* (order → stock check → assemble from parts → missing-part replenishment → supplier order with approval or auto-limit → delay mails → assembly task → human escalation → used-device search with purchase only after approval). They double as acceptance fixtures for M1–M6 (§29.3).

### 12.6 What moves out of HQ and LD3

HQ's own lead-to-cash state machine (`HQ-W1-15`) and LD3's automation (`LD3-W1-17`) are rebuilt **on** Flows (W-19). HQ keeps the domain semantics (what a valid order transition is) and publishes triggers/nodes; the engine is shared.

### 12.7 Acceptance tests — Flows

| ID | Test |
|---|---|
| PAT-FLW-01 | `kill -9` of the worker mid-run: the run resumes from durable state; every side-effecting node executes exactly once (receipt lookup) |
| PAT-FLW-02 | A wait of N days survives deploys and restarts and wakes on time (± scheduler tolerance); no worker is blocked meanwhile |
| PAT-FLW-03 | Failure after two side-effecting steps triggers compensation in reverse order; compensation actions have receipts |
| PAT-FLW-04 | A running flow stays on its pinned version when a new version is activated |
| PAT-FLW-05 | A flow node cannot bypass the Action pipeline: direct DB/connector writes by node code are rejected by the node contract gate |
| PAT-FLW-06 | An approval node pauses durably; reject → defined branch; expiry → defined branch |
| PAT-FLW-07 | The iPhone reference flow runs end-to-end against sandbox systems with all three outcome branches (in stock / assemble / replenish) and the human-escalation branch |
| PAT-FLW-08 | A flow budget cap stops the run with `budget_exhausted` and an inbox exception |

---

## 13. Integrations and provider binding ✅ D-02

### 13.1 Division of labour

| Layer | Owns |
|---|---|
| **Platform Integrations engine** | connections (OAuth/API credentials via `SecretRef`), sync scheduling (full/delta), inbound webhook ingress (signature check, replay protection, dedupe, DLQ), outbound call mechanics (idempotency, backoff, circuit breaker, rate-limit budgets), mapping runtime, reconciliation, health/degraded state, connector registry, binding model and router |
| **App / connector / HQ domain** | the *domain mapping* — how this external system's objects and actions map to canonical ones; nothing else |

HQ, LD3 and apps MUST NOT ship their own webhook receivers, sync loops, API-key stores or credential UIs (R-19, R-51). Where the pack currently does (`HQ-W1-33/34/35`, `APP-W1-02/03/10`), plans are corrected to consume the engine.

### 13.2 Binding — how Ottili adapts (P1)

A **binding** exists per *capability/entity type* and *company*:

```ts
interface Binding {
  company_id: string;
  entity_type: string;                 // organization | contact | product | stock | order | invoice | mail | calendar | …
  mode: "native" | "mirror" | "federated" | "migration";
  provider: string;                    // "ottili" | "shopify" | "odoo" | "cobra" | "m365" | …
  connection_id?: string;
  system_of_record: Record<FieldGroup, "ottili" | "provider">;
  conflict_policy: Record<FieldGroup, "provider" | "ottili" | "newest" | "manual">;
  maturity: 0 | 1 | 2 | 3;             // connector maturity for this entity (§13.5)
  cutover?: { phase: "import" | "parallel" | "freeze" | "switched"; plan_ref: string };
  status: "active" | "degraded" | "paused" | "error";
}
```

| Mode | Meaning | Example | System of record | Write path |
|---|---|---|---|---|
| **Native** | Ottili core/app leads | HQ CRM | Ottili | direct |
| **Mirror** | external system leads; Ottili keeps a *readable projection* for search, 360° view, flows, AI | cobra CRM, Odoo | external | action → binding router → connector → external; projection follows via sync/webhook |
| **Federated** | no copy; live query on demand | Outlook mail, Teams, SharePoint | external | live call via connector/MCP |
| **Migration** | binding moves Mirror → Native with cutover | cobra → HQ CRM | switches | import → parallel run → freeze → switch |

**Binding router (AR-14):** an action such as `crm.customer.create` resolves to the Ottili handler (native) or the connector (mirror/federated) — callers (UI, Flows, alran, MCP) cannot tell the difference. The system of record is decided **per entity and per field group** (e.g. product: master data → ERP; texts → LD3; prices → per channel rules; stock ← stock ledger).

### 13.3 Canonical business graph and `external_refs[]`

Canonical objects: party (organization/contact), product/variant/bill of materials, quote/price, order, stock/location/movement, invoice/payment, shipment, task, document, message, content, campaign. Every record that mirrors or links to an external object carries:

```ts
external_refs: Array<{ system: string; id: string; version?: string /* ETag/rev */; last_synced_at: string; hash: string }>
```

Used for mapping, duplicate detection and conflict handling (`hash` + `version` detect divergence). Graph *views* are read projections; **writes are always canonical actions.**

### 13.4 Conflict policy

Per field group: `provider` (external wins) · `ottili` (Ottili wins) · `newest` (by authoritative timestamps) · `manual` (creates an inbox exception with both versions). Silent overwrite is forbidden; every conflict resolution is audited.

### 13.5 Connector capability declaration and maturity

Every connector/app declares (in its manifest, `connector` contribution): authentication scheme, supported entities and actions, delta capability, webhooks, rate limits, health check, mapping to canonical objects, data classes — and a **maturity level per entity**:

| Level | Capability |
|---|---|
| **0** | read only |
| **1** | read + write |
| **2** | delta sync / webhooks |
| **3** | reconciliation + compensation |

A missing capability degrades cleanly: *"action not possible with this provider → task for a human"* (`unsupported_by_provider`, §8.4). Contract tests are run per declared maturity level (`FB-28`).

### 13.6 Sync, webhooks and "effectively once"

Truly exactly-once delivery across systems is not achievable. The architecture delivers **effectively once** = at-least-once delivery + idempotency keys + deduplication + reconciliation:

| Direction | Key | Mechanism |
|---|---|---|
| Inbound event | `(company_id, binding, entity, external_event_id)` | signature verified, raw payload hash stored, deduped, written to the outbox, processed idempotently; failures → DLQ with operator replay; **webhook ordering is not trusted** |
| Outbound call | `(action, input_digest, resource_revision)` | idempotency key sent to the provider where supported; otherwise read-before-write |
| Unclear outcome | – | state `unknown_external_result` → reconciliation job or human (LD3 already has this concept, §34.6 of the LD3 blueprint) |
| Drift | – | periodic **reconciliation** compares provider snapshot to the internal ledger; differences become inbox exceptions (case), never silent overwrite |
| Provider outage | – | binding `degraded`; reads show staleness; **never a fabricated success state** |

Stock example (Doc 2 §2.4 #3): channel orders reserve idempotently by `(channel, order, line)`; the stock ledger (append-only movements in milli-units; physical · reserved · available) pushes allocations with safety buffers to channels idempotently; reconciliation against channel stock turns divergences into cases. "No oversell" is **not promised** — the goal is avoidance (reservation, buffer), detection (reconciliation) and a defined handling (back-order, cancel, alternative). 🟡

### 13.7 The connection ladder (P5)

The lowest *reliable* rung wins. Higher rungs are used when lower ones do not exist.

| # | Rung | When | Governance |
|---|---|---|---|
| 1 | **Native** | an Ottili app covers it | full action architecture |
| 2 | **Official API / webhooks** | the system has a dependable API | Integrations engine: connection, vault refs, sync, signed/idempotent webhooks, DLQ (Shopify, Stripe, eBay API, AliExpress dropshipping API 🟡 D11, Microsoft Graph) |
| 3 | **External MCP** | vendor/community offers MCP | registered in the **MCP registry of the AI Gateway** (§15.8) |
| 4 | **Ottili adapter MCP** | MCP absent or unsafe | own wrapper over rung 2, same registry (e.g. Odoo: no confirmed official MCP, D14) |
| 5 | **Skill** | lightweight capability, no sync | `SKILL.md` + few tools bound to actions (§7.9) |
| 6 | **Browser / CUA** | site without a usable API — a **principle**, not a one-off | domain policy, CAPTCHA policy, audit with evidence (§17); **never bulk sync, never a replacement for a system of record** |

### 13.8 Generic connector mechanism — "Zapier level" ✅ D-01 / BP-6

Goal: connect as much as possible, *mechanism-driven rather than hand-built one by one*:

- **REST/OpenAPI importer** generates a connector manifest skeleton (entities, actions, auth, pagination, rate limits); a developer or alran completes the mapping; contract tests run per maturity.
- **Webhook sources** with signature schemes as configuration.
- **MCP servers as connectors** (HTTP/SSE only; allow-listed tools; risk class ↔ effect class mapping).
- **Browser skills** as policy-gated fallback.
- **Coexistence:** Ottili exposes events and actions via API, webhooks and Ottili MCP so customers can use n8n/Make/Zapier alongside — P1 means no forced replacement. 🟠
- **Build-vs-use (AR-28):** before building any connector framework component, check existing open standards and OSS (OpenAPI tooling, MCP SDKs) for license, maturity, multi-tenancy and operating cost.

### 13.9 Import, migration, export

- **Import profiles** (CSV/Excel first): mapping, dry-run, validation report, duplicate detection via `external_refs`/natural keys, idempotent re-import, row-level errors to an exception list.
- **Migration mode** procedure: import → parallel run with reconciliation gates → freeze window → switch (`cutover.phase`) → decommission the mirror. A rollback path exists until `switched`.
- **Export:** a **full-company export** in machine-readable form (JSON/NDJSON + CSV, versioned schemas, files with a manifest) through an open API. The EU Data Act gives switching/portability rights (in force since 12.09.2025; switching charges phased out from 12.01.2027 🟢 D5) — hint, not legal advice. Per-domain exports (DATEV, evidence bundles) are views on the same mechanism.

### 13.10 On-premise systems — Connector Agent 🟠 (architecture contract only in the beta)

For systems with no inbound access (e.g. cobra CRM runs through the "Cobra CXM Web Connect" Windows service at the customer, 🟡 D13): an **Ottili Connector Agent** — outbound-only connection (mTLS), signed releases, bound to one company, capability allow-list, versioned protocol, no inbound ports. Implementation is family `FS-03`, after a design partner exists.

### 13.11 First "bring your own stack" proof 🔴 D-26

Willi wants *as much as possible* connected. Default proposal until decided: **Microsoft 365 mail + calendar, federated** via Microsoft Graph as the first BYO proof (family `FB-19`); Odoo/cobra afterwards, driven by test-customer need; import starts with CSV/Excel.

### 13.12 Customer types the architecture must serve

| Type | Path | Test |
|---|---|---|
| **Start from zero** | native apps (shop, stock, CRM) | complete journey with demo data |
| **Existing stack** | bindings (mirror/federated) | an order flows through bound CRM + mail without Ottili being SoR |
| **Switching** | migration mode | cutover rehearsal with reconciliation proof |

Flows, alran and the inbox see no difference between the three (AR-14).

### 13.13 Acceptance tests — bindings and integrations

| ID | Test |
|---|---|
| PAT-BND-01 | The same action (`crm.customer.create`) succeeds against a native binding and a mirror binding (sandbox external CRM); the caller sees an identical contract |
| PAT-BND-02 | `external_refs[]` stay consistent across create/update/duplicate-detection round trips; hash divergence is detected |
| PAT-BND-03 | Conflict policy matrix: provider/ottili/newest/manual each behaves as declared; `manual` produces an inbox exception with both versions |
| PAT-BND-04 | A connector lacking a capability degrades to a human task (`unsupported_by_provider`) instead of erroring |
| PAT-BND-05 | Cutover rehearsal: import → parallel → freeze → switch with zero unreconciled differences; rollback before `switched` works |
| PAT-INT-01 | Duplicate and out-of-order webhook deliveries produce exactly one effect |
| PAT-INT-02 | Timeout after sending an outbound write ⇒ `unknown_external_result`; reconciliation resolves it without a second write |
| PAT-INT-03 | Provider outage ⇒ binding `degraded`, staleness shown, no fabricated state, recovery drains the backlog idempotently |
| PAT-INT-04 | Reconciliation detects an injected stock deviation (1,069 vs 1,067) and creates a case with the likely cause |
| PAT-INT-05 | Full-company export validates against its versioned schema and re-imports into an empty company without loss (round trip) |
| PAT-INT-06 | No product/app contains a private webhook receiver, API-key store or sync loop (repo scan against the allow-list) |
| PAT-INT-07 | OpenAPI importer generates a working connector skeleton for a reference API; contract tests pass at declared maturity |

---

## 14. Ottili MCP — one per company ✅ D-29

### 14.1 Shape

One MCP server endpoint **per company**, so external clients (ChatGPT, Claude, other agents) and alran can drive HQ, LD3 and apps through the same typed surface (VD-36: "attach the Ottili MCP in Claude or ChatGPT and steer everything from there").

- **Transport:** HTTP-based MCP transport (streamable HTTP; SSE for legacy clients). `stdio` is not offered for managed use.
- **Authorization:** OAuth 2.1 with PKCE per the MCP authorization model; tokens are **bound to user and company** and audience-restricted to the MCP resource; token passthrough to downstream services is forbidden (confused-deputy defence).
- **Endpoint:** 🟠 `https://mcp.ottili.one/{company_slug}/mcp`; the company binding comes from the token, the path is for clarity and routing.

### 14.2 Surface

| Element | Rule |
|---|---|
| **Tools** | the exported actions (§8.7), filtered by `caller rights ∩ agent/client grants ∩ toolset`; namespaces `hq_*`, `ld3_*`, `app_<name>_*`; stable names |
| **Toolsets / profiles** | bundles such as "Sales (read)", "Purchasing with approval" limit the tool count per client (large tool lists degrade model performance); configured per client in the Ottili Console |
| **Resources** | read-only views: business-graph extracts, cases, inbox, product catalogue, documents (permission-filtered) |
| **Prompts** | skill-derived (§7.9), optional |
| **Notifications** | `tools/list_changed` on entitlement or toolset changes |

### 14.3 The MCP is a facade, not a second path

Every call enters the **Action pipeline** (§8.3): permissions, entitlements, autonomy, approvals, budgets, receipts. The consent screen lists the toolsets the client will receive. The company decides which toolsets are open **through grants and the autonomy ceiling** (D-11) — there is no hard-coded beta restriction. 🟠 Operating default: a newly registered external client receives **read + draft** toolsets only; widening is an explicit grant within the ceiling.

### 14.4 Security

- Tool results and resource contents are **untrusted data** (AR-06); injection fixtures (mail text, product titles, web content) are release gates.
- Per-client rate limits and cost budgets; client id appears in every receipt's actor chain.
- Revocation of a client is immediate; tokens are short-lived; refresh follows §5.3.
- Cross-tenant and confused-deputy fixtures run on every release (§6.9).

### 14.5 External MCP servers consumed by Ottili

Third-party MCP servers (e.g. community Odoo servers) are **registered in the AI Gateway's MCP registry** (§15.8) — never attached directly to agents. Registration states transport (HTTP/SSE only), allowed tool list, risk class ↔ effect class mapping, health policy, pinned version, egress allow-list and token vault references.

### 14.6 Acceptance tests — Ottili MCP

| ID | Test |
|---|---|
| PAT-MCP-01 | A client sees only tools within `rights ∩ grants ∩ toolset`; calling a hidden tool by name fails as unknown |
| PAT-MCP-02 | A write tool on an external-change action returns `approval_required` for a T3 client and creates an inbox decision |
| PAT-MCP-03 | A token for company A is useless against company B's endpoint, including path-swapping and token-audience confusion |
| PAT-MCP-04 | Injection fixtures through tool arguments and resource content never change authorization or trigger unlisted tools |
| PAT-MCP-05 | Revoking a client takes effect within the revocation SLA across running sessions |
| PAT-MCP-06 | New external clients default to read + draft; widening requires a grant and is audited |
| PAT-MCP-07 | `tools/list_changed` is emitted when an entitlement or toolset changes |

---
## 15. AI Gateway

### 15.1 Role

The AI Gateway is the **only door to models** (AR-12). HQ, LD3, apps, alran, Flows and GERMO-built features never import a provider SDK. The gateway owns: model catalogue and eligibility flags, data-class enforcement, routing and fallbacks, budget reservation and metering, the MCP registry for external tool servers, and provider data-use profiles. **alran API & Console** is the public face of the same machine (§15.10): the gateway is the engine, the alran console is a separate product that exposes keys, usage, budgets, routing and billing to developers and companies.

### 15.2 API surface

| Endpoint | Purpose | Notes |
|---|---|---|
| `POST /v1/responses` | **canonical** generation endpoint (Responses API shape, streaming, tool calls, structured output) | GERMO understands only the Responses API; Codex-class harnesses require it (🔴 verify `wire_api` against Codex source/release notes, Doc 1 §3.7) |
| `POST /v1/chat/completions` | compatibility shim translated to the canonical path | for clients that cannot speak Responses; feature-parity gaps are documented, not hidden |
| `POST /v1/embeddings` | embeddings | data class applies identically |
| `GET /v1/models` | models **eligible for the caller** (company, key scope, data class hint) | never lists dev-only models to customer keys |
| `POST /v1/usage/estimate` | pre-flight cost estimate / budget check | used by the Action pipeline preflight (§8.3) |
| Admin API | keys, budgets, routing policy, provider config, MCP registry | Ottili Console and alran console are clients |

Authentication: company-scoped API key, OAuth client token, or workload service JWT (§5.5). Every call carries `PlatformContext` (§4.5) plus `data_class`, `purpose`, optional `mission_id`/`action_id`/`business_case_id`. A request without `company_id` and `data_class` is rejected (AR-04, AR-13).

### 15.3 Model catalogue and flags

```ts
interface ModelEndpoint {
  id: string;                         // gateway-internal, e.g. "claude-sonnet-5-5@openrouter-eu"
  logical_model: string;              // what callers may request, e.g. "claude-sonnet-5-5"
  provider: string;                   // openrouter | own-hosted | dev-pool | …
  region: "eu" | "eea_uk_ch" | "us" | "cn" | "global" | "unknown";
  retains_data: boolean;              // false only with a verified ZDR route
  trains_on_data: boolean;
  dpa_status: "signed" | "available" | "none";
  distillation_allowed: boolean;      // may outputs be used to train other models?
  resale_allowed: boolean;            // may the model be offered to third parties via alran API?
  customer_eligible: boolean;         // dev models: false
  max_data_class: DataClass;          // highest class this endpoint may receive
  capabilities: { tools: boolean; vision: boolean; structured_output: boolean; context_tokens: number };
  cost: { input_per_mtok: number; output_per_mtok: number; currency: "USD" }; // from live provider data; never typed by hand
  terms_ref: string;                  // provider terms version reviewed
  status: "active" | "degraded" | "disabled";
}
```

Prices come from the provider's live catalogue and are refreshed on a schedule; a price typed into a document is not a source (Doc 1 §3.13: values pasted from a provider page are verified before use). Terms are reviewed per provider and recorded in `terms_ref`; a model whose terms forbid the intended use gets the corresponding flag set to `false` before it is enabled.

### 15.4 Data classes and eligibility ✅ D-33 🟠

Every request carries one data class; classification and redaction happen **before** the provider transfer.

| Class | Examples | Eligible endpoints (default policy) |
|---|---|---|
| `public` | LD3 research on public sources, public catalogue data | any endpoint whose terms allow the use — including cheaper or China-hosted ones |
| `internal` | notes without personal data, purchase prices, supplier terms | EU region, `trains_on_data=false`, `dpa_status=signed` |
| `personal` | customers, employees, orders with names/addresses | **only** EU region + ZDR (`retains_data=false`) + `trains_on_data=false` + DPA signed; default: Claude Sonnet 5.5 via `eu.openrouter.ai` |
| `secret` | credentials, contracts, bank/finance data | credentials never enter a prompt (vault refs, AR-11); contracts and finance data only EU-ZDR endpoints |

Rules:

1. **Filter by eligibility first, choose by cost second.** The eligible set is computed from `data_class`, company policy flags, endpoint flags and `max_data_class`; routing optimises cost/latency only inside it.
2. **Dev models are never customer-eligible** (`customer_eligible=false`); they live in a separate provider namespace with separate credentials and never see customer data (§15.11).
3. **Presidio runs before every external transfer** as an additional layer (defence in depth), **not** as the legal basis. Detection is never complete and pseudonymisation is not anonymisation while the link is recoverable; context alone can identify.
4. **"Presidio-cleaned → cheaper China-hosted model" is off by default** and switchable per company only after a small legal review (D-28); the gateway enforces the switch, the UI labels the risk. Own models hosted in China (e.g. Vale 1.1) are for `public` tasks only — for customer data that would be a third-country transfer without an adequacy decision.
5. **Classification source of truth:** the caller declares the class; the gateway **raises** (never lowers) it when detectors find personal data in a `public`/`internal` request, and then re-routes or rejects. A caller can request a stricter class than needed, never a looser one than policy permits for its action (`ActionDefinition.effects.reads/writes`).
6. Company-level policy flags: `allow_cheap_models_public` (default on), `allow_presidio_cn_routing` (default off), `allowed_regions`, `allowed_providers`.

### 15.5 Provider data-use profiles

A **profile** describes what a provider does with data on a route and is referenced by `ActionDefinition.provider_data_use_profile` (§8.2) and by endpoints.

| Field | Meaning |
|---|---|
| `retention` | none (ZDR) · short-term abuse logging · long-term |
| `training_use` | never · opt-out · default-on |
| `regions` | where prompts/outputs are processed |
| `out_of_region_data` | what may leave the region (OpenRouter EU domain: account, billing, authentication data, security logs, abuse metadata — prompts and answers stay in-region 🟢 D18) |
| `subprocessors` | listed in the subprocessor register (§23.5) |
| `dpa` | status, clauses (SCC), **EU-only addendum chosen in writing** (OpenRouter Exhibit A is effective only if chosen — task for G2) |
| `not_regional` | features that break regional guarantees: global/cross-region deployments, auto-router, batch API; on the EU domain no web-search engine and no `web_fetch` |

The default customer route is `eu.openrouter.ai` with `zdr: true` and `data_collection: deny`, which **fails closed** when no in-region endpoint exists — it never falls back silently outside the region. 🔴 Open until checked against the live `/api/v1/models` of the EU domain: whether Sonnet 5.5 (Vertex EU) is listed as in-region **and** ZDR-capable.

### 15.6 Routing and fallbacks

- Routing policy per `(company, purpose)`: ordered list of logical models, cost ceiling, latency target, structured-output requirement.
- **Fallback stays inside the eligible set.** A fallback that would violate region, ZDR or class is skipped; when the set is empty the call fails with `no_eligible_model` — an inbox exception, never a silent downgrade.
- Features that break regional guarantees (global profiles, auto-router, batch) are disabled for classes `personal`/`secret`.
- Circuit breakers per endpoint; degraded status propagates to the Console; retries are bounded and idempotent by `request_id`.

### 15.7 Budgets, metering and cost

- **Reserve → call → settle.** The Action pipeline reserves credits at preflight (§8.3); the gateway settles actual usage; leftover is released. A request that would exceed the reservation, the mission budget or the company cap is rejected before the provider is called (AR-26).
- **Free beta = hard per-company credit caps** (G6, §20): inference cost of test companies is borne by Ottili, so the caps are not advisory.
- Usage records carry `company_id`, `user_id`/`agent_id`, `mission_id`, `action_id`, `model`, tokens in/out/cached, cost, data class, region, latency, outcome.
- Cost classes on actions (`free | metered | expensive`) drive reservation size and approval thresholds (§9.4).

### 15.8 MCP registry — external tool servers

External MCP servers are **never attached directly to agents**. They are registered here.

| Field | Rule |
|---|---|
| Transport | HTTP/SSE only; **stdio is forbidden in managed mode** |
| Identity | `server_id`, vendor, pinned version/digest, source, license |
| Tools | **allow-listed** tool names; schemas pinned; changes require re-approval |
| Risk | per tool: risk class ↔ effect class (§8.2); anything not classified is `critical` and disabled |
| Egress | allowed hosts for the server's outbound calls; secrets only via vault refs |
| Health | probe, latency, error rate; auto-disable on repeated failure |
| Scope | per company enablement; per agent grants (§16.2) |
| Binding | an MCP tool becomes an **Action** (own namespace) before any agent can use it, so policy/approval/receipt apply unchanged |

Tool descriptions and tool outputs from registered servers are untrusted data (AR-06).

### 15.9 Provider ports

`ProviderPort` is the adapter interface (`generate`, `embed`, `list_models`, `health`, `price_catalogue`). Implementations: OpenRouter (first, EU domain), own-hosted models (Pico/Vale/Cairn/Spire as "just another provider"), a **dev pool** (free development inference until year end, customer-ineligible). Replacing a provider is configuration plus contract tests; no caller changes.

### 15.10 alran API & Console — the public face ✅ D-04

A separate product with its own console, built on the gateway: model catalogue, keys, usage, budgets, routing, billing. Because third parties would receive model access, the **`resale_allowed` flag is a hard gate**: until the provider-terms question is resolved (Anthropic Commercial Terms D.4 forbid building competing products, training competing models, or reselling the services unless approved — Doc 1 §3.13, 🔴 interpretation open, D-28), alran API & Console offers **only own models and models with an explicit resale permission**. The same pattern applies to every other provider: read terms, set flags, then enable. Hint, not legal advice.

### 15.11 Development versus customer inference

| | Development | Customer |
|---|---|---|
| Models | free development model (large MoE, free until year end; afterwards paid) | Sonnet 5.5 EU-ZDR default; others per flags |
| Data | development and test data only | customer data per class |
| Credentials | separate provider account/keys, separate namespace | separate |
| Enforcement | `customer_eligible=false`; gateway rejects any customer-context request | normal |

Test **PAT-GWY-03** proves the separation. Because free development inference ends with the year, the gateway records development-model usage so the cost after year end is a measured number, not a guess.

### 15.12 Content logging and evaluation

By default the gateway stores **metadata and digests**, not prompt/response bodies. Content capture is opt-in per company and purpose (debugging, evaluation) with retention and class limits; captured content is a tenant-owned data class subject to deletion (§19.9). OpenTelemetry GenAI-style attributes feed traces (§24.5). Evaluation sets (golden missions M1–M6, injection fixtures) run through the same gateway with a `purpose=eval` tag.

### 15.13 Acceptance tests — AI Gateway

| ID | Test |
|---|---|
| PAT-GWY-01 | A `personal` request is routed only to EU+ZDR+no-training+DPA endpoints; when none is available it fails with `no_eligible_model` (no fallback outside the region) |
| PAT-GWY-02 | A `public` request may use the cheaper eligible endpoint; the same request with a detected email address is raised to `personal` and re-routed |
| PAT-GWY-03 | A customer-context request to a dev-pool model is rejected; dev traffic never carries customer data (traffic fixture) |
| PAT-GWY-04 | Budget reservation: a call exceeding the reservation is rejected before the provider is contacted; settlement matches provider usage within tolerance |
| PAT-GWY-05 | Direct provider SDK imports outside the gateway are detected by a repository scan (allow-list) |
| PAT-GWY-06 | `/v1/responses` conformance suite passes (streaming, tool calls, structured output); the chat-completions shim documents and tests its gaps |
| PAT-GWY-07 | An MCP tool outside the allow-list or with an unclassified risk class is not callable; a tool-schema change disables it until re-approved |
| PAT-GWY-08 | `allow_presidio_cn_routing=false` blocks routing to a CN-region endpoint for `internal`/`personal` data; the flag change is audited |
| PAT-GWY-09 | An endpoint with `resale_allowed=false` is absent from alran API model listings and rejects third-party keys |
| PAT-GWY-10 | Provider outage: breaker opens, eligible fallback is used, ineligible fallback is skipped, usage is attributed correctly |

---

## 16. Agent governance

### 16.1 Boundary

The **alran Runtime** is a thin adapter around a harness (DeerFlow for alran AI, Codex for alran Code). Ottili builds what neither harness has: tenant separation, authentication, a sandbox per company/mission, inbound events, mission persistence, budgets, approvals, receipts, audit (Doc 1 §1.4 #1). The Platform's **Agent Governance** service owns four contracts: agent principal (§16.2), mission (§16.3), runtime adapter (§16.4) and context service (§16.5), plus the watcher (§16.6). The mission/run/checkpoint runtime of the former Rooke blueprint is **not** built (D-05).

### 16.2 Agent principal

```ts
interface AgentPrincipal {
  agent_id: string; company_id: string;
  kind: "alran_system" | "custom";          // "alran_system": the default company agent; custom agents are templates + skills
  owner_user_id: string;                    // accountable human
  status: "active" | "paused" | "revoked";
  grants: Grant[];                          // §8.6 — never wider than the owner's rights ∩ company policy
  budget: { credits_per_day?: number; credits_per_mission?: number; hard_cap: boolean };
  autonomy: { selected: AutonomyLevel };    // clamped by company ceiling (§9.2)
  allowed_skills: string[]; allowed_toolsets: string[];
  token_audience: "ottili:agent";           // separate from humans and service accounts (§5.5)
}
```

An agent can never raise its own rights, change policy, touch audit, backups or other tenants (guardrail 5, §9.6). Pausing or revoking an agent invalidates its tokens and halts its missions at the next step boundary (immediately for external effects through the kill switch).

### 16.3 Mission

A **mission** is the Platform's durable record of an agent task.

```ts
interface Mission {
  mission_id: string; company_id: string; agent_id: string;
  initiator: { type: "user" | "flow" | "signal" | "schedule" | "inbound_event"; ref: string };
  business_case_id?: string;
  goal: string;                             // natural language
  constraints: { max_credits: number; deadline?: string; allowed_toolsets: string[]; autonomy_override?: AutonomyLevel };
  result_contract: JsonSchema<unknown>;     // what "done" must look like; verified, not asserted
  state: "queued" | "running" | "waiting_human" | "waiting_external" | "succeeded" | "partial" | "failed" | "cancelled" | "budget_exhausted";
  steps: MissionStep[];                     // (step_id, input_digest, action_id?, receipt_ref?, status)
  checkpoint_ref?: string;                  // opaque harness checkpoint
  created_at: string; completed_at?: string;
}
```

- **Durable and resumable.** State lives in the Platform (PostgreSQL), not in the harness. After a crash the mission resumes from the last checkpoint; every step performs a **receipt lookup on `(mission_id, step_id, input_digest)`** before acting, so an already-executed action is never repeated (§8.9).
- **Started by** a user, a Flow `mission` node (§12.2), a signal (§18.7), a schedule, or an inbound event — inbound events are received by the Platform's webhook ingress (§13.6) and turned into missions, because DeerFlow offers none.
- **Budget:** credits are reserved per mission and per step; `budget_exhausted` is a defined terminal state with an inbox exception.
- **Result verification:** a mission is `succeeded` only if the result validates against `result_contract` and the underlying actions have verified receipts; otherwise `partial` or `failed`.
- **Cancellation:** cooperative at step boundaries; hard for external effects through the kill switch.
- **Human waits:** an approval or question moves the mission to `waiting_human` and releases the runtime slot.

### 16.4 Runtime adapter contract

```ts
interface HarnessAdapter {
  start(mission: Mission, ctx: AgentRunContext): RunHandle;
  resume(mission: Mission, checkpoint: Checkpoint): RunHandle;
  cancel(run: RunHandle, mode: "cooperative" | "hard"): void;
  events(run: RunHandle): AsyncIterable<RunEvent>;      // thinking summaries, tool calls, outputs — mapped to trace + inbox
  health(): AdapterHealth;
  version(): { harness: string; pinned: string; protocol: string };
}
```

The adapter must satisfy **AR-16**:

| Boundary | Rule |
|---|---|
| Tools | only through Ottili MCP / Actions (§14); the harness has no direct network path to HQ/LD3 databases or provider APIs |
| Models | only through the AI Gateway (§15); provider URL/token injected per run, short-lived |
| Missions, receipts, grants | in the Platform; the harness' own memory/state is a cache |
| Channels | the Channel Port (§10.3) — harness-native channels (DeerFlow Telegram/Slack/…) are **disabled** |
| Credentials | never inside the sandbox or prompt (AR-11) |
| Upgrades | pinned versions, upgrade window, SBOM entry; contract tests run before adoption; exit strategy written before first customer use |

**DeerFlow adapter (alran AI)** 🟢 D1/D8: authentication is *off* by default in DeerFlow → enable OIDC against Ottili Auth; the gateway is never publicly reachable; short-lived service tokens per mission; sandbox per mission/company (Docker/Kubernetes); `allowed-tools` is not a security boundary → enforcement in the action layer; no tenant-wide isolation is documented → isolation by deployment cut plus Platform scoping, with isolation tests as release gate; multi-worker only with PostgreSQL + Redis-stream bridge, channel state is process-local; sizing ≥ 8 vCPU / 16 GB per gateway (🔴 server capacity, D-20).

**Codex adapter (alran Code)** 🟢 D2/D9: the `codex app-server` (JSON-RPC over stdio; threads/turns, approvals, sandbox modes — described by OpenAI as experimental for product integrations) is hosted in sandboxes for cloud execution, with **contract tests against the protocol** for every version bump; model provider = AI Gateway endpoint via `model_providers.<id>` with token from `auth.command` (user-level config only); MCP to Ottili via `mcp_servers`; autonomy ↔ approval/sandbox mapping per §9.8; own models must be trained/evaluated on the *real* tool protocol (`apply_patch`, shell), not on the old "Rooke Tool Protocol v1" (🔴). alran Code runs as its own parallel track and needs from the Platform essentially login, AI Gateway and credits 🟡.

**Isolation before density (AR-17):** few companies per runtime instance (or a dedicated lightweight instance) until isolation tests prove pooling safe.

### 16.5 Context service

What an agent may see is **assembled by the Platform**, not fetched freely:

- **Context packs** — permission-filtered extracts of the business graph (party, order, stock, case timeline) produced via read actions under the caller's rights ∩ agent grants; each pack carries data class and provenance.
- **Retrieval** — tenant-scoped search/vector index (§19.6); every hit is re-authorised at read time.
- **Memory** — agent memory is stored in a Platform-owned, tenant-scoped, user-deletable store; no cross-company or cross-user leakage; harness-internal memory is disabled or mirrored into that store 🟠; memory entries carry data class and are part of company deletion (§19.9).
- Anything coming from the web, mail or tools is marked `untrusted` in the context (AR-06).

### 16.6 Watcher and perception

The **watcher** subscribes to events and OOIE signals (§18.7) and creates **proposals** in the inbox ("stock-out risk high → purchasing proposal"). A proposal becomes a mission only if the agent's autonomy and grants allow it; otherwise it waits as a T1 draft/decision. Watchers are rate-limited per company, have a cost cap, and can be paused by the kill switch.

### 16.7 alran in HQ/LD3 versus alran AI

One runtime layer, two shells (Doc 1 §2.3): the standalone alran AI web app and the panels in HQ/LD3 use the same governance services and adapters. **No hard dependency of HQ/LD3 on alran.ai:** if alran AI is down, panels keep working because they talk to the Platform's mission API and runtime, not to the alran.ai app. Test **PAT-AGT-08**.

### 16.8 Evaluation

The six reference missions (§29.3) are the golden evaluation set. Each runs against sandbox systems with real DB and UI, records success rate, policy violations, cost, steps and interventions; injection fixtures (mail text, product titles, web content, tool output) are release gates (AR-06).

### 16.9 Acceptance tests — agent governance

| ID | Test |
|---|---|
| PAT-AGT-01 | Agent grants are the intersection of owner rights and company policy; a grant request beyond the owner's rights is refused |
| PAT-AGT-02 | Killing the runtime mid-mission and resuming executes every side-effecting step exactly once (receipt lookup) |
| PAT-AGT-03 | A mission exceeding its budget ends `budget_exhausted` before further provider/action cost occurs |
| PAT-AGT-04 | A mission is `succeeded` only if the result validates against `result_contract` and the receipts verify; otherwise `partial`/`failed` |
| PAT-AGT-05 | Harness-native channels are disabled; an approval can only be answered through the Channel Port |
| PAT-AGT-06 | The sandbox has no credentials, no route to internal services except Ottili MCP and the Gateway; egress allow-list enforced |
| PAT-AGT-07 | Cross-tenant runtime isolation suite (two companies, shared host or pooled instance) finds no leakage of files, memory, sessions or logs |
| PAT-AGT-08 | With alran.ai stopped, the HQ/LD3 panels still run missions through the Platform runtime |
| PAT-AGT-09 | Pausing/revoking an agent invalidates tokens and halts missions at the next step boundary (immediately for external effects) |
| PAT-AGT-10 | Harness version bump: the adapter contract suite runs; a failing suite blocks promotion |
| PAT-AGT-11 | Memory: user deletion removes agent memory entries; company deletion removes all; no entry is retrievable across companies |

---

## 17. Browser / computer-use and CAPTCHA policy ✅ W18 🟠 D-07

### 17.1 Role

Browser/CUA is **rung 6 of the connection ladder** (§13.7): a tool of alran AI for sites with no usable API, as a *principle* (AliExpress and Kleinanzeigen were examples). Official APIs go first. It is a policy-gated fallback, **never bulk sync and never a replacement for a system of record**.

### 17.2 Architecture

- One **browser sandbox per mission** in the `agent` zone (§4.3): no credentials inside, egress by domain policy, resource limits, recorded session (screenshots/DOM excerpts as evidence).
- **Credential broker:** secrets live in the vault (`SecretRef`); the broker performs login or injects session state outside the model's view; sessions are reusable per company/domain.
- Page content is untrusted (AR-06). **Every commit-type step** (purchase, submit, publish, message send) is an `external_change` Action that passes policy, approval and receipt — the model cannot "click through".
- **Human takeover:** live view plus "take over" hands the browser to a user; the agent resumes after hand-back.

### 17.3 Domain policy

Per domain exactly one mode (company-level; Platform ships a blocklist):

| Mode | Behaviour |
|---|---|
| `blocked` | no access |
| `read_only` | navigate and read |
| `actions_with_approval` | commit steps need approval (T3) |
| `actions_autonomous` | commit steps within grant limits (T4), requires explicit admin setting |

Unknown domains: `read_only` (or ask). Start blocklist: Kleinanzeigen until legally clarified; purchase flows at eBay (eBay's terms update of Jan 2026 prohibit buy-for-me agents without human review, D4). Kleinanzeigen § 5 No. 1 prohibits crawlers/scrapers and circumventing access protection without written consent (D10). Hint, not legal advice. 🔴

### 17.4 CAPTCHA policy

Global company setting with per-domain override.

| Mode (UI label) | `captcha_mode` | Behaviour |
|---|---|---|
| Solve CAPTCHAs Automatically | `solve_automatically` | solves everywhere; requires explicit admin confirmation, daily/monthly limit and risk notice |
| Solve CAPTCHAs on Approved Domains | `solve_on_approved_domains` | **default**; solves only on admin-approved domains (own accounts/shops, partner portals) |
| Never Solve CAPTCHAs Automatically | `never_solve` | never; creates a human-takeover item in the inbox; for regulated customers |

- **Provider port** (2Captcha first): cost cap per day/month, circuit breaker, per-solution audit (domain, type, cost, result), subprocessor entry and DPA check (G2). 2Captcha's terms allow only "authorized and legal purposes" and put responsibility on the user (D12).
- Solving a CAPTCHA *circumvents* an access control; it is therefore not a standard capability on blocklisted domains and the policy UI says so.

### 17.5 Evidence and receipts

Each browser action records URL, step intent, screenshot/DOM excerpt hash and outcome; receipts reference the evidence; evidence has retention and data class like any file (§19.5).

### 17.6 Acceptance tests — browser

| ID | Test |
|---|---|
| PAT-BRW-01 | An unknown domain is read-only; a commit step there is rejected with a policy reason |
| PAT-BRW-02 | A purchase step on an `actions_with_approval` domain creates an approval; without it nothing is submitted |
| PAT-BRW-03 | Prompt injection embedded in a page cannot trigger a navigation to a blocked domain or a commit step |
| PAT-BRW-04 | The sandbox filesystem and process environment contain no secrets (secret scanner); login runs through the broker |
| PAT-BRW-05 | CAPTCHA modes: `never_solve` always escalates; `solve_on_approved_domains` solves only on approved domains; `solve_automatically` is impossible without recorded admin confirmation; caps and breaker stop solving when exceeded |
| PAT-BRW-06 | Every solved CAPTCHA has an audit entry with domain, type, cost and result |
| PAT-BRW-07 | Human takeover: hand-over and hand-back preserve session state; actions during takeover are attributed to the human |
| PAT-BRW-08 | The browser path cannot be used for bulk reads beyond the per-mission page budget |

---
## 18. Events, jobs, schedules and signals

### 18.1 One event layer (AR-22) 🟠 D-13

There is **one** event layer: the Platform outbox. One catalogue, one naming scheme, one product-identifier vocabulary. OOIE is a **consumer**, not a second transport; Redis Streams may be used inside OOIE internals only.

### 18.2 Transactional outbox (AR-07)

- An event is written **in the same database transaction** as the state change it describes. A relay publishes committed rows; consumers are idempotent by `event_id`.
- Delivery is at-least-once, ordered per aggregate key (`company_id`, `aggregate_id`) — not globally ordered. Consumers must not assume cross-aggregate order.
- Per-consumer cursor/checkpoint; poison events go to a dead-letter queue with operator replay (audited). Retention of the outbox and of consumed events is configurable; replay beyond retention uses the owning domain's re-emit action.

### 18.3 Envelope and catalogue

```ts
interface EventEnvelope<T> {
  event_id: string;               // UUIDv7
  type: string;                   // <namespace>.<entity>.<verb>.v<N>   e.g. one.hq.order.confirmed.v1
  company_id: string;             // mandatory for tenant events
  occurred_at: string;            // UTC, RFC 3339
  aggregate: { type: string; id: string; revision: number };
  actor: ActorChain;              // §4.6
  correlation: { request_id: string; business_case_id?: string; mission_id?: string; causation_id?: string };
  data_class: DataClass;
  schema_version: number;
  payload: T;                     // minimal; sensitive data by reference, not by value
}
```

- **Namespaces** follow the product identifiers (§2.2): `platform.*`, `one.hq.*`, `one.ld3.*`, `alran.*`, `app.<name>.*`.
- **Catalogue and schema registry:** every event type is registered with owner, JSON Schema, compatibility mode and example. CI rejects a breaking change without a new `v<N>`; consumers declare the versions they accept (consumer conformance, §26.6).
- **PII minimisation:** payloads carry IDs and facts needed by consumers; personal data are fetched by authorised read actions, which keeps deletion tractable (§19.9).

### 18.4 Subscriptions and replay

Consumers subscribe by type pattern and company scope. The Platform offers (a) in-process/internal subscriptions through the relay, (b) outbound customer webhooks (signed, retried, with a delivery log) for API customers, (c) replay by time range or cursor for a given consumer. Replay never re-triggers external effects whose receipts exist (§8.9).

### 18.5 Jobs and schedules (AR-08)

| Concept | Rule |
|---|---|
| **Durable job** | row in PostgreSQL with `company_id`, kind, payload digest, state, attempts, lease owner, lease expiry, fencing token, `run_after`, priority, concurrency key |
| **Lease + fencing** | a worker holds a time-bounded lease; every side effect carries the fencing token; a stale worker's write is rejected |
| **Retry** | exponential backoff with jitter; per-kind max attempts; permanent failures go to DLQ with an inbox exception |
| **Schedules** | cron-like and interval schedules stored per company; wake-ups create jobs; a missed window is handled by a declared policy (`run_once_late`, `skip`, `catch_up_bounded`) |
| **Concurrency** | per-company and per-kind caps; concurrency keys serialise work on one aggregate |
| **Cancellation** | cooperative; long jobs checkpoint |
| **202 + job** | synchronous API work is bounded; anything longer returns `202 Accepted` with a job resource (AR-25) |
| **Valkey** | only for caches, rate-limit counters and short-lived locks — **no business-critical state** |

### 18.6 Time

Storage in UTC; the company has a time zone (default `Europe/Berlin` for DACH) used for display, schedules and business-day logic; DST transitions are tested for schedules and waits (§12.7).

### 18.7 Signals — OOIE as a consumer 🟢 BP-OOIE

OOIE (Ottili Operational Intelligence Engine) stays a **Platform product document**, not a Research topic. Its binding line: **event → feature → prediction → anomaly → signal → delivery → feedback**, no LLM in the core, and a **4-week shadow pilot** before customer visibility.

- **Input:** events from the outbox (read-only consumer); no direct database access to domain schemas.
- **Output:** `signal` records (type, severity, entity refs, explanation, evidence, suggested action id) delivered to (a) the operations inbox as *proposals* (§11.3) and (b) alran's watcher as *perception* (§16.6). **A signal never executes anything**; any reaction is an Action through the pipeline.
- **Feedback:** accept/dismiss/act decisions flow back as events to evaluate signal quality.
- **Examples at beta:** stock-out risk, stock deviation channel vs. ledger, supplier delay, order stuck in a state, unusual refund rate.
- **Shadow mode:** signals are computed and logged but not shown to customers until the pilot's precision/recall thresholds are met 🟠 (thresholds set after the first measurement).

### 18.8 Acceptance tests — events and jobs

| ID | Test |
|---|---|
| PAT-EVT-01 | A rolled-back transaction emits no event; a committed one emits exactly one outbox row |
| PAT-EVT-02 | A consumer crash and restart processes each event effectively once (idempotent by `event_id`) |
| PAT-EVT-03 | Registering an event type without schema/owner fails CI; a breaking schema change without a new version fails CI |
| PAT-EVT-04 | A poison event lands in the DLQ with company scope; replay by an operator is audited |
| PAT-EVT-05 | Lease expiry: a stalled worker's late write is rejected by the fencing token |
| PAT-EVT-06 | Cross-tenant: a consumer scoped to company A never receives company B events (fixture) |
| PAT-EVT-07 | A scheduled job around a DST change fires at the intended local time |
| PAT-EVT-08 | OOIE signals produce inbox proposals but never call actions; shadow mode hides them from customers |

---

## 19. Data, files, search and lifecycle

### 19.1 Stores and ownership

| Store | Role | Rule |
|---|---|---|
| **PostgreSQL** | source of truth for all state | one cluster for the beta (D-20), logical schemas per owner; `company_id` on every tenant row; RLS adoption per §6.5 |
| **Object storage** (S3-compatible) | file bodies, exports, evidence, backups | tenant-prefixed keys; private by default |
| **Valkey** | cache, rate limits, ephemeral locks | tenant-namespaced keys; loss of Valkey loses no business fact (AR-08) |
| **Search index** | derived, rebuildable | tenant-filtered at query *and* re-authorised at read (§6.6) |
| **Vector index** | derived embeddings | same tenant and permission rules as search |

Derived stores are always rebuildable from PostgreSQL + object storage; backups prioritise the truth stores.

### 19.2 Schema ownership and migrations

- Each module owns its schema; **no cross-schema writes**; reads across modules go through contracts (read actions, views owned by the producer, events).
- Migrations: forward-only, **expand → migrate → contract**, each with a rollback plan or an explicit "no rollback" justification; verified on a restored copy of production-shaped data before release. R14 found 142 of 432 migrations refused in LD3 — migration health is a CI gate (G3/G4).
- Seed/demo data are separate from migrations and tagged as demo (used for the SAP-lesson "try it with demo data", §25.6).

### 19.3 Data classification and catalogue

Every column or field that holds personal, secret or financial data is tagged in a data catalogue (class, purpose, retention, legal basis note, erasure behaviour). The catalogue feeds: gateway data classes (§15.4), export, deletion saga (§19.9), log redaction (§24.5), the record of processing activities (§23.4).

### 19.4 Conventions

- **Identifiers:** UUIDv7 (time-ordered) for rows and events; human-readable numbers (invoice, order) are **server-generated, gap-aware sequences** per company (R14: the caller must never supply invoice numbers).
- **Money:** integer minor units + ISO 4217 currency, never floats; tax computed server-side.
- **Quantities:** integer milli-units for stock and measures (avoid float drift).
- **Timestamps:** `timestamptz` UTC; business dates carry the company time zone.
- **Text:** UTF-8, normalised; i18n keys for user-visible strings (AR-24).
- **Optimistic concurrency:** every mutable aggregate has `revision`; updates require `If-Match` or action-level precondition.

### 19.5 Files

- **Metadata in PostgreSQL** (`file_id`, `company_id`, owner module, name, MIME, size, hash, data class, retention, legal hold, scan status, created_by); **bytes in object storage**.
- **Upload flow:** pre-signed upload to a quarantine prefix → antivirus/content scan → type sniffing (not trusting client MIME) → promotion; size and type limits per company plan.
- **Download:** short-lived signed URLs after a permission check; no public buckets; download events are auditable.
- **Versions and dedup** by content hash; thumbnails and previews are derived artifacts.
- **Evidence files** (browser screenshots, receipts' attachments) use the same service with retention classes.
- **Documents of apps** (office documents, attachments in HQ) are files with a domain binding; ownership and permissions follow the owning aggregate.

### 19.6 Search

- **Global search** across HQ, LD3 and apps is one Platform service; products **contribute index definitions** (searchable fields, facets, permission model) via the registry (`search_contribution`, §7.3); they do not operate their own search clusters (R-19).
- Query path: tenant filter → permission-aware filtering (document-level ACL tokens or post-filter with re-authorisation) → ranking. A result is never shown without a successful read-permission check.
- **Index freshness** via outbox events; a rebuild job exists per index; PostgreSQL full-text is the beta default, a dedicated engine is introduced only when measurements demand it (AR-25: measured bottlenecks before added technology). 🟠
- **Semantic search** (vectors) is optional and obeys the same tenancy and class rules; embeddings of personal data use only eligible endpoints (§15.4).

### 19.7 Caching

Cache keys include `company_id` (and, for permission-dependent values, the policy revision); a cache miss path is always correct; no cache stores secrets; invalidation by events. A cross-tenant cache fixture is part of the isolation suite (§6.9).

### 19.8 Analytics and reporting

Operational reporting runs on read replicas or derived tables owned by the producing module; every number in a dashboard has unit, period, comparison and an explanation (SAP lesson, §25.6). Cross-company analytics for Ottili itself (product metrics) uses aggregated, de-identified data with a documented legal basis — never raw tenant data (§23.4).

### 19.9 Lifecycle — retention, deletion, export, legal hold

| Topic | Architecture |
|---|---|
| **Retention** | per data class and legal duty (e.g. bookkeeping records, invoices — durations configured as `UNVERIFIED` until a tax adviser confirms, §23.6); retention is evaluated by a job, not by ad-hoc scripts |
| **Soft delete / trash** | user deletions first move to a recoverable trash (guardrail 2, §9.6); purge after a configured period |
| **Company deletion saga** | `deletion_pending → deleted`: primary stores, files, search/vector indices, caches, analytics extracts, backups (separate, documented expiry), subprocessors (provider-side deletion requests), with **completion evidence**; legal-hold exceptions are explicit |
| **Data subject requests** | access/erasure/portability tracked as cases (§23.4); erasure respects retention duties by anonymising instead of deleting where law requires keeping the record |
| **Export** | full-company export (§13.9) and per-domain exports use the same mechanism and the same permission model |
| **Legal hold** | a flag that suspends purge for defined scopes; audited |
| **Customer-managed keys, multi-region** 🟠 *post-beta contract slots* | key references on stores and region attribute on `company` are modelled now (no behaviour yet) so later adoption is a migration, not a redesign |

### 19.10 Acceptance tests — data

| ID | Test |
|---|---|
| PAT-DAT-01 | Cross-schema write attempts are rejected by role grants; a repository scan finds no direct cross-module table access |
| PAT-DAT-02 | Every migration passes expand/contract checks and a restore-and-migrate rehearsal on production-shaped data |
| PAT-DAT-03 | Upload quarantine: an infected or mistyped file never reaches `ready`; signed URLs expire; a foreign tenant cannot fetch another tenant's key |
| PAT-DAT-04 | Search returns no document the caller cannot read, including via suggestions and facets; deleted/revoked access disappears within the freshness SLA |
| PAT-DAT-05 | Index rebuild from scratch reproduces the same result set |
| PAT-DAT-06 | Company deletion saga: after completion evidence, no tenant data remains in primary stores, files, indices or caches; backup expiry is documented and verified by date |
| PAT-DAT-07 | Money and quantity arithmetic fixtures (rounding, tax, milli-units) pass; no floating point in monetary columns (schema scan) |
| PAT-DAT-08 | Invoice numbers are server-generated and gap-aware; a client-supplied number is rejected |
| PAT-DAT-09 | Legal hold blocks purge for the held scope only |
| PAT-DAT-10 | A Valkey flush loses no business fact and the system recovers without manual repair |

---

## 20. Credits, plans, billing and usage

### 20.1 Principles

Credits make cost **a first-class constraint** (AR-26): every expensive operation reserves budget at preflight, usage is metered against the actor chain, and caps are enforced by the Platform — not by prompts. There is **one** plan/price/entitlement registry; the three price families found in the old documents are merged into it (D-14, G6: website = checkout = invoice = docs = contract).

### 20.2 Credit ledger

An **append-only ledger** per company with entry kinds: `grant` (plan/trial/promo), `reserve`, `settle`, `release`, `adjust` (audited manual correction), `expire`. Balance = grants − settled − open reservations. Reservations are idempotent by `(action_id | mission_step, input_digest)`. The ledger is the single source for "can this run?" decisions; derived balances may be cached with revision checks.

### 20.3 Metering sources

| Source | Unit | Notes |
|---|---|---|
| AI Gateway | tokens in/out/cached × model rate | settled from provider usage (§15.7) |
| Browser sandbox | minutes + steps | per mission page budget (§17.6) |
| CAPTCHA solves | per solution (cost passthrough + margin 🟠) | cap per day/month (§17.4) |
| Storage and egress | GB-month, GB | derived from object store inventory |
| Connectors / sync | calls or rows above plan allowance | Integrations engine |
| Channel messages | per message where the channel is metered (e.g. WhatsApp later) | |
| Jobs / compute | job-seconds for heavy kinds | only where cost-relevant |

Rates live in the **rate card** (versioned, effective-dated). Price changes never rewrite history.

### 20.4 Plan / price / entitlement registry

`plan` → `plan_version` (immutable) → `entitlement set` (capability IDs, quotas) + `price` (per currency, billing period) + `rate card`. Add-ons, trials and promotions are grants on top. Subscriptions reference a `plan_version`; upgrades/downgrades create new subscription items with proration rules. Products query capabilities by stable IDs (§6.4).

### 20.5 Free beta with hard per-company credit caps ✅ D-14 / G6

- The beta is free; every test company receives the **beta plan grant** with a **hard cap** on credits per period and sub-caps per source (AI, browser, CAPTCHA, storage).
- **Hard** means: when the cap is reached, new reservations are rejected, running missions end `budget_exhausted`, and the company is notified through the Channel Port; no overdraft.
- Caps are visible in the Ottili Console (usage, remaining, projected); admins can request more — an operator decision, audited.
- Ottili bears the inference cost of test companies, so the caps are sized from measured cost per mission (M1–M6) and reviewed weekly during the beta 🟡.

### 20.6 Billing and invoicing (after the beta) 🟠

- Subscriptions, usage-based add-ons, credit top-ups, invoices and dunning are built on the registry; a payment provider port (Stripe first) handles collection; invoices for Ottili's own customers follow the same GoBD-oriented rules as the HQ invoice service (numbers server-side, immutability, correction documents).
- **alran API & Console** shows keys, usage, budgets and bills per organisation; it reads the same ledger.
- VAT/e-invoicing obligations and reverse-charge handling are listed as `UNVERIFIED` hints for the tax adviser (D-28), not implemented as claims.

### 20.7 Acceptance tests — credits and billing

| ID | Test |
|---|---|
| PAT-CRD-01 | Concurrent reservations never exceed the cap (race fixture); the ledger balance equals the sum of entries |
| PAT-CRD-02 | A reservation is idempotent; replaying a step does not double-reserve or double-settle |
| PAT-CRD-03 | Reaching the cap stops AI, browser and CAPTCHA use immediately and ends missions `budget_exhausted` with a notification |
| PAT-CRD-04 | Settlement matches provider usage within tolerance; unmatched usage raises an anomaly |
| PAT-CRD-05 | Plan version changes are effective-dated and do not alter past usage valuation |
| PAT-CRD-06 | Website price, checkout price, invoice and documentation render from the same registry version (consistency check) |
| PAT-CRD-07 | A company cannot read or spend another company's credits (isolation fixture) |

---

## 21. Notifications and settings

### 21.1 Notifications

Notifications are **intents** (§10.4) rendered per channel through the Channel Port: *inbox item*, *email*, *chat message*, *digest*. Rules: user and company preferences (channels, categories, quiet hours); digest aggregation for volume; localisation via message catalogues; idempotent send with delivery receipt; unsubscribe/consent handling for non-transactional mail; templates are versioned and tenant-overridable within a safe variable set. Transactional email goes through a provider port (IMAP/SMTP or API provider) with bounce/complaint handling. Mail text assembled from tenant or external data is escaped; templates cannot execute code.

### 21.2 Settings

A **typed settings registry**: each setting has key, owner module, scope (platform · company · user), schema, default, who may change it, audit level, and whether it is secret. Resolution order: user → company → plan default → platform default, with enforced locks (a company setting can lock a user setting, e.g. the autonomy ceiling). Settings changes are Actions (audited, revisioned, previewable); secrets are stored only as `SecretRef`.

### 21.3 Acceptance tests

| ID | Test |
|---|---|
| PAT-NTF-01 | Notification fan-out respects user/company channel preferences and quiet hours; a critical security notification overrides quiet hours but not channel allow-lists |
| PAT-NTF-02 | Digest aggregation collapses N events into one message with correct counts and deep links |
| PAT-NTF-03 | Duplicate send attempts produce one delivery (idempotency); delivery receipt is audited |
| PAT-NTF-04 | A template variable containing markup or a script does not execute or break rendering (escape fixture) |
| PAT-SET-01 | Setting resolution order and locks behave as declared; a user cannot override a locked company setting |
| PAT-SET-02 | A secret setting never appears in API responses, logs, exports or the audit diff |

---
## 22. Audit, receipts and evidence

### 22.1 Principles

Audit is **evidence**, not logging (P7). It is append-only, tenant-scoped, tamper-evident and stored separately from application logs. Receipts (§8.5) are the per-action evidence; the audit log is the chronological, company-wide record that references them.

### 22.2 Audit event

```ts
interface AuditEvent {
  audit_id: string; company_id?: string;       // platform-level events have no company
  occurred_at: string;
  actor: ActorChain;                           // §4.6 — user · agent · skill · service · operator
  category: "auth" | "policy" | "action" | "approval" | "data_access" | "admin" | "billing" | "security" | "integration" | "agent" | "lifecycle";
  verb: string;                                // e.g. action.executed, grant.created, autonomy.ceiling_changed
  subject: { type: string; id: string; revision?: number };
  outcome: "success" | "denied" | "failed" | "unknown_external_result";
  policy_revision?: string; receipt_ref?: string; request_id: string;
  diff?: { before_hash: string; after_hash: string; redacted_fields: string[] };
  data_class: DataClass;
  prev_hash: string; hash: string;             // hash chain per (company, partition)
}
```

Always audited: authentication events (§5.7), grants and role changes, **autonomy ceiling and level changes**, kill-switch use, approvals (request, decision, channel, delivery), every external change and destructive action, data export and deletion requests, operator access (support grants, break-glass), connector and MCP registrations, CAPTCHA domain approvals, model policy changes. Sensitive values are never stored — only digests and redacted diffs.

### 22.3 Tamper evidence

- **Hash chain** per company partition: each event stores `prev_hash`; a verification job re-computes chains on a schedule and on demand.
- **External anchoring:** a periodic digest of each chain head is written to a separate trust boundary (separate storage account/bucket with write-once semantics or an external timestamp) so a database admin cannot silently rewrite history.
- **Write path:** the application role may `INSERT` only; `UPDATE`/`DELETE` are not granted; partition drops are an operator-only, audited maintenance action.
- **Repository protection:** R14 found a "clean worktree and push" step that deleted audit chains; audit-related paths are protected paths in the GERMO safe-commit and CI (see §27.8).

### 22.4 Access and retention

- Company admins see their company's audit in the Ottili Console (filter by actor, verb, subject, time; export). Platform operators see platform-level audit and **only** company audit under a support grant (§6.7), which is itself audited and visible to the company.
- Retention is configured per category (security and financial-relevant events longer); retention values are `UNVERIFIED` until confirmed (§23.6). Deleting a company deletes its audit after the retention duty, except what law requires keeping (legal hold).
- Audit access by non-admins is a permission (`audit.read`), not implicit.

### 22.5 Logs, metrics, traces are not audit

Operational telemetry (§24.5) may be sampled, rotated and redacted; audit may not. Audit never depends on the observability stack being up: the audit write is part of the transaction (or outbox) of the audited change.

### 22.6 Acceptance tests — audit

| ID | Test |
|---|---|
| PAT-AUD-01 | Every action execution, approval, grant change and autonomy change produces an audit event with actor chain and policy revision (coverage test over the action registry) |
| PAT-AUD-02 | The application DB role cannot `UPDATE`/`DELETE` audit rows; an attempted tamper is detected by the chain verifier |
| PAT-AUD-03 | Anchored head digests detect rollback of the audit table to an earlier state |
| PAT-AUD-04 | Operator access to a company's audit without a support grant is denied; with a grant it is allowed, expiring, and visible to the company |
| PAT-AUD-05 | Secrets and personal payload values never appear in audit diffs (secret/PII scanner) |
| PAT-AUD-06 | Audit write failure fails the audited operation (fail closed), except where the audit itself is the outbox row committed in the same transaction |
| PAT-AUD-07 | Repository protection: a GERMO safe-commit that touches audit-protected paths is blocked |

---

## 23. Legal, privacy and compliance architecture

### 23.1 Posture

All legal, tax and licence statements in this blueprint are **hints for implementers, not legal advice** (Doc 1 §0). The architecture provides controls and evidence; whether a control is *sufficient* is decided by a lawyer or tax adviser. With no budget now (D-28), the plan is staged: own companies first; drafts for the privacy notice, DPA/AVV, beta terms, T5 liability text and AI-marking policy plus a question list; **one fixed-price review before external test customers**. Unverified legal or tax points are modelled as configurable values with status `UNVERIFIED`, never as product claims (P11).

### 23.2 Legal documents and acceptance

Versioned documents (terms, beta terms, privacy notice, DPA/AVV, acceptable-use policy, subprocessor list, T5 liability notice) live in a **legal document registry**: version, language, effective date, changelog, hash. Acceptance is recorded per user and per company (who, which version, when, from where); material changes require re-acceptance before use. The beta terms state the free beta, credit caps, availability expectations and data handling.

### 23.3 AI regulation controls (EU AI Act Art. 50 and related) 🟢 D3/D15 — hint

- **Chatbot notice:** every alran surface shows that the user interacts with an AI system.
- **Marking of synthetic content:** LD3 output carries **machine-readable provenance** metadata; the **visible AI label is a switch per project** (✅ D-09; default proposal: no visible label, but machine-readable origin, human release and a named editorial owner 🟠). Transitional periods apply for legacy systems until 02.12.2026 per secondary sources; legal review before the public beta.
- **Human oversight:** autonomy regulator, approvals, kill switch (§9).
- **AI inventory:** the registry lists models, providers, purposes, data classes, evaluation sets and owners; the AI Gateway exports it (§15.3).
- **Training data policy:** no outputs of providers whose terms forbid it in training sets (`distillation_allowed`), provenance field on every training example (Research Labs blueprint).

### 23.4 Privacy by design

| Control | Architecture |
|---|---|
| Records of processing | generated from the data catalogue (§19.3) + module manifests (`data` section) |
| Data subject requests | tracked as cases: access, rectification, erasure, portability, objection; SLA timers; actions executed through the same deletion/export machinery (§19.9) |
| Minimisation | event payloads by reference (§18.3); gateway classification (§15.4); logs redacted (§24.5) |
| Purpose binding | data class + purpose on gateway calls; analytics uses de-identified aggregates |
| Consent and communication preferences | consent records per contact and purpose (CRM core); LD3 and mail honour them |
| DPIA support | template and evidence collection for high-risk processing (agents acting on personal data) |
| Breach handling | incident process with timers (GDPR notification window 72 h as a hint), affected-company lists from audit |

### 23.5 Subprocessor register (gate G2)

Every subprocessor has an entry: purpose, data classes, regions, contract status (DPA/AVV, SCC), technical and organisational measures, exit plan. Initial entries: AI providers (OpenRouter incl. **EU-only addendum Exhibit A chosen in writing**, own-hosted models), CAPTCHA provider (2Captcha), hosting (Hetzner), CDN/DNS (Cloudflare), email provider, channel providers (Slack, Discord, Telegram; WhatsApp later), payment provider (post-beta), backup storage. **A provider is not enabled in production until its register entry is complete.** The customer-facing subprocessor list is generated from the register.

### 23.6 Invoicing, tax and bookkeeping 🔴 UNVERIFIED

HQ invoicing follows GoBD-oriented design: server-side numbering and totals (R14), immutability after issue with correction documents, audit trail, export to DATEV. Retention periods, VAT handling, e-invoicing obligations and reverse-charge cases are stored in a **configurable `UNVERIFIED` rules table** with a mandatory tax-adviser review flag. The Platform provides the mechanism (rules, effective dates, evidence); it does not assert correctness.

### 23.7 Open-source and licence governance (gate G1)

- Licence inventory and SBOM per release (§24.7); copyleft and non-commercial terms flagged before adoption (DeerFlow MIT, Codex Apache-2.0, candidate apps such as ArtCraft: review pending, D-23).
- **Company licence:** LICENSE v6.2 (Willi's statement; the project copy is v6.0 and omits alran, GERMO and model names) is added to the project and verified in G1.
- Model licences: Qwen3.8-27B (Apache-2.0) unproblematic; the Flash-Next base needs a separate licence for "Model as a Service" / "AI Work Assistant" use (Qwen Community License, D16) → frozen for planning.

### 23.8 Provider-terms register

A table of third-party terms that constrain behaviour, each with a flag in code and a review date: model providers' use restrictions (e.g. Anthropic Commercial Terms D.4 — competing products, training competing models, resale — 🔴 interpretation open), eBay's buy-agent rule (D4), Kleinanzeigen § 5 No. 1 (D10), 2Captcha purposes (D12), AliExpress dropshipping API terms (to check), OpenRouter DPA. The register drives gateway flags (`distillation_allowed`, `resale_allowed`), browser blocklists and connector defaults.

### 23.9 Portability and switching

EU Data Act switching/portability support is implemented as the full-company export plus open APIs (§13.9, AR-15); switching charges are phased out from 12.01.2027 (🟢 D5, hint).

### 23.10 Acceptance tests — legal and privacy

| ID | Test |
|---|---|
| PAT-LEG-01 | A new legal-document version blocks product use until accepted; acceptance records are queryable per user and company |
| PAT-LEG-02 | A provider without a complete subprocessor entry cannot be enabled in a production company (gate test) |
| PAT-LEG-03 | Every alran surface shows the AI-interaction notice; LD3 output carries provenance metadata when the visible label is off |
| PAT-LEG-04 | A data subject erasure request removes or anonymises the person across primary stores, files, indices and agent memory, with completion evidence; retention-bound records are anonymised, not silently kept |
| PAT-LEG-05 | `UNVERIFIED` rules are visibly flagged in the UI and exports; they cannot be marked verified without reviewer identity and date |
| PAT-LEG-06 | SBOM and licence inventory are generated for every release and flag a copyleft/non-commercial dependency |
| PAT-LEG-07 | The privacy record of processing generated from the catalogue matches the module manifests (drift check) |

---

## 24. Security

### 24.1 Threat model (summary)

| Threat | Primary controls |
|---|---|
| Cross-tenant access (API, cache, search, jobs, files, AI) | §6.5 five layers, §6.9 suite, RLS adoption gate |
| Stolen credentials / session | §5 (PKCE, rotation, reuse detection, step-up), device/session management |
| Privilege escalation (user, agent, app) | deny-by-default policy, grants ∩ rights, closed contribution vocabulary, fail-closed extension host |
| Prompt injection / confused deputy / tool poisoning | AR-05, AR-06, action pipeline, MCP registry allow-lists, injection fixtures |
| Data exfiltration through AI/egress | data classes, gateway eligibility, sandbox egress allow-lists, destination checks at preflight |
| Supply-chain compromise | pinned digests, SBOM, provenance, private registry, protected branches/paths |
| Insider / operator abuse | support grants, break-glass audit, separate operator identity, anchored audit |
| Denial of service / cost abuse | rate limits, quotas, credit caps, concurrency keys, circuit breakers |
| Webhook forgery / replay | signature + timestamp + dedupe (§13.6) |
| Malicious files | quarantine + scan (§19.5) |

### 24.2 Authentication and authorisation

See §5 and §6; this chapter adds only the cross-cutting rules: all internal calls authenticate (workload JWT); no endpoint trusts a network position; authorisation is re-evaluated at execution time; admin and operator surfaces require MFA and step-up.

### 24.3 Secrets

- Secrets live in the secrets manager (Infisical-class) and are addressed by `SecretRef`; applications receive them just-in-time, scoped, short-lived where possible.
- No secret in code, images, flow definitions, manifests, prompts, sandboxes, logs, traces or backups of configuration (scanners in CI and on stores).
- Rotation procedures exist per secret class (DB, provider keys, signing keys, OAuth client secrets); rotation is tested; compromise runbooks name the owner.
- The pack contains a fallback password in a dev helper (`truth-dev-only`); fixing such defaults is a G3 item — **production code must refuse to start with a known default secret**.

### 24.4 Network and transport

Edge via Cloudflare (DNS/WAF/DDoS) and Caddy (TLS termination, HTTP security headers); private connectivity via Tailscale; internal service-to-service traffic authenticated (mTLS or signed tokens); databases and object storage not publicly reachable; sandboxes in an isolated network segment with allow-listed egress (§17.2); outbound calls from the platform pass an SSRF guard (deny private/link-local ranges, resolve-then-check, redirect limits).

### 24.5 Logging, redaction and telemetry

- Structured logs with request, company and trace IDs; **PII/secret redaction at the logger** and a scanner on the log pipeline; log bodies of prompts/responses off by default (§15.12).
- OpenTelemetry for traces/metrics/logs; Prometheus/Loki/Tempo/Grafana stack (§27.6); high-cardinality tenant labels are controlled; tenant isolation applies to dashboards shown to customers.
- Security-relevant events are copied to audit (§22), not only to logs.

### 24.6 Application security

Schema validation at every boundary (JSON Schema/zod-class), output encoding, CSP and frame policy for app iframes, CSRF protection for cookie-based BFF sessions, strict CORS, upload limits, rate limiting per key/IP/company, dependency pinning, secure defaults for cookies (HttpOnly, Secure, SameSite), no secrets in URLs, clickjacking protection.

### 24.7 Supply chain

- **Builds are reproducible-ish and promoted by digest** (AR-18): CI builds once, signs the artifact/provenance, stores the SBOM, and production deploys the digest.
- **Dependencies:** lockfiles, private registry (Verdaccio for `@ottili/*`), proxy of public registries with allow-list and quarantine for new versions; licence scan; known-vulnerability scan with SLAs per severity.
- **Harness dependencies** (DeerFlow, Codex) are pinned and verified like any other (§16.4).
- **GERMO** (the build factory) pushes directly to `main` (D-17 ✅: no integration branch, no review hook), therefore the guards inside safe-commit stay on: owned paths only, secret scan, gate bound to exact content, protected-paths list (audit, migrations, auth, policy), and CI as the second line. Residual risk (R14: clean-worktree push deleted audit chains) is covered by protected paths.
- **The GERMO pack and its truth-kit are untrusted input:** nothing in the pack is executed; scripts are read, not run; reviewed code is copied into a repository only through the normal gates.

### 24.8 AI-specific security

Controls consolidated from earlier chapters: untrusted-content marking (AR-06), authorisation never derived from model output (AR-05), tool results treated as data, per-tool risk classes, egress allow-lists, memory poisoning defence (memory entries are provenance-tagged and reviewable, §16.5), output validation against schemas before use, cost-based DoS limits, kill switch. **Injection fixtures** (mail bodies, product titles/descriptions, web pages, PDF text, tool outputs, channel messages) run in CI against the full action pipeline; a fixture that changes authorisation, destination or tool choice fails the release.

### 24.9 Vulnerability and incident management

Named **incident owner** and deputy; severity levels with response targets; runbooks (credential leak, tenant-isolation breach, provider compromise, data loss); customer and authority notification timers (GDPR 72 h hint); post-incident review with action items; status page (G4/G8). Vulnerability intake via a security contact and `security.txt`.

### 24.10 Security release gates

A release is blocked unless: tenant-isolation suite green, authorisation matrix tests green, injection fixtures green, secret scan clean, SBOM generated, critical/high vulnerabilities within SLA, restore proof current (≤ 30 days), audit chain verification green.

### 24.11 Acceptance tests — security

| ID | Test |
|---|---|
| PAT-SEC-01 | Secret scanners find no secrets in repositories, images, logs, traces, sandboxes and flow definitions (seeded canary secrets are detected) |
| PAT-SEC-02 | The SSRF guard blocks requests to private ranges, metadata endpoints and redirects into them |
| PAT-SEC-03 | A service started with a known default secret refuses to boot in production mode |
| PAT-SEC-04 | The full injection fixture corpus yields zero authorisation, destination or tool-choice changes |
| PAT-SEC-05 | Rate limiting and quotas hold under a burst test per key, IP and company; the platform stays within SLO for other tenants |
| PAT-SEC-06 | Release pipeline refuses an artifact without provenance, SBOM and signature; production runs the promoted digest only |
| PAT-SEC-07 | Break-glass operator access is time-boxed, audited and visible to the company |
| PAT-SEC-08 | Security headers/CSP/cookie flags meet the baseline on all public hosts (scanner) |
| PAT-SEC-09 | Incident drill: a simulated credential leak is detected, contained and rotated within the runbook targets |

---

## 25. Experience foundation

### 25.1 Principle

UI is **a client of actions and read models**, never a second source of business rules (P2). The experience foundation provides what every product shares so that HQ, LD3, apps and the Console feel like one system (promise 1).

### 25.2 Design system and components

A shared token set (colour, type, spacing, elevation, motion, density), a component library with accessibility built in, and layout primitives (app shell, split views, tables with virtualisation, forms with server-side validation messages, empty/error/loading states). Tokens are themeable per company within guardrails (logo, accent); dark mode is part of the token set. Components consume i18n keys only (AR-24). A **component workbench** (successor of the former "Foundation Lab") renders every component state, theme, locale and density in CI for visual and accessibility regression. White-label beyond logo and accent colour is post-beta 🟠.

### 25.3 App shell and navigation

Few, well-named areas; advanced functions reachable progressively, **not removed**; one global command palette over navigation, search and actions (`command` contributions, §7.3); breadcrumbs and a consistent record layout (header, key facts, timeline, related records, attachments). Installed apps add areas via manifests; deactivating a core module removes its areas and dependencies cleanly (D-03). A simulated terminal (post-beta) is a command interpreter over actions (§7.8), not a shell.

### 25.4 Bootstrap read model

On session start and on every company switch the client fetches one **Bootstrap** document: user, selected company, role/permission summary (for UI hints only — never authorisation), entitlements, enabled products/apps with their navigation and contribution points, locale and time zone, autonomy ceiling and selected level, feature flags, revision numbers. It is cacheable by `bootstrap_revision`; any change emits a revision bump, the shell re-fetches, and **a company switch cancels in-flight company-scoped work and drops scoped caches** (§6.1). Missing bootstrap data fails closed to a minimal shell with an error, never to a default company.

### 25.5 Extension surfaces

Third-party and tenant-private app UIs run in cross-origin iframes with the bridge protocol (§7.5); first-party modules may be federated components under the same CSP discipline. Contribution points: route, navigation, command, widget, record section, custom field, report, file view.

### 25.6 The SAP lesson — three rules made testable 🟢 VD, V §5.1

1. **Navigation:** few clear areas; domain terms explained in place; advanced functions progressively disclosed.
2. **Numbers:** every figure shows unit, period, comparison and an explanation; **empty states say why they are empty**; filters never block simple tasks.
3. **Onboarding:** a usable default view without configuration; demo data to try things; **no months of training**.

Implemented as acceptance criteria on each product's golden paths (e.g. "a new company reaches a populated morning dashboard in under N minutes using demo data" — N set after the first measurement 🟡).

### 25.7 Accessibility and responsiveness

Target WCAG 2.2 AA for all first-party UI; keyboard-complete navigation; focus management in dialogs and iframes; contrast and motion preferences honoured; responsive layouts down to tablet width in the beta (native app clients are out of scope). EU accessibility legislation may apply to some offerings — hint, check with counsel.

### 25.8 Performance budgets

Per-route budgets (interaction latency, bundle size, API calls on first paint) and server-side p95 targets per capability (D-16: both a stretch load campaign and per-capability performance budgets). Budgets are measured in CI on a reference environment and reported, not guessed.

### 25.9 Internationalisation (AR-24)

- All user-visible strings come from message catalogues (ICU MessageFormat) with stable keys; **`de` and `en` are release-gated** (no missing keys, no untranslated fallback in `de`); code, identifiers, errors' machine codes and logs are English.
- Locale-aware formatting for numbers, dates, currencies, units; time zone per company/user; right-to-left readiness (logical CSS properties) as a design constraint; pseudo-locale test catches hard-coded strings and layout overflow.
- Server-originated messages (notifications, emails, validation errors) use the same catalogues with the recipient's locale. LLM-generated text is generated in the requested language and labelled as generated content where required (§23.3).

### 25.10 Ottili Console — admin surface of the Platform ✅ W18b

Explicitly marked important by the founder (W18b). The Console is the administrative UI of the Platform (not "alran Console", not the Developer Console of alran API):

| Area | Content |
|---|---|
| Members and roles | invitations, roles, custom roles, SSO status, sessions, MFA enforcement |
| Companies | profile, time zone, locale, legal documents accepted, deletion/export |
| Rights and policy | permissions, grants, support grants, **autonomy ceiling** and per-action maxima (with step-up), allowed channels, data-class/model policy flags |
| Agents | agent principals, grants, budgets, kill switch |
| Apps and extensions | catalogue, install/uninstall, consent screens, versions, health |
| Integrations | connections, bindings, maturity, sync health, DLQ |
| Billing and credits | plan, caps, usage, invoices (post-beta) |
| Developer | API keys, OAuth clients, webhooks, MCP clients and toolsets |
| Privacy and audit | audit explorer, DSR cases, subprocessor list, retention |
| Operations | system health summary, feature flags (operator only) |

R14 found 353k lines for ~10 pages and empty browser routes: **shrink first (`CON-W0-04`), then build** — the Console is rebuilt on the shared foundation and tested against the real browser. Every Console function is an Action (parity, AR-21).

### 25.11 The autonomy regulator in the product

Label (English base string): **"Choose how autonomous alran can do actions"**, German via i18n. The control appears in alran AI and the HQ/LD3 panels; levels above the company ceiling are locked with an explanation; T5 sits behind a confirmation (§9.7).

### 25.12 Acceptance tests — experience

| ID | Test |
|---|---|
| PAT-UX-01 | Bootstrap: permissions in the UI never grant API access (API still denies); a revision bump triggers a re-fetch; a company switch cancels in-flight work and clears scoped caches |
| PAT-UX-02 | i18n gate: no missing keys in `de`/`en`; pseudo-locale run finds no hard-coded strings; server messages use the recipient locale |
| PAT-UX-03 | Accessibility: automated checks plus keyboard-only run on the golden paths pass WCAG 2.2 AA criteria set |
| PAT-UX-04 | New-company journey with demo data shows a populated dashboard; empty states explain themselves; every KPI has unit/period/comparison/explanation (UI test) |
| PAT-UX-05 | Every Console function maps to a registered action (parity scan) and works against the real browser (no empty routes) |
| PAT-UX-06 | The autonomy regulator cannot select a level above the ceiling; T5 requires confirmation and owner rights |
| PAT-UX-07 | Per-route performance budgets are measured in CI and regressions fail the build |

---

## 26. API conventions

### 26.1 Style and versioning

Resource-oriented HTTPS JSON APIs under `/v1/...` per module; additive changes within a version; breaking changes only in a new major path with a deprecation window. Action invocation: `POST /v1/actions/{action_id}:invoke` (and typed convenience routes generated from definitions). OpenAPI 3.1 documents are generated from the action/route definitions — one source of truth.

### 26.2 Errors

Problem Details (RFC 9457) with stable machine `code`, i18n `title` key, `request_id`, `retryable` flag and field-level validation errors. Reserved codes include `policy_denied`, `entitlement_missing`, `approval_required`, `budget_exhausted`, `revision_conflict`, `idempotency_conflict`, `unsupported_by_provider`, `no_eligible_model`, `unknown_external_result`, `rate_limited`, `tenant_context_missing`. Errors never leak existence of other tenants' resources (404 vs 403 policy documented).

### 26.3 Idempotency

`Idempotency-Key` header on all mutating calls; keys are scoped to `(company, caller, route)`; the stored response is replayed for the retention window; same key with different payload ⇒ `idempotency_conflict`.

### 26.4 Pagination, filtering, sorting

Cursor pagination (opaque cursors, stable ordering), explicit page-size caps, allow-listed filter/sort fields, total counts optional and rate-limited.

### 26.5 Concurrency

`ETag` / `If-Match` backed by aggregate `revision`; lost updates return `revision_conflict` with the current revision.

### 26.6 Contract tests and consumer conformance

- Machine-readable **dependency registry** of producer → consumer edges (APIs, events, actions, manifests).
- For every contract change CI computes affected consumers and runs their contract tests against **at least the latest supported and the next candidate version**.
- Event schemas follow compatibility rules (§18.3); action definitions are semver'd; the manifest schema is versioned (`ottili.product/v3`, `ottili.app/v3`).
- Contract tests run against the real implementation and real DB, not mocks of the Platform (R14: golden paths against real DB and UI).

### 26.7 Rate limits and quotas

Limits per key, user, IP and company, per capability class; `429` with `Retry-After`; quotas visible in the Console; platform-internal callers have separate budgets; limit headers are standardised.

### 26.8 Outbound webhooks

Signed (`HMAC-SHA256` over timestamp + body), timestamp tolerance, delivery ID, retries with backoff, delivery log, secret rotation with overlap, replay endpoint. Inbound webhooks use the same signature discipline per provider (§13.6).

### 26.9 Asynchronous operations

Long operations return `202` + a job resource with status, progress, result link and cancel; clients may subscribe to events instead of polling.

### 26.10 SDK and developer experience

Generated TypeScript SDK (and OpenAPI for others); the SDK enforces idempotency keys and typed errors; a local host simulator for app developers (§7.6); examples are tested in CI.

### 26.11 Acceptance tests — API

| ID | Test |
|---|---|
| PAT-API-01 | Every public route has an OpenAPI entry generated from definitions; drift between code and spec fails CI |
| PAT-API-02 | Idempotency: replay returns the stored response; payload mismatch returns `idempotency_conflict` |
| PAT-API-03 | Concurrent updates with stale `If-Match` return `revision_conflict` and do not overwrite |
| PAT-API-04 | Problem Details are produced for all error paths; no stack traces or tenant-existence leaks |
| PAT-API-05 | A breaking change to an event schema or action definition fails the consumer-conformance job |
| PAT-API-06 | Rate limiting returns `429` with `Retry-After`; limits are per company and do not starve other tenants |
| PAT-API-07 | Webhook signature verification rejects tampered, expired and replayed deliveries |

---
## 27. Infrastructure, deployment and delivery

### 27.1 Environments

`local`, `development`, `test`, `preview`, `staging`, `production` are first-class resources sharing contracts, migration format, image format, health semantics and configuration schema; they differ in **values and scale, not in architecture**. Production and staging never share writable databases, Valkey namespaces, cookies, OAuth redirect registrations or provider credentials. Staging never uses production credentials or tenant data by default; sanitised imports are explicit, provenance-tracked jobs. Preview environments (optional) have synthetic data, isolated domains/secrets/DB namespaces and automatic expiry.

> **Beta reality (D-20 ✅):** the existing servers are **development infrastructure** (Codex agents, tests, builds). Production servers come later from revenue. The beta for own companies and first test customers therefore runs on development infrastructure with **limited concurrency** 🟡 — a conscious trade-off, listed as risk RSK-04 (§32.2).

### 27.2 Network and zones

Logical zones (even when they share hardware): **public edge** (Cloudflare + origin ingress), **control** (gateway/auth/platform APIs), **data** (PostgreSQL, backup/archive, object metadata), **worker** (jobs, flows, files, LD3, integrations), **agent** (sandboxes, browser sandboxes; §4.3), **management** (Tailscale ACLs, operator access), **observability** (independent collection). Default deny between zones except declared dependencies.

- Cloudflare: DNS, proxy/CDN, WAF/rate limiting. Caddy: origin ingress (TLS, routing to private upstreams), config generated from a versioned **Domain Registry** and reloaded atomically; no application edits ingress.
- Application ports bind to loopback/private interfaces. Product containers get no Docker socket and no host-repository mounts.
- Tailscale is an administrative overlay, not authorisation.
- Domains (🟠 naming): `auth.ottili.one` (identity), `api.ottili.one`, `mcp.ottili.one`, app hosts per product, `status.ottili.one` (independent).

### 27.3 Deployables — grouped but with explicit logical owners

One logical service ≠ one process. For the beta the deployables are grouped to match the available hardware; module boundaries (code ownership, schemas, contracts) stay explicit so a deployable can be split without redesign.

| Deployable | Logical owners inside | Scale unit |
|---|---|---|
| `edge` | Caddy ingress | host |
| `identity` | Keycloak + Ottili Auth service | instance (stateless except DB) |
| `platform-api` | gateway/BFF, company, policy, entitlements, actions, approvals, operations, registry, settings, audit writer | stateless replicas |
| `platform-workers` | outbox relay, job runner, flows runtime, integrations sync/webhooks, notifications, search indexer, credits settlement | pools by queue |
| `ai-gateway` | AI Gateway, MCP registry, metering | stateless replicas |
| `agent-runtime` | harness adapters (DeerFlow instances per company group, Codex hosts), mission service | per isolation unit (AR-17) |
| `browser-sandbox` | browser/CUA sandboxes | per mission |
| `hq` | HQ API + workers (domain) | stateless replicas |
| `ld3` | LD3 API + pipeline workers | stateless replicas |
| `console-web`, `hq-web`, `ld3-web`, `alran-web` | front ends | static/edge + SSR if needed |
| `alran-api-console` | alran API & Console face | with `ai-gateway` |
| data | PostgreSQL (+ pooler), object storage, Valkey | stateful, single writer |
| observability | Prometheus/Loki/Tempo/Grafana/alerting | independent node when available |

### 27.4 Servers today and roles

| Node | Place | Role (beta) |
|---|---|---|
| `ottiliserver01` | basement (own premises) | core/data + edge + development workloads (as available) |
| `ottiliserver02` | Hetzner cpx42 | workers, agent runtimes, degraded-recovery fallback |

The long-range infrastructure blueprint planned a six-server small-scale topology plus NAS and off-site backup; **the current two-server reality is kept separate from that target** (Doc 2 §8.1). Facts that drive sizing: a DeerFlow gateway needs ≥ 8 vCPU / 16 GB (D1/D8, 🔴 hardware verification of the cpx42 instance type), so **agent concurrency is the first capacity limit**; heavy untrusted execution must not stay on the core node. The platform dev instance `127.0.0.1:18310` (company `hq-fixture`) is **not touched**; cleanup only after backup and on Willi's word (D-22).

### 27.5 CI/CD — artifact-first, state-machine deployments

```text
source commit → CI validation → deterministic build → immutable OCI artifact (+digest, SBOM, provenance, signature)
→ immutable release manifest → deployment(environment, release)
→ DB compatibility/migration gate → runtime rollout → readiness + critical-journey health gate
→ route activation (atomic at ingress) → observe / rollback
```

- Deployment is a persisted state machine: `queued → preparing → migrating → deploying → health_gating → active | failed → rolled_back | intervention_required`; every transition recorded with evidence; retries idempotent.
- **Production hosts never `git pull`, rebuild from mutable source or use a checkout as release mechanism** (AR-18). Rollback = redeploy a previously known-good immutable release plus its config references; never `git reset` on a host.
- Migrations are expand/contract; a release with a forward-only data transformation rolls back via a compatibility release or documented restore, never by running old binaries against an incompatible schema (§19.2).
- Critical APIs/Auth keep the previous healthy instance until synthetic journeys pass on the new one.
- Small scale: rolling or blue/green per service depending on capacity.

### 27.6 Observability and status

OpenTelemetry instrumentation; Prometheus (metrics), Loki (logs), Tempo (traces), Grafana (dashboards), alerting with named owners. SLIs measure user/system contracts (login journey, API latency, job age, event age, deployment success, backup freshness, restore drill success) rather than process uptime. Observability and the **status page / off-site probe live in a different failure domain** than the thing they report on. Label discipline limits cardinality (tenant labels only where needed). Health endpoints distinguish liveness, readiness and degradation (capability-specific).

### 27.7 Configuration and feature flags

Typed configuration schema per service, validated at boot (fail on unknown or default secrets, §24.3); environment differences are values. Feature flags are Platform settings (§21.2) with owner, expiry date and audit; flags never replace authorisation or entitlements.

### 27.8 Branch model and GERMO ✅ D-17

- **GERMO pushes directly to `main`** (no integration branch, no review hook). Consequence: the guards inside safe-commit stay on — owned paths only, secret scan, gate bound to the exact content, `TRUNK_STATUS.json` — and CI on `main` is the second line.
- **Protected paths** (audit, auth, policy, migrations, release configuration, CI definitions) are enforced by safe-commit *and* by CI; a change touching them requires the corresponding contract/migration tests to be green in the same commit.
- Releases are **tags on `main`** that CI turns into signed artifacts (§27.5); `main` is always buildable; a broken `main` is fixed forward by revert commits, never by history rewrite or force-push.
- Residual risk (R14: a "clean worktree and push" step deleted audit chains) is covered by the protected-path list and by backups of the repositories (Willi's own todo: back up all eight repos before G0).
- GERMO plans, prompts and tasks are **English** and are written only after an explicit "go"; the Platform blueprint describes GERMO only where it constrains architecture.

### 27.9 Scalability — measured, not guessed (AR-25)

Sequence of scale-out: (1) separate heavy workers from request-serving; (2) replicate stateless API/web instances; (3) add a DB pooler, then a replica; (4) split object storage and observability; (5) add qualified runtime nodes; (6) dedicated event/search/orchestration infrastructure only at **measured** thresholds. Bottleneck table (first response → scale response): gateway process (profile → replicas + pooler); PostgreSQL (indexes/pooling → replica/partitioning of append tables); Valkey (classify → separate instances, never truth); workers (oldest-job age → pools/nodes); object storage (lifecycle → replicated/provider storage); build disk (cleanup → external registry/build workers); observability (label discipline → dedicated storage); credits ledger (batched projections → partitioning). **The first response is always to remove accidental coupling and measure; adding infrastructure is second.**

Performance: per-capability budgets measured in CI (§25.8); a stretch load campaign (target order of magnitude 15,000 req/s on a reference topology — D-16 🟠, `PLT-W2-04`) validates the headroom claim but is not a beta promise.

Autoscaling is initially queue/metric-driven **within pre-provisioned capacity**, with min/max, cooldown and budget limits; it never exceeds cost caps silently.

### 27.10 Post-beta slots (contracts only) 🟠

- **Multi-region and customer-managed keys:** `company.region` and key-reference attributes exist in the data model (§19.9); no behaviour in the beta.
- **Ottili Cloud runtime for customers** (managed WordPress hosting, deploy integration for alran Code, customer app runtime): the *internal* deployment controller of §27.5 is the beta scope; offering it to customers is post-beta. Provider abstraction (Docker/OCI nodes first; OpenStack as a later provider under the same contract) is kept stable; the controller never SSHes arbitrary shell strings as its primary API — SSH is break-glass only. Customer WordPress state never enters the Platform transaction database.
- **Self-hosting:** not in 2026 (D-15 🟠); architecture hygiene (no cloud-only assumptions) keeps the option open.

### 27.11 Acceptance tests — infrastructure and delivery

| ID | Test |
|---|---|
| PAT-INF-01 | A release is built once in CI, signed, SBOM'd; production runs only the promoted digest; a host with a mutable checkout is detected by an inventory check |
| PAT-INF-02 | A deployment with a failing health journey does not activate; the previous release keeps serving; evidence is recorded |
| PAT-INF-03 | Rollback redeploys the previous immutable release within the target time and re-applies its config references |
| PAT-INF-04 | Zone policy: connections that are not declared dependencies are blocked (network policy test); containers have no Docker socket |
| PAT-INF-05 | Ingress config is generated from the Domain Registry; manual drift is detected and reconciled |
| PAT-INF-06 | Safe-commit blocks a change that touches protected paths without matching tests, a secret, or content that differs from the gate's input |
| PAT-INF-07 | Configuration validation refuses boot with an unknown key, missing required value or default secret |
| PAT-INF-08 | Load test of the reference journeys on the beta topology records throughput, p95 latency and saturation points; results feed the capacity plan (no unverified performance claim in documents) |

---

## 28. Reliability, backup and disaster recovery

### 28.1 Failure domains

Explicit dimensions: process/container, host, storage device/pool, site (power/LAN), DNS/CDN/provider, credential provider, software release. Replicas and backups are placed across the relevant domains; **two NAS devices in one building are one site domain; a monitor on the primary host is one host domain**. No configuration is labelled "highly available" merely because two processes run on one host.

### 28.2 Backup architecture (AR-19)

One canonical backup controller. PostgreSQL: periodic base backups + continuous WAL archive (pgBackRest-class) to a local repository and an **encrypted, immutable off-site copy**. Object storage: versioning + manifest snapshots + off-site copy. Release registry, configuration state and encryption-key escrow have their own recovery class. Every backup set records ID, component coverage, start/end, source release and schema, checksums, retention class and verification state. Freshness is monitored; a successful backup command is **not** recovery proof.

### 28.3 Restore and drills

Restore is automated and repeatable: create an isolated recovery environment → select a point in time/version → restore DB + matching object/config state → validate integrity and migrations → start the release → run critical journeys → emit measured timing and evidence. Supported: object-level recovery, full-environment recovery, point-in-time recovery. Production replacement is a separate, approved step after validation. **Restore drills run on a schedule; a restore proof older than 30 days blocks release (§24.10).**

### 28.4 Objectives

Planning objectives (not promises): core Auth/Gateway/PostgreSQL **RPO ≤ 15 min, RTO ≤ 60 min** *after* PITR automation is proven; object/file RPO may begin at ≤ 24 h until continuous replication is proven. Failover always **fences** a failed or unknown primary before promotion (no split brain). Site-disaster recovery depends on the encrypted off-site copy, not on local devices.

### 28.5 High-availability roadmap

Stage 1: remove avoidable co-location, prove restore. Stage 2: stateless replicas, independent observability. Stage 3: PostgreSQL async replica on a separate node with rehearsed fenced promotion. Stage 4: provider/site standby. Only then evaluate automated failover or multi-region. Nodes and runtime instances have states `active`, `draining`, `maintenance`, `offline`, `quarantined`; maintenance drains traffic and jobs, verifies recovery capacity, changes, validates health and journeys, then returns capacity gradually; cleanup never deletes unknown volumes, images or backups before ownership and retention are classified. Availability is capability-specific (a preview-worker outage degrades previews while downloads continue; a billing-provider outage degrades payment changes while history stays readable).

### 28.6 SLO / SLI

Candidate SLOs, **set after measurement**: Auth journey ~99.9 %, Gateway/API ~99.9 %, credit-ledger writes ~99.9 % with zero tolerated ledger inconsistency, async jobs by oldest-job age per queue, deployment control plane ~99.5 %, status page independent. Error budgets steer release caution. Five nines is not a planning assumption. 🟡

### 28.7 Degradation matrix (required behaviour)

| Failure | Required behaviour |
|---|---|
| Auth DB unavailable | deny new logins safely; token validation per policy; visible degraded status |
| Gateway instance dies | other ready instance serves; no session truth lost |
| Valkey lost | cache/rate-limit degradation; accepted jobs/events recover from PostgreSQL |
| Worker dies mid-job | lease expires; fencing prevents stale completion; resume from checkpoint |
| Event consumer crashes | durable progress; replay; DLQ after bounded retries |
| Provider duplicates a webhook | signature + dedupe; idempotent reconciliation |
| Cross-tenant ID substituted | denied at policy/query/RLS layers; security event |
| Bad deployment | gate fails or previous release restored |
| Migration partially backfills | checkpoint and resume or forward-repair; old compatible code still works |
| Primary node lost | fence; activate rehearsed degraded recovery/restore; off-host monitor reports |
| Local storage device lost | alternate/off-site copy; no site-DR claim from same-site copy |
| Site/router/power lost | off-site monitor reports; restore elsewhere from off-site copies |
| Object store lost | restore versions + manifest; validate integrity |
| Model provider outage | gateway breaker + eligible fallback or `no_eligible_model` exception |
| Secret backend unavailable | injected secrets continue until policy expiry; no plaintext fallback |

### 28.8 Incident management and status

Incident owner and deputy named (G4); severities, runbooks per failure class, on-call expectation matched to beta honesty (best effort, stated in beta terms); post-incident reviews; **status page independent of core** (G4/G8).

### 28.9 Capacity and cost model

Cost is measured per capability: inference (largest variable cost; development inference free until year end, then paid), compute, storage, egress, third-party APIs (CAPTCHA, channels). Dashboards in the Console (operator view) join metering and infrastructure cost to produce **cost per mission** and **cost per active company** — the inputs for the credit caps (§20.5) and for the post-beta price book. 🟡

### 28.10 Acceptance tests — reliability

| ID | Test |
|---|---|
| PAT-REL-01 | Full restore drill from base backup + WAL to a chosen minute meets the RPO/RTO targets (measured) and passes critical journeys; evidence stored |
| PAT-REL-02 | Backup freshness alert fires when the last verified backup exceeds the threshold |
| PAT-REL-03 | Off-site copy is independent of the primary site; restore from it works with the site unreachable |
| PAT-REL-04 | `kill -9` of API, worker and runtime processes during load loses no accepted job, event or receipt |
| PAT-REL-05 | Valkey flush and loss: system recovers without manual repair (see PAT-DAT-10) |
| PAT-REL-06 | Primary-node loss drill: fencing prevents split brain; degraded recovery serves the core journeys |
| PAT-REL-07 | Status page remains reachable when the core is down; it reports independently measured probes |
| PAT-REL-08 | Degradation matrix rows are exercised by fault injection at least for the first ten rows before beta invitation |

---
## 29. Beta profile

### 29.1 Definition ✅ D-01

> "Beta does not mean perfect. Beta means ready enough to deliver real value." — "We are not building half a product to call it beta. We build the complete product in a first robust, testable and presentable version." (W18b)

| Criterion | What the Platform must show |
|---|---|
| **Everything essential is in** | functional breadth as in the vision; the surface need not be polished — the Platform chapters §5–§28 are implemented to the acceptance tests listed |
| **Thought big and implemented** | no single pipeline passed off as a product; no prototype that only runs in a prepared demo |
| **Investor-capable** 🟡 (reading: an outsider can inspect product, architecture and measurements without a prepared demo) | acceptance against real data, reproducible evidence bundle (gate report), architecture and test results readable without us |
| **Ready for first customers** | own companies first, then selected test customers; free with hard caps |
| **Stable and secure** | G3/G4 met; injection and cross-tenant suites green; backup with restore proof |

### 29.2 Scope — everything except desktop and app clients ✅ W18b

| In the beta | Not in the beta (🟡 reading of "everything except desktop/app"; the architecture keeps the contract slot) |
|---|---|
| Ottili ONE (HQ core + bundled, LD3), Ottili Console, alran AI (web, incl. browser agent and CAPTCHA policy), alran Code (own parallel track), alran API & Console, API, alran in HQ/LD3, first integrations, Flows, Operations, Channel Port, Ottili MCP | desktop and app clients · Shop app (Saleor, Q1 2027) · manufacturing/gastro/office/WMS apps (when a mission needs them) · Odoo/cobra bindings (by test-customer need) · tenant-private apps (Q1–Q2 2027, D-27) · customer/supplier portals · shipping carrier connectors · self-hosting (D-15) · Research Labs (own line) |

### 29.3 Reference missions M1–M6 — the acceptance set ✅ D-01

Each mission runs against **real systems** (test/sandbox accounts), **real database** and **real UI**, with **0 policy violations** and a stable success rate (threshold 🟠 set after the first measurement runs; proposal ≥ 90 % over 20 runs per mission).

| # | Mission | Systems | Level | Platform capabilities exercised | Negative case (must fail or stop) |
|---|---|---|---|---|---|
| **M1** | Check a new supplier article and create it as a draft | supplier API / browser (read), HQ product, Shopify draft | T1 | MCP/actions (read, draft), integrations, browser read, mission, inbox draft | invented mandatory fields instead of asking |
| **M2** | Order without stock cover → order at supplier | Shopify, HQ stock, supplier API | T3 → T4 up to amount limit | Flows, actions with external change, approvals, T4 grant (amount/count/time), verification, receipts, credits | price jump over threshold ⇒ stop + approval |
| **M3** | Supplier delay → inform customer | supplier, HQ, mail | T2 | signal/event, case update, mail action with template policy, task | mail to wrong customer or without policy |
| **M4** | Stock deviation Shopify ↔ HQ | Shopify, HQ stock ledger | T1/T2 | reconciliation, binding refs, internal correction, verification | correction reported as done **without** verification |
| **M5** | Product-launch content, approval, publication | HQ product, LD3, approval channel (web inbox, Slack or Discord), WordPress | T3 | cross-product contracts (S1), Channel Port, Gateway, connector, receipts | publication without approval; product claim without evidence |
| **M6** | Complaint/return → credit-note and mail draft | HQ order/payment, mail | T3 | actions with step-up threshold, drafts, approval | amount above limit without step-up |

Common fixtures for every mission: **injection fixtures** in supplier/mail/product text (§24.8), cross-tenant fixtures (a second company with similar data), kill-switch mid-run, runtime crash mid-run (exactly-once via receipt lookup), budget exhaustion mid-run, provider outage mid-run (`unknown_external_result` handling). Reports distinguish observed, inferred and hypothesis (AR-23).

### 29.4 Build stages BP-0 … BP-6 — all in the beta 🟠

> A build stage is a block of related work with its own acceptance — **not** a choice between paths and **not** a cut order. All stages are in scope (§29.2); order follows dependencies.

| Stage | Platform deliverables (sections) | Acceptance journey | Depends on | Main risk |
|---|---|---|---|---|
| **BP-0 Foundation + Ottili Console** | boot on PostgreSQL; Auth (§5); Company/Policy/Entitlements (§6); Registry with product self-registration (§7); events/jobs (§18); data basics (§19); audit (§22); notifications/settings (§21); credits and caps (§20); Console shrunk first, then rebuilt (§25.10) | register → company → invite → role → activate product/app → plan/credits → audit and notification (`PLT-W2-01`, `CON-W2-01`) | Platform W0 | Platform does not boot yet; Console legacy (353k lines for ~10 pages) |
| **BP-1 HQ core + bundled** | actions registered by HQ (Appendix C), Files/Search contributions, Integrations engine for Shopify/Stripe/DATEV, binding router, invoice numbering/totals server-side | contact → quote → order → stock issue → invoice (GoBD design) → payment → open item → DATEV export (`HQ-W2-02`, `APP-W2-02`) | HQ W0/W1, Shopify/Stripe/DATEV apps | largest scope; stock movement from order missing (R14) |
| **BP-2 LD3 source-to-published** | AI Gateway (§15) for LD3 calls; Channel Port approval; WordPress connector; S1 staleness contract (event `one.hq.product.revised.v1` → LD3 content "to review"); AI marking switch (D-09) | source → topic → evidence → article → review → approval via Channel Port → WordPress → update (`LD3-W2-02`) | LD3 W0/W1, Gateway | no LLM call/connector today; AI Act policy |
| **BP-3 Cases and missions M1–M6** | Flows with editor and compensation (§12); Operations (§11); Approvals/Channel Port with Slack/Discord/Telegram adapters (§10); dropshipping app with supplier APIs (API first); mail | M1–M6 | Flows, Approvals, Operations, HQ purchasing/stock, apps | largest new-build share; proves "HQ is alive" |
| **BP-4 alran in the product** | action catalogue and parity (§8); regulator T0–T5 + ceiling + kill switch (§9); receipts; budgets (§20); Ottili MCP per company (§14) | panel journey in the real browser | Actions, Approvals, Gateway, Policy | action coverage |
| **BP-5 alran AI · Code · API & Console** | DeerFlow adapter incl. browser/CAPTCHA (§16–§17); Codex adapter (own track); alran API & Console on the Gateway (§15.10); model policy (§15.4) | journeys per product | Gateway, adapters, isolation, server capacity | adapter maturity and isolation; `wire_api` check; name separation from Ottili Console |
| **BP-6 Connectivity "Zapier level"** | generic connector mechanism (§13.8), maturity 0–3, browser skills as fallback, one BYO proof (D-26 open; default M365 mail/calendar federated), import profiles (CSV/Excel), Connector Agent contract only | connector journey | binding model, Integrations engine | open-ended breadth → maturity levels bound it |

### 29.5 Gates G1–G8 — not negotiable

| Gate | Content | Platform evidence (tests / artefacts) |
|---|---|---|
| **G1 Licence / company truth** | LICENSE v6.2 with alran/GERMO/model names; third-party licence inventory + SBOM; consistent names | PAT-LEG-06, PAT-ARC-04, PAT-BTA-02 |
| **G2 Privacy / contracts** | AVV/TOM/subprocessor list (AI providers, OpenRouter with EU-only addendum Exhibit A, 2Captcha, channels); privacy notice; beta terms; deletion concept | PAT-LEG-01, -02, -04, -07; PAT-DAT-06 |
| **G3 Security** | tenant isolation (16/16 today in the test), auth/MFA, secrets, injection and cross-tenant fixtures | PAT-TEN-*, PAT-AUTH-*, PAT-SEC-*, PAT-AGT-07, PAT-MCP-03/-04 |
| **G4 Operations** | backup **with restore proof** (RPO ≤ 15 min / RTO ≤ 60 min as target), monitoring/alerting, incident owner, status page | PAT-REL-*, PAT-INF-*, PAT-AUD-02/-03 |
| **G5 Product paths** | acceptance against real DB + real UI (golden paths) **and** M1–M6 | PAT-BTA-03, PAT-BTA-04 |
| **G6 Terms** | one price/entitlement registry; beta free with hard per-company credit caps; website = checkout = invoice = docs = contract | PAT-CRD-01..07 |
| **G7 AI governance** | autonomy T0–T5 with company ceiling, kill switch, budgets, receipts, chatbot notice, injection gates | PAT-AUT-*, PAT-AGT-*, PAT-GWY-*, PAT-LEG-03, PAT-SEC-04 |
| **G8 Support / onboarding** | onboarding owner, support channel, docs/changelog | PAT-BTA-08, PAT-REL-07 |

### 29.6 Measurement before promises — week 1 (group G0)

The throughput of the build factory is **unmeasured**; any commitment before measurement is guessing. Week 1 runs the W0 repair jobs and records: time per task, gate pass rate, rework/failure rate by category, tokens/cost per task, merge-to-`main` stability. From these the forecast for the full task base (pack: 1,846 tasks + new families) is derived and reported with a range. **If 31.12.2026 does not fit, Willi decides:** move the date, pay for inference, or re-cut stages — nothing is dropped silently, and G1–G8 are never trimmed. (The deadline is cost-driven: free development inference ends with the year.) As of 19.10.2026 about **10 weeks** remain.

### 29.7 Users and terms ✅ D-14 🟠 D-21

First users are **own companies** (internal data), then **selected test customers** once the gates stand. The beta is **free**; Ottili bears the inference cost, hence hard per-company credit caps (§20.5). "31.12. = ready for own companies and first test customers, not a broad release" resolves the conflict with "no HQ release before January 2027". 🟡

### 29.8 Indicative backward plan 🟠 (replaced by the week-1 measurement)

| By | Target |
|---|---|
| ~25.10. | safeguards (Doc 3 §3.1), pack v2 reviewed, G0 started, throughput measured, first tranche of new job families written |
| ~15.11. | Platform boots on PostgreSQL; Auth/Company/Policy/Events/Jobs green; HQ/LD3 W0 green; Console shrunk |
| ~06.12. | product W1 chains (HQ, LD3), Flows/Approvals/Actions/Channel Port; first missions (M1, M4) in integration test |
| ~20.12. | M1–M6 in integration test; hardening: acceptance tests, restore drill, security review, beta documents, support/status |
| 20.–31.12. | buffer, freeze, invitation preparation (own companies first) |

### 29.9 Acceptance tests — beta readiness

| ID | Test |
|---|---|
| PAT-BTA-01 | The gate report links, for each gate G1–G8, the evidence bundle (test run IDs, commit, date); a gate without current evidence is red |
| PAT-BTA-02 | LICENSE v6.2 is present in the project and repositories and names alran, GERMO and the model names (file check + reviewer sign-off) |
| PAT-BTA-03 | The four golden paths run against real DB and real UI in CI with no mocks of Platform services |
| PAT-BTA-04 | M1–M6 meet the agreed success threshold with 0 policy violations over the agreed number of runs, including all negative cases |
| PAT-BTA-05 | Reports and receipts label statements as `observed`, `inferred` or `hypothesis` (schema lint) |
| PAT-BTA-06 | Plan lint: every own-build job begins with a build-vs-use review task (AR-28) |
| PAT-BTA-07 | Every capability has a completed definition-of-done checklist (AR-29, §31.4) before it is marked done |
| PAT-BTA-08 | A new test company is onboarded by checklist (account, company, plan, first data, first mission); support channel, changelog and status page exist |
| PAT-BTA-09 | The week-1 measurement report exists and is the basis for any date statement |

---

## 30. Migration from the current state

### 30.1 Starting point (R14, 14.10.2026 — to be re-verified by the repository check) 🟢

| Area | Finding |
|---|---|
| Golden paths | 0 of 4 run |
| Platform | does not build/boot on PostgreSQL; login and tenant isolation tests 16/16 pass |
| HQ | UI empty; order → payment works only after three patches |
| LD3 | 142 of 432 migrations refused; no WordPress connector; **no LLM call in code** |
| Console | all routes empty in the browser; 353k lines for ~10 pages |
| Duplicates | multiple owners alive for Auth, billing, registry (Foundation v2 §64) |

The founder believes almost all eight repositories fail and that HQ/LD3 do not run at all; this blueprint **does not rely on that claim**. The read-only repository check (Task 1) is still pending: it needs repository access and will refine G0 (the estimate of additional repair jobs).

### 30.2 Principles

1. **Strangler, not big bang:** a new owner takes over a capability behind a stable contract; the old implementation is removed only after its consumers moved.
2. **No two live owners** of one capability (AR-01); a temporary compatibility layer has an owner, an expiry date and a removal test.
3. **Archive first:** every replaced blueprint and legacy artefact is archived unchanged with a date; nothing is deleted until every row of Appendix G has a destination.
4. **Spec extraction before removal:** `alran-core-v2` and `alran-clients-v2` (R14 "remove candidates") are tagged and their specifications extracted (OpenAPI snapshot, 573 event/schema JSONs, module manifests, acceptance matrix, UX budgets) into the alran blueprint before leaving active lanes.
5. **Reality before refactoring:** repair (G0) precedes feature work; golden paths guard every extraction step.

### 30.3 Extraction sequence (by dependency)

1. **W0 repair:** Platform boots on PostgreSQL; HQ/LD3/Console build and start; migration health restored; secrets defaults removed.
2. **Identity and tenancy:** single Auth owner (Keycloak behind `auth.ottili.one`), `PlatformContext` everywhere, RLS adoption per table inventory.
3. **Registry:** products self-register with manifests; remove second registries (marketing/console/cloud).
4. **Actions:** HQ/LD3/apps register actions; UI paths call them (parity matrix); route inventory vs action registry gate.
5. **Cross-cutting consumption:** Flows, Approvals, Integrations, Search, Files, Notifications adopted by HQ/LD3/apps; delete product-private copies (HQ-W1-33/34/35, APP-W1-02/03/10 corrected).
6. **AI Gateway:** all model calls routed; direct SDK imports removed (scan gate).
7. **Operations + Channel Port + Ottili MCP.**
8. **Agent runtime adapters** (DeerFlow, Codex) and alran API & Console.
9. **`libs/common` decomposition and unified API migration:** split by owner into versioned packages; endpoints move behind the gateway with compatibility shims that expire (Foundation v2 §65/§66 → this section).
10. **Removal:** compatibility layers and legacy modules deleted on their expiry date after consumer-conformance green.

### 30.4 Repository targets

Repository roles per §2.3. The proposed `alran` repository receives adapters and UI semantics; `alranbot`/`synth` stay research/data lines outside the beta; the `skills` repository remains GERMO tooling. Cloud/deploy code that today lives in a broad `services/cloud` module is decomposed behind bounded controllers (§27.10) rather than preserved as a new monolith.

### 30.5 Pack and plan handling (GERMO)

The pack (242 plans / 1,846 tasks) is patched in **pack v2** (11 plans) per Doc 3 §3.2; 32 plans remain marked as needing a patch; new families `FB-01…FB-31` (three tranches) and `FS-01…FS-03` implement what the pack lacks (Operations, Channel Port, Ottili MCP, binding, agent governance, browser/CAPTCHA, connector mechanism, …), estimated 106–129 new jobs. G0 as sized by Willi: 30 jobs / 213 tasks (platform 10/73, hq-v2 6/38, ld3-v2 5/34, console-v2 4/24, ottili-apps 2/16, alranbot/synth/skills 3/28), to be enlarged by the repository check. **Nothing is imported, started or stopped without an explicit "go"; GERMO plans and prompts are English; the pack and its scripts are untrusted (read, never run).**

### 30.6 Acceptance tests — migration

| ID | Test |
|---|---|
| PAT-MIG-01 | After each extraction step the four golden paths still pass against real DB and UI |
| PAT-MIG-02 | A compatibility layer without owner and expiry date fails CI; an expired one fails the build until removed |
| PAT-MIG-03 | No capability has two live canonical implementations (registry + repository scan, see PAT-REG-03, PAT-INT-06) |
| PAT-MIG-04 | Spec extraction from the "remove candidate" repositories is complete (checklist over OpenAPI/events/manifests/acceptance matrix) before they leave active lanes |
| PAT-MIG-05 | Archive check: every replaced document exists unchanged in the archive with a date; every row of Appendix G has a destination |

---

## 31. Acceptance catalogue and definition of done

### 31.1 Conventions

Test IDs are `PAT-<AREA>-nn`. Each test states setup, action, expected result and evidence; evidence is bound to a commit and run ID. Levels: **unit** (logic), **contract** (producer/consumer), **integration** (real DB, real services), **e2e** (real browser/UI), **fault** (kill, outage, duplication), **security** (adversarial), **measurement** (load/cost). Tests of tenancy, authorisation, injection and money are never mocked at the Platform boundary.

### 31.2 Rule index — architecture rules → tests

| Rule | Tests |
|---|---|
| AR-01 | PAT-ARC-01, PAT-ARC-02, PAT-REG-03, PAT-INT-06, PAT-DAT-01 |
| AR-02 | PAT-ACT-01, PAT-ACT-09, PAT-FLW-05 |
| AR-03 | PAT-POL-02, PAT-AUT-03, PAT-ACT-08 |
| AR-04 | PAT-CTX-01, PAT-TEN-01, PAT-TEN-02, PAT-EVT-06 |
| AR-05 | PAT-AUT-01, PAT-AUT-07, PAT-CTX-04, PAT-SEC-04 |
| AR-06 | PAT-SEC-04, PAT-MCP-04, PAT-BRW-03, PAT-CHN-02 |
| AR-07 | PAT-EVT-01, PAT-EVT-02 |
| AR-08 | PAT-EVT-05, PAT-OPS-05, PAT-DAT-10, PAT-REL-04 |
| AR-09 | PAT-ACT-04, PAT-INT-02, PAT-AGT-04 |
| AR-10 | PAT-REG-01, PAT-POL-01, PAT-GWY-01, PAT-CTX-01 |
| AR-11 | PAT-SEC-01, PAT-SKL-02, PAT-BRW-04 |
| AR-12 | PAT-GWY-05 |
| AR-13 | PAT-GWY-01, PAT-GWY-02 |
| AR-14 | PAT-BND-01, PAT-BND-02 |
| AR-15 | PAT-INT-05 |
| AR-16 | PAT-AGT-05, PAT-AGT-10, PAT-AUTH-08 |
| AR-17 | PAT-AGT-07 |
| AR-18 | PAT-INF-01, PAT-SEC-06 |
| AR-19 | PAT-REL-01, PAT-REL-03 |
| AR-20 | PAT-ACT-03 |
| AR-21 | PAT-ACT-01, PAT-ACT-07, PAT-UX-05 |
| AR-22 | PAT-EVT-03, PAT-ARC-04 |
| AR-23 | PAT-BTA-05 |
| AR-24 | PAT-UX-02, PAT-ARC-05 |
| AR-25 | PAT-INF-08, PAT-INF-04, PAT-REL-04 |
| AR-26 | PAT-CRD-01, PAT-CRD-03, PAT-GWY-04, PAT-AUT-08 |
| AR-27 | PAT-AUT-05, PAT-AGT-09 |
| AR-28 | PAT-BTA-06 |
| AR-29 | PAT-BTA-07 |
| AR-30 | PAT-AUT-09 |

### 31.3 Chapter index

Landscape PAT-ARC/CTX/ZON (§2, §4) · Auth PAT-AUTH (§5) · Tenancy, policy PAT-TEN/POL (§6) · Registry, extensions, skills PAT-REG/EXT/SKL (§7) · Actions PAT-ACT (§8) · Autonomy PAT-AUT (§9) · Approvals, channels PAT-APR/CHN (§10) · Operations PAT-OPS (§11) · Flows PAT-FLW (§12) · Bindings, integrations PAT-BND/INT (§13) · MCP PAT-MCP (§14) · Gateway PAT-GWY (§15) · Agents PAT-AGT (§16) · Browser PAT-BRW (§17) · Events PAT-EVT (§18) · Data PAT-DAT (§19) · Credits PAT-CRD (§20) · Notifications, settings PAT-NTF/SET (§21) · Audit PAT-AUD (§22) · Legal PAT-LEG (§23) · Security PAT-SEC (§24) · Experience PAT-UX (§25) · API PAT-API (§26) · Infrastructure PAT-INF (§27) · Reliability PAT-REL (§28) · Beta PAT-BTA (§29) · Migration PAT-MIG (§30).

### 31.4 Definition of done for a capability (AR-29)

A capability is done only when it has: a named owner; API/event/job/data contracts registered; migration with rollback or documented no-rollback; authorisation and tenancy tests; security review items closed; observability (metrics, traces, logs, alerts) and an SLI where relevant; backup/restore semantics stated; deployment manifest; i18n complete for `de`/`en`; runbook; acceptance tests green with evidence; and — for any AI-facing capability — action definition, parity test, injection fixtures and cost class.

---

## 32. Risks, open decisions and architecture decision records

### 32.1 Decisions — state as used in this blueprint

| ID | State | Used here |
|---|---|---|
| D-01…D-05, D-09…D-12, D-14, D-17, D-19, D-20, D-22, D-29…D-32 | ✅ decided | applied as written (see Appendix E for locations) |
| D-06, D-07, D-08, D-13, D-15, D-16, D-21, D-23, D-24, D-25, D-27, D-33 | 🟠 proposed | applied as defaults and tagged 🟠 where they shape behaviour |
| **D-18** archive German old documents | 🔴 open | default: archive a copy outside the repositories; the five clean-up jobs (`PLT-W2-05`, `HQ-W2-06`, `LD3-W2-03`, `CON-W2-03`, `APP-W2-04`) stay held |
| **D-26** first bring-your-own-stack proof | 🔴 open | default: Microsoft 365 mail + calendar, federated; Odoo/cobra later; import starts with CSV/Excel |
| **D-28** legal without budget | 🔴 open | staged: hints only; own companies first; drafts + question list; one fixed-price review before external test customers |

Additional defaults chosen by this blueprint and flagged for Willi: company autonomy ceiling default **T3** 🟠 (§9.2); new external MCP clients start with read + draft toolsets 🟠 (§14.3); Ottili Cloud runtime for customers (managed WordPress, deploy integration) post-beta 🟠 (§27.10); simulated terminal, "Sign in with Ottili", white-label post-beta 🟠.

### 32.2 Risk register

| ID | Risk | Effect | Mitigation | Owner |
|---|---|---|---|---|
| RSK-01 | Scope versus time (≈ 10 weeks left) | gates missed | week-1 measurement; Willi decides date/cost/cut; gates never trimmed | Willi |
| RSK-02 | Verification is the bottleneck; free development model produces fragile code | rework, unstable `main` | independent review and gate tasks, protected paths, golden paths in CI | Willi / GERMO |
| RSK-03 | Tenant isolation in agent runtimes (DeerFlow has none documented) | cross-company leak | isolation before density, isolation suite as release gate, no credentials in sandboxes | Platform |
| RSK-04 | Beta on development infrastructure (D-20) | limited concurrency, weak HA | concurrency caps, restore drills, honest beta terms | Willi |
| RSK-05 | Model provider terms (Anthropic D.4, resale, training) | forbidden use | gateway flags, no Claude outputs in training data, counsel question list | Willi |
| RSK-06 | Cost of the free beta (Ottili pays inference) | budget overrun | hard caps, cost classes, cheapest eligible model, weekly cost review | Platform |
| RSK-07 | Harness dependency (DeerFlow v2 rewrite, Codex experimental protocol) | breakage on upgrade | adapter-first, pinning, contract tests, exit strategy | Platform |
| RSK-08 | Legal exposure without budget | unreviewed claims | `UNVERIFIED` registry, staged review, honest claims (P11) | Willi |
| RSK-09 | Browser/CAPTCHA terms violations | account bans, liability | blocklist, approved-domains default, API first | Platform |
| RSK-10 | Approval fatigue | rubber-stamping | typed risk classes, few well-chosen approval points, digests | Platform |
| RSK-11 | Duplicate owners remain alive during migration | divergence | strangler rules, PAT-MIG-03, dependency registry | Platform |
| RSK-12 | Single-founder capacity | decision latency | decisions batched in short questions; defaults documented so work continues | Willi / Claude |
| RSK-13 | Backup/restore unproven | irrecoverable loss | AR-19 drills, G4 | Platform |
| RSK-14 | Identity engine operational weight | auth outages | adapter + exit strategy, monitoring, backups of realm config | Platform |
| RSK-15 | Connector breadth open-ended | endless work | maturity levels, generic mechanism, BYO proof only | Platform |
| RSK-16 | Competitor/market claims unverified | wrong positioning | hypotheses until REA/clean-room (D-25) | Willi |

### 32.3 Architecture decision records to open (evidence required before lock)

| ADR | Question | Evidence required |
|---|---|---|
| ADR-P-01 | Event transport after the PostgreSQL outbox | sustained events/s, backlog and replay latency, operating cost |
| ADR-P-02 | Durable workflow runtime for Flows: own implementation vs adopting an existing engine (AR-28 review first) | licence, maturity, multi-tenancy, operating cost, fit to node contract |
| ADR-P-03 | Search engine beyond PostgreSQL full-text | corpus size, query latency, saturation |
| ADR-P-04 | Object storage implementation (self-hosted S3-compatible vs provider) | node qualification vs provider economics and durability |
| ADR-P-05 | Off-site backup provider | restore throughput, immutability, cost, jurisdiction |
| ADR-P-06 | Secrets backend maturity (Infisical-class vs alternatives) | `SecretRef` integration, rotation/audit needs, portability |
| ADR-P-07 | Agent runtime pooling vs dedicated instances | isolation suite results, density, cost |
| ADR-P-08 | Codex wire format (`wire_api`/Responses) and gateway compatibility | Codex source and release notes, conformance run |
| ADR-P-09 | PostgreSQL replica/failover tool and fencing | DB size/WAL, RPO/RTO drills |
| ADR-P-10 | Runtime scheduler beyond the node agent | node count, workload churn, bin-packing/HA needs |
| ADR-P-11 | Policy engine implementation (embedded evaluator vs external) | decision latency, expressiveness, test tooling |

### 32.4 Open verifications (hints, not advice) 🔴

Codex `wire_api` against source and release notes · Kleinanzeigen § 5 full text · AliExpress developer portal terms and regions · 2Captcha privacy/DPA · fallback model licences (DeepSeek-V4-Flash, GLM-5.3-Flash — claimed MIT, unverified) · Odoo official MCP · eBay original terms and APIs · competitor/market statements (REA) · build-vs-use candidates · AI Act guidance and marking practice · Sonnet 5.5 (Vertex EU) in the OpenRouter EU region list as in-region **and** ZDR-capable (`/api/v1/models`) · the pasted price/latency figures (unverified; check against the live price page) · interpretation of the Anthropic clause for alran AI/Code · content of LICENSE 6.2 · WhatsApp as approval channel (Meta business verification, templates, cost) · hosting or using models in China for public tasks.

---
## Appendix A — Glossary and naming

| Term | Meaning |
|---|---|
| **Binding** | per company and entity: provider, mode (Native · Mirror · Federated · Migration), system of record per field group, conflict policy, maturity 0–3 (§13) |
| **SoR** | system of record — the leading system for an entity/field group |
| **Business graph** | canonical objects (party, product/variant/BOM, quote/price, order, stock/location/movement, invoice/payment, shipment, task, document, message, content, campaign) with `external_refs[]` |
| **Action / effect class / receipt / grant** | §8 |
| **Autonomy level T0–T5 / ceiling** | policy template over grants, approval and budget / the maximum a company allows (§9) |
| **Mission** | durable Platform object for an agent task (§16.3) |
| **Harness / adapter-first** | ready-made agent frame (DeerFlow, Codex) / thin integration without fork (§16.4) |
| **Business case (German "Vorgang") / Operations inbox** | cross-system business case / queue of decisions, exceptions, proposals, drafts (§11) |
| **Channel Port** | Platform interface for approvals and notifications; channels are adapters (§10.3) |
| **Build stage BP-0…BP-6 / Gate G1–G8 / Missions M1–M6** | §29 |
| **Golden path** | acceptance path against real DB and real UI |
| **ZDR** | zero data retention at the model provider |
| **REA / clean room** | competitor analysis as inspiration without code or assets |
| **Truth-kit** | GERMO gate tooling (preflight, gate, safe-commit, `TRUNK_STATUS.json`) — untrusted input when it comes from the pack |

Valid names: Ottili (umbrella) · **Ottili ONE** (HQ + LD3) · **Ottili Platform** (control plane) · **Ottili Console** (admin UI of the Platform) · **alran AI** · **alran Code** · **alran API & Console** · alran in HQ/LD3 · Ottili Research Labs · GERMO. History: Rooke → Alrun → alran. Dead names (CI grep gate PAT-ARC-04): `platform.ld3`, `rooke.`, `login.ottili.one`, "alran Chat", "alran Work", "Rooke Platform", "Otily". "Ottili Console" ≠ "alran Console".

---

## Appendix B — Event catalogue seed

Naming: `<namespace>.<entity>.<verb>.v<N>` (D-13 🟠). Owners register schemas (§18.3).

| Namespace | Events (seed) |
|---|---|
| `platform.auth` | `login_succeeded.v1`, `login_failed.v1`, `token_reuse_detected.v1`, `session_revoked.v1`, `stepup_completed.v1`, `mfa_changed.v1`, `recovery_started.v1` |
| `platform.company` / `platform.membership` | `company.created.v1`, `company.suspended.v1`, `company.deletion_started.v1`, `company.deleted.v1`, `membership.changed.v1` |
| `platform.entitlement` / `platform.policy` | `entitlement.changed.v1`, `policy.changed.v1`, `autonomy.ceiling_changed.v1`, `grant.created.v1`, `grant.revoked.v1`, `kill_switch.triggered.v1` |
| `platform.action` / `platform.approval` | `action.executed.v1` (receipt created), `action.failed.v1`, `approval.requested.v1`, `approval.decided.v1`, `approval.expired.v1`, `approval.escalated.v1` |
| `platform.case` / `platform.inbox` | `case.opened.v1`, `case.updated.v1`, `case.closed.v1`, `inbox.item_created.v1`, `inbox.item_resolved.v1` |
| `platform.flow` | `run_started.v1`, `run_waiting.v1`, `run_completed.v1`, `run_failed.v1`, `run_compensated.v1` |
| `platform.binding` / `platform.integration` | `binding.degraded.v1`, `binding.recovered.v1`, `binding.cutover_phase_changed.v1`, `integration.webhook_received.v1`, `integration.reconciliation_diff.v1` |
| `platform.credits` | `reserved.v1`, `settled.v1`, `released.v1`, `cap_reached.v1` |
| `platform.signal` | `signal.created.v1`, `signal.feedback_recorded.v1` |
| `alran.mission` | `created.v1`, `state_changed.v1`, `completed.v1`, `budget_exhausted.v1`; `alran.proposal.created.v1` |
| `one.hq` | `order.confirmed.v1`, `order.cancelled.v1`, `stock.movement_recorded.v1`, `stock.deviation_detected.v1`, `product.revised.v1`, `purchase_order.submitted.v1`, `goods_receipt.posted.v1`, `invoice.issued.v1`, `payment.received.v1`, `return.requested.v1` |
| `one.ld3` | `content.review_requested.v1`, `content.published.v1`, `content.flagged_stale.v1`, `content.revalidated.v1` |

The staleness loop S1 (D-32): `one.hq.product.revised.v1` → LD3 marks dependent content `flagged_stale` → revalidation → approval.

---

## Appendix C — Seed action catalogue (carries M1–M6; target ≈ 30–40 first actions)

Effect classes: R read · D draft · I internal change · E external change · X destructive. "Max default" = highest level at which the action may run without approval unless the company raises it (§9.2). All actions have `tool_export`, receipt and kill-switch group.

| Action | Owner | Class | Risk | Max default | Dry-run | Verification | Missions |
|---|---|---|---|---|---|---|---|
| `crm.organization.get` / `list` | one.hq | R | low | T5 | – | – | M3, M6 |
| `crm.contact.create` | one.hq | I | low | T2 | ✔ | read-back | M5, M6 |
| `crm.organization.create` / `update` | one.hq | I | low | T2 | ✔ | read-back | M1 |
| `catalog.product.create_draft` | one.hq | D | low | T1 | ✔ | read-back | M1 |
| `catalog.product.create` | one.hq | I | medium | T2 | ✔ | read-back | M1 |
| `catalog.product.publish` | one.hq | E | medium | T3 | ✔ | provider receipt | M1, M5 |
| `channel.listing.create_draft` (Shopify draft) | app.shopify | E→D | low | T1 | ✔ | provider receipt | M1 |
| `sales.quote.create_draft` | one.hq | D | low | T1 | ✔ | read-back | – |
| `sales.order.get` / `list` | one.hq | R | low | T5 | – | – | M2, M3, M4 |
| `sales.order.create` | one.hq | I | medium | T2 | ✔ | read-back | M2 |
| `inventory.stock.get` | one.hq | R | low | T5 | – | – | M2, M4 |
| `inventory.stock.reserve` | one.hq | I | medium | T2 | ✔ | ledger check | M2 |
| `inventory.stock.adjust` | one.hq | I | high | T2 (rules) | ✔ | ledger check + reconciliation | M4 |
| `binding.reconcile.run` | platform | R/D | low | T1 | ✔ | diff report | M4 |
| `purchasing.po.create_draft` | one.hq | D | low | T1 | ✔ | read-back | M2 |
| `purchasing.po.submit` | one.hq | E | high | T4 (limits) | ✔ | supplier confirmation | M2 |
| `purchasing.supplier_order.place` | app.dropshipping | E | high | T4 (limits) | ✔ | provider receipt | M2 |
| `purchasing.supplier_status.get` | app.dropshipping | R | low | T5 | – | – | M3 |
| `tasks.task.create` | one.hq | I | low | T2 | ✔ | read-back | M3 |
| `mail.message.draft` | app.mail | D | low | T1 | ✔ | read-back | M3, M6 |
| `mail.message.send` | app.mail | E | medium | T3 | ✔ | provider receipt | M3, M6 |
| `sales.credit_note.create_draft` | one.hq | D | medium | T1 | ✔ | read-back | M6 |
| `sales.credit_note.issue` | one.hq | E | high | T3 + step-up above limit | ✔ | ledger + document check | M6 |
| `finance.invoice.issue` | one.hq | E | high | T3 | ✔ | document hash | – |
| `ld3.topic.create` | one.ld3 | I | low | T2 | ✔ | read-back | M5 |
| `ld3.research.run` | one.ld3 | R/D | medium (cost) | T2 | ✔ | evidence count | M5 |
| `ld3.content.create` | one.ld3 | D | low | T1 | ✔ | read-back | M5 |
| `ld3.content.review` | one.ld3 | I | low | T2 | – | findings stored | M5 |
| `ld3.content.publish` | one.ld3 | E | medium | T3 | ✔ | provider receipt (WordPress) | M5 |
| `ld3.content.revalidate` | one.ld3 | I | low | T2 | ✔ | read-back | S1 |
| `flows.pipeline.create` / `activate` | platform | I | medium | T2 / T3 | ✔ | read-back | – |
| `flows.pipeline.execute` / `status.get` | platform | per flow / R | per flow | per flow | ✔ | run record | all |
| `notifications.send` | platform | E | low | T3 (T4 within caps) | ✔ | delivery receipt | M3, M5 |
| `approvals.request.create` | platform | I | low | T5 | – | read-back | M2, M5, M6 |
| `ops.case.get` / `explain` / `inbox.list` | platform | R | low | T5 | – | – | M4 |
| `mission.create` / `cancel` | platform | I | medium | T2 | – | state check | all |
| `autonomy.ceiling.set` | platform | I | critical | **T0 (humans only; step-up)** | – | read-back | – |
| `agent.kill_switch.trigger` | platform | I | critical | humans only | – | state check | – |
| `export.company.create` | platform | R/I | high | T3 + step-up | ✔ | manifest hash | – |
| `company.delete` | platform | X | critical | T3 → S | ✔ | saga evidence | – |

Parity rule: for each action the UI path and the action path return identical validation errors (PAT-ACT-01). The exhaustive catalogue (target: every UI function) is generated from registered definitions; this table fixes the **seed**.

---

## Appendix D — Error code catalogue (machine codes, Problem Details `code`)

| Code | HTTP | Retryable | Meaning |
|---|---|---|---|
| `tenant_context_missing` | 400 | no | no verified company context |
| `unauthenticated` | 401 | after login | missing/expired credentials |
| `policy_denied` | 403 | no | policy decision deny; carries `reason_code` |
| `entitlement_missing` | 403 | no | capability not in plan/grants |
| `step_up_required` | 401/403 | after step-up | fresh strong authentication needed |
| `approval_required` | 202/409 | after approval | action waits for a human decision |
| `autonomy_too_low` | 403 | no | effective level does not permit execution (P/X in §9.3) |
| `budget_exhausted` | 402/429 | after top-up | credit cap or reservation exceeded |
| `no_eligible_model` | 503 | maybe | no endpoint satisfies data-class/region/policy |
| `revision_conflict` | 409 | after re-read | stale `If-Match`/revision |
| `idempotency_conflict` | 409 | no | same key, different payload |
| `unsupported_by_provider` | 422 | no | binding lacks the capability → human task |
| `unknown_external_result` | 202 | after reconciliation | external outcome unclear; reconciling |
| `validation_failed` | 422 | no | schema/field errors listed |
| `rate_limited` | 429 | yes | back off per `Retry-After` |
| `deadline_exceeded` | 504 | maybe | request deadline passed |
| `kill_switch_active` | 423 | after release | group/company kill switch engaged |
| `not_found` | 404 | no | also used for foreign-tenant resources (no existence leak) |
| `dependency_degraded` | 503 | yes | binding/provider degraded; staleness indicated |

---

## Appendix E — Decision traceability

| Decision | Where applied |
|---|---|
| D-01 beta definition, scope, M1–M6, gates | §29 |
| D-02 provider binding | §13, AR-14 |
| D-03 core/bundled/app | §7.2 |
| D-04 names | §2.1, §2.2, Appendix A |
| D-05 adapter-first | AR-16, §16.4 |
| D-06 own models | §15.3, §15.4 (flags); detailed in Research Labs blueprint |
| D-07 CAPTCHA default | §17.4 |
| D-08 Kleinanzeigen/eBay/AliExpress | §13.7, §17.3 |
| D-09 AI marking switch | §23.3 |
| D-10 Channel Port | §10.3 |
| D-11 autonomy T0–T5 | §9 |
| D-12 Keycloak behind `auth.ottili.one` | §5.1 |
| D-13 event layer | §18.1 |
| D-14 free beta, one price registry | §20.4, §20.5 |
| D-15 self-hosting | §27.10 |
| D-16 performance | §25.8, §27.9 |
| D-17 GERMO to `main` | §27.8, §24.7 |
| D-18 archive German docs (open) | §30.2, §32.1 |
| D-19 name clean-up, LICENSE 6.2 | §23.7, Appendix A |
| D-20 servers are dev infrastructure | §27.1, §27.4 |
| D-21 first users | §29.7 |
| D-22 dev instance untouched | §27.4 |
| D-23 OSS apps | §7.8 |
| D-24 alran Code IDE | alran blueprint |
| D-25 REA programme | §23.8, §32.4 |
| D-26 first BYO proof (open) | §13.11 |
| D-27 tenant-private apps | §7.6 |
| D-28 legal without budget (open) | §23.1, §32.1 |
| D-29 Ottili MCP per company | §14 |
| D-30 Operations | §11 |
| D-31 build vs use | AR-28 |
| D-32 staleness loop S1 | Appendix B, §29.4 BP-2 |
| D-33 model/data policy | §15.3–§15.5 |

---

## Appendix F — Source register (external facts and checks)

Retrieved 18.10.2026 (Doc 2 §9). Confidence: 🟢 primary source/wording · 🟡 secondary or excerpt · 🔴 contradictory or unconfirmed. Hints, not legal advice.

| ID | Topic | Core statement | Confidence | Used in |
|---|---|---|---|---|
| D1 | DeerFlow 2.0 | MIT; LangGraph-based harness, lead + sub-agents, sandboxes (local/Docker/Kubernetes/E2B), skills (`SKILL.md`, not a hard security boundary), MCP stdio + HTTP/SSE, authorisation off by default, no inbound webhooks, ≥ 8 vCPU/16 GB | 🟢 | §16.4 |
| D2 | Codex | Apache-2.0; `codex app-server` JSON-RPC over stdio, experimental for product integrations; approvals and sandbox modes | 🟢 licence / 🟡 protocol | §16.4 |
| D3 | AI Act Art. 50 status | applies since 02.08.2026; grace for legacy marking until 02.12.2026 (secondary) | 🟡 | §23.3 |
| D4 | eBay | terms update (20.01.2026): buy agents/LLM bots without human review before ordering prohibited | 🟡 | §17.3 |
| D5 | EU Data Act | switching rules since 12.09.2025; switching/egress charges phased out from 12.01.2027; structured machine-readable export via open APIs | 🟡 | §13.9, §23.9 |
| D7 | Qwen model cards | Qwen3.8-27B Apache-2.0; Qwen3.8-Flash-Next "other" licence | 🟢 | §23.7 |
| D8 | DeerFlow addendum | per-user scoping, no documented tenant-wide isolation | 🟢 | §16.4 |
| D9 | Codex configuration | `approval_policy`, `sandbox_mode`, `model_providers.<id>`, `mcp_servers`, user-level only; `wire_api` not found in reference, secondary source says Responses-only | 🟢 config / 🔴 `wire_api` | §15.2, §16.4 |
| D10 | Kleinanzeigen | § 5 No. 1 forbids crawlers/scrapers and circumventing access protection without written consent (excerpt) | 🟡 | §17.3 |
| D11 | AliExpress | official dropshipping interfaces (e.g. `aliexpress.ds.order.create`), access after approval, regional limits | 🟡 | §13.7 |
| D12 | 2Captcha | per-1,000 prices; AI first, humans for low confidence; ToS: authorised and legal purposes only, user responsible | 🟢 | §17.4 |
| D13 | cobra CRM | "Cobra CXM Web Connect" Windows service with API key and endpoint token | 🟡 | §13.10 |
| D14 | Odoo MCP | community servers; official MCP not confirmed | 🟡 | §13.7 |
| D15 | AI Act Art. 50 wording | 50(1) notice; 50(2) machine-readable marking; 50(4) disclosure for AI text of public interest unless human review/editorial responsibility | 🟢 | §23.3 |
| D16 | Qwen Community License 1.0 | separate licence for "Model as a Service"/"AI Work Assistant" | 🟢 | §23.7 |
| D17 | Anthropic Commercial Terms D.4 | no building competing products, training competing models, or reselling without approval (interpretation open) | 🟢 wording / 🔴 interpretation | §15.10, §23.8 |
| D18 | OpenRouter region routing | `eu.openrouter.ai` in-region only, fail-closed; ZDR and `data_collection` compatible; non-regional features; DPA with SCC; Exhibit A only by written choice | 🟢 | §15.5 |

Internal sources: Doc 1 (consolidated foundation, v2), Doc 2 (analysis, gaps, assessments), Doc 3 (pack verdict), R14 inventory of 14.10.2026, the founder's voice dump of 17.10.2026 (items VD-xx), the replaced blueprints (Appendix G). Open checks: §32.4.

---

## Appendix G — Where the replaced blueprints went

Both replaced documents are **archived unchanged first**; a row is complete only when its destination exists. Section numbers refer to the original documents.

### G.1 `OTTILI_PLATFORM_INFRASTRUCTURE_MASTER_BLUEPRINT.md`

| Original | Destination | | Original | Destination |
|---|---|---|---|---|
| 1 Authority | §0 | | 46 Load balancing | §27.9 |
| 2 Summary, 3 Mission | §1 | | 47 Capacity management | §27.9, §28.9 |
| 4 Non-goals | §1.4 | | 48 Autoscaling | §27.9 |
| 5 System context | §4.1 | | 49 Failure domains | §28.1 |
| 6 Environments | §27.1 | | 50 Backup | §28.2 |
| 7 Network | §4.3, §27.2 | | 51 Restore | §28.3 |
| 8 Edge/CDN/DNS | §27.2 | | 52 Disaster recovery | §28.4 |
| 9 API gateway | §26, §27.3 | | 53 HA roadmap | §28.5 |
| 10 Authentication | §5 | | 54 Maintenance | §28.5 |
| 11 Authorization | §6.3 | | 55 Security architecture | §24 |
| 12 Multi-tenancy | §6.5 | | 56 Internal admin access | §6.7, §24.1 |
| 13 Entitlements | §6.4 | | 57 CI/CD | §27.5 |
| 14 Billing | §20.6 | | 58 Testing infrastructure | §31 |
| 15 Usage/credits | §20 | | 59 Performance testing | §25.8, §27.9, PAT-INF-08 |
| 16 Product registry | §7.1 | | 60 Security validation | §24.10 |
| 17 Service architecture | §2.5, §27.3 | | 61 Cost model | §28.9, §20 |
| 18 Service-to-service | §4.5, §24.2 | | 62 Resource quotas | §20.3, §26.7 |
| 19 Data architecture | §19.1–§19.4 | | 63 Provider failure strategy | §15.6, §28.7 |
| 20 PostgreSQL | §19.1, §19.2, §6.5 | | 64 Rate limits | §26.7 |
| 21 Redis | §18.5, §19.7 (Valkey) | | 65 Data retention | §19.9 |
| 22 Event platform | §18 | | 66 Privacy/deletion | §19.9, §23.4 |
| 23 Job platform | §18.5 | | 67 Operational tooling | §28.8 |
| 24 Flow runtime | §12 | | 68 Incident management | §24.9, §28.8 |
| 25 Files | §19.5 | | 69 Runbooks | §28.8 |
| 26 Search | §19.6 | | 70 SLO/SLI | §28.6 |
| 27 Notifications | §21.1 | | 71 Dashboards | §27.6 |
| 28 Approvals | §10 | | 72 Logging | §24.5 |
| 29 Audit | §22 | | 73 Tracing | §24.5, §27.6 |
| 30 Secrets | §24.3 | | 74 Metrics | §27.6 |
| 31 Configuration | §21.2, §27.7 | | 75 Version/compatibility | §26.1, §26.6 |
| 32 Observability | §24.5, §27.6 | | 76 Developer experience | §26.10 |
| 33 Health/degradation | §27.6, §28.7 | | 77 Local/dev/prod parity | §27.1 |
| 34 Status | §28.8 | | 78 Deprecation | §26.1 |
| 35 Deployment | §27.5 | | 79 Legacy migration | §30 |
| 36 Artifacts | §24.7, §27.5 | | 80–82 Topologies | §27.4 (today), §27.9 (growth) |
| 37 Release management | §27.5, §27.8 | | 83 Bottlenecks | §27.9 |
| 38 Migration model | §19.2 | | 84 Failure mode catalogue | §28.7 |
| 39 Ottili Cloud runtime | §27.10 | | 85 Acceptance tests | §31, PAT-INF/REL |
| 40 Rooke Deploy integration | §27.10 (alran Code deploy client, post-beta) | | 86 Definition of done | §31.4 |
| 41 Managed WordPress | §27.10 (post-beta) | | 87 Deferred infrastructure | §27.10 |
| 42 Provider abstraction | §15.9, §27.10 | | 88 Open decisions | §32.3 |
| 43 Server/node model | §27.4 | | 89 Risks | §32.2 |
| 44 Multi-server scaling | §27.9 | | 90 Target end state | §1, §27.9, §28.5 |
| 45 Service discovery | §27.9 | | Appendices A–C | diagrams embedded; source register → App. F; interpretation → §0.2 |

### G.2 `OTTILI_VNEXT_FOUNDATION_V2_MASTER_BLUEPRINT.md`

| Original | Destination | | Original | Destination |
|---|---|---|---|---|
| 1–2 Summary, mission | §1 | | 46 Templates and recipes | §12.5 |
| 3–4 Repository reality, v1 assessment | §30.1 | | 47 Public websites | outside Platform: LD3 publishing, Shop app, product sites (HQ/LD3 blueprints) |
| 5 Product model | §2.1 | | 48 Documentation system | §26.10 (docs generated from OpenAPI/manifests) 🟡 |
| 6 Platform definition | §2, §4 | | 49 Foundation Lab | §25.2 (component workbench) |
| 7 Ottili ONE | §2.1; HQ/LD3 blueprints | | 50 Customization / white label | §25.2 (post-beta beyond logo/accent) |
| 8 Rooke definition | alran blueprint | | 51 AI-native foundation | AR-05/06/12/13/20/21, §8, §15, §16, §24.8 |
| 9 Cloud/deployment | §27.10 | | 52 Skills, machine-readable metadata | §7.9, §8.7 |
| 10 Repository boundaries | §2.3 | | 53 Foundation TUI | deferred (post-beta developer convenience; alran Code CLI covers) 🟠 |
| 11 Monorepo structures | §2.3, §2.5 (layout detail in repository READMEs) 🟡 | | 54 Performance architecture | §25.8, §27.9 |
| 12 Ownership | §2.4 | | 55 Accessibility | §25.7 |
| 13 Dependency rules | §2.5 | | 56 Responsive behaviour | §25.7 |
| 14 Foundation v2 definition | §25, §26 | | 57 Internationalisation | §25.9 |
| 15 Frontend packages | §25.2, §26.10 | | 58 Testing architecture | §31 |
| 16 Backend foundation | §4.2, §27.3 | | 59 Consumer conformance | §26.6 |
| 17 Platform APIs | §26 | | 60 Versioning | §26.1 |
| 18 Contracts and SDKs | §26.6, §26.10 | | 61 Release, CI, deployment | §27.5 |
| 19 Product manifest | §7.3 | | 62 Security architecture | §24 |
| 20 App manifest | §7.3 | | 63 Multi-tenancy | §6.5 |
| 21 Extension runtime | §7.5 | | 64 Legacy inventory | §30.1 |
| 22 HQ app runtime | §7.5; HQ blueprint | | 65 `libs/common` decomposition | §30.3 |
| 23 Third-party extensions | §7.5–§7.7 | | 66 API/unified API migration | §30.3 |
| 24 Marketplace | §7.7 | | 67 ONE migration | §30.3; HQ/LD3 blueprints |
| 25 Bootstrap | §25.4 | | 68 Rooke migration | alran blueprint; §30.3 |
| 26 Auth and session | §5 | | 69 Platform extraction | §30.3 |
| 27 Company context | §4.5, §6.1 | | 70 Migration dependency graph | §30.3 |
| 28 Permissions/entitlements | §6.2–§6.4 | | 71 Compatibility layers | §30.2 |
| 29 Console integration | §25.10 | | 72 Removal plan | §30.3 step 10 |
| 30 Files | §19.5 | | 73 Implementation streams | §29.4 (build stages replace streams) |
| 31 Flows | §12 | | 74 Acceptance criteria | §31 |
| 32 Search | §19.6 | | 75 Risks | §32.2 |
| 33 Commands and actions | §8 | | 76 ADRs/spikes | §32.3 |
| 34 Settings | §21.2 | | 77 Repository evidence index | App. F (internal sources), R14 archive |
| 35 Notifications/approvals | §10, §21.1 | | 78 Final target architecture | §4 |
| 36 Errors/degraded states | §26.2, §28.7 | | 79 Data lifecycle | §19.9 |
| 37 Events | §18 | | 80 Privacy and data rights | §23.4 |
| 38 OOIE integration | §18.7 | | 81 Legal/compliance | §23 |
| 39 Observability | §24.5, §27.6 | | 82 Product-to-contract model | §20.4, §23.2 |
| 40–42 Design language, tokens, components | §25.2 | | 83 AI regulatory layer | §23.3 |
| 43 Enterprise patterns | §25.3; HQ blueprint | | 84 OSS and supply chain | §23.7, §24.7 |
| 44 Dashboard runtime | §11.5, §25.3 | | 85 Git branch model | §27.8 |
| 45 Widgets | §7.3 (widget contribution) | | 86 Delivery ownership | §2.4, §32.2 |
| | | | 87 Operational readiness | §28.8, §29.5 (G4, G8) |
| | | | 88 Strategic sequencing | §29.4 |
| | | | 89 Contradiction resolution | Doc 2 §6 |
| | | | 90 Binding final decision | superseded by Doc 1 §5 and §0.1 |

**End of document.**
