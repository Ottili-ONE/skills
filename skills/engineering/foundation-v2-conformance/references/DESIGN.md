# foundation-v2-conformance — Design

## Trigger description (draft)
Fires when: an agent imports, styles, or composes anything from the Ottili Foundation UI
packages (`@ottili/foundation-*`), builds a new page/component on top of them, or reviews a
PR for Foundation usage. Also fires when a build/test reports a missing or mismatched
Foundation dependency, a CSS variable that does not exist in the token set, or an a11y failure
attributed to a Foundation component.
Does NOT fire for: plain HTML/CSS without Foundation, third-party component libraries, or
Foundation v1 migration advice (pin the version; this skill is v2).

## Procedure outline
1. Pin the Foundation package versions in package.json; never allow `^` ranges on Foundation
   packages in a locked-release lane (FREEZE rule).
2. Import components and tokens from the package entry points only — never re-export or
   copy source into the consuming app.
3. Use the token set for spacing, type, and colour; a raw value that is not in the token file is
   a defect, not a workaround.
4. Mark workarounds explicitly with a `data-ottili-workaround` attribute and a comment naming
   the ticket; workarounds without a ticket are bugs.
5. Run the fresh-consumer test: a minimal app that imports the component and renders it with
   only the documented props; if it fails, the public API has drifted.
6. Record conformance in the component's test file with the exact Foundation version asserted.

## Scripts (shipped)
- `scripts/check_foundation_tokens.py` — validates that every raw design value used in CSS/JS
  resolves to a token in the Foundation token file; `ALLOWED` comment lines are exempt.
  Self-tested via `check_foundation_tokens_test.py`.
- `scripts/fresh_consumer_test.sh <component> <outdir>` — builds a throwaway app that imports a
  named Foundation component and asserts it renders with documented props only.

## Five eval prompts
1. "Add a settings page using the Foundation `Tabs` and `Select` components. The designer gave me
   hex colours `#1a1a1a` and `#3a8a6c`." → agent must map colours to tokens or flag them as
   custom and request a token addition; must not hardcode.
2. "The build fails: `Cannot find module '@ottili/foundation-button/dist/index'`." → agent must
   import from the package root, not the deep path, and check the version pin.
3. "My PR uses `data-ottili-workaround` to hide a layout bug." → agent must require a ticket
   reference in the attribute/comment or reject the workaround.
4. "Write a test proving the Foundation `Modal` still opens with only the documented props."
   → fresh-consumer test; must not depend on internal state.
5. "Foundation v2.4.1 is out; should we bump?" → agent must check the Freeze notice in
   `docs/STATUS_ALL.md` and refuse to bump without integrator approval.

## What this skill does better than existing public skills

- Existing: the Foundation Framework's own READMEs and the SoT blueprint are reference material
  for humans, not agents. Public "component library" skills (e.g. in anthropics/skills,
  openai/skills, community collections) are generic and name no concrete package, so they
  cannot detect a deep import or a token drift.
- Difference: this skill pins the *exact published version* (1.0.13 at retrieval time, with the
  1.0.11.1/1.0.12/1.0.1-1.1 corruption history recorded so an agent never installs a bad
  version), enforces the package's `exports` map (no deep imports such as
  `@ottili/foundation-ui/dist/index`), treats every raw design value as a defect unless it
  resolves to a token, makes workarounds ticket-bound, and ships a fresh-consumer test that
  proves the public API has not drifted — rather than advising "use the component correctly".
