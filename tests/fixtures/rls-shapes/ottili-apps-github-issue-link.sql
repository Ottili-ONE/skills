-- Expand step for BACKLOG B4: the one row this app writes today.
--
-- `github_issue_link` is the projection behind three built contributions: the sync action and the
-- link-issue command write it (both through `writeLink` in `src/handlers.mjs`), and the custom
-- fields, the record section and the report read it. Until this table exists, `src/ports.mjs` has an
-- interface and a refusing default and nothing behind them — `BACKLOG.md` B2/B4, `docs/platform-gaps.md`
-- entry 43.
--
-- The key is `(company_id, repository, issue_number)`, and it is an **upsert** rather than an append
-- for the reason `ports.mjs` gives: the idempotency store settles one key, so two different keys
-- naming the same issue are two reads of one fact and have to end in one row. A store that appended
-- would answer "which of these four syncs is the truth" with "all four, in the order they arrived".
--
-- The column list is `ISSUE_LINK_FIELDS` from `src/mapping.mjs`, in that order, and `test/data.test.mjs`
-- compares the two in both directions: a row field the table does not have is a write that fails in
-- production on a column nobody migrated, and a column the mapping never fills is a promise the
-- manifest makes to the platform and nobody keeps.
--
-- Additive only: nothing here drops, renames or narrows. The contract step (dropping
-- `idempotency_key` once retention no longer reads it) is a separate, deliberately absent decision.

CREATE TABLE IF NOT EXISTS public.github_issue_link (
  -- The tenant is the first column of the key and NOT NULL. NOT NULL is not decoration:
  -- `secureSchema` in `packages/service-runtime/src/postgres.mjs` only creates a policy for a table
  -- whose `company_id` is NOT NULL, so a nullable tenant would silently cost this table its
  -- row-level security and nothing would report the loss.
  company_id   TEXT   NOT NULL,
  -- `owner/name`, verbatim as GitHub spells it. The pattern that admits it lives in
  -- `src/provider.mjs` (`isRepository`) and is checked again by `mapping.linkView` on the way out,
  -- so a row that reached the table by another road still has to survive the reader.
  repository   TEXT   NOT NULL,
  -- `BIGINT`, not `INTEGER`: GitHub's issue numbers are 64-bit on the wire and the app refuses
  -- anything above `ISSUE_NUMBER_MAX` rather than truncating. `pg` hands a `BIGINT` back as a
  -- **string** to avoid precision loss, and the row contract in `mapping.mjs` wants a number — so
  -- `src/stores.mjs` is where that string becomes a number, and `test/sql-world.mjs` models the
  -- driver rather than the wish.
  issue_number BIGINT NOT NULL,
  title        TEXT,
  -- `open` or `closed`, the two of `ISSUE_STATES`. A CHECK, because the reader (`linkView`) refuses
  -- anything else and a row that cannot be read is a row that was stored for nothing.
  state        TEXT   NOT NULL CHECK (state IN ('open', 'closed')),
  -- The browser URL, not the API URL: this string is the one a person follows.
  url          TEXT,
  author       TEXT,
  -- Sorted and de-duplicated by `mapping.labelNames`, and JSONB because a label list is a list and
  -- a TEXT column would make "the same labels in another order" a difference.
  labels       JSONB  NOT NULL DEFAULT '[]'::jsonb,
  -- The Alran half of the link. Nullable on purpose: `github.action.sync-issue` may sync an issue
  -- before somebody has linked it to a record, while `github.command.link-issue` refuses without one.
  record_type  TEXT,
  record_id    TEXT,
  -- Both are `TIMESTAMPTZ`, not TEXT. A TEXT timestamp only orders correctly for one fixed-width
  -- spelling — "…T12:00:00.000Z" sorts *before* "…T12:00:00Z" because '.' is 0x2E and 'Z' is 0x5A —
  -- and the column a report compares ("has the issue moved since we linked it?") is exactly the one
  -- that must order. The store projects them back to ISO strings, because the row contract is text.
  issue_updated_at TIMESTAMPTZ,
  linked_at        TIMESTAMPTZ NOT NULL,
  -- Which call wrote the row last. Two different keys writing the same issue are two reads of the
  -- same fact, and the row says so instead of pretending the second one was the first.
  idempotency_key  TEXT   NOT NULL,
  CONSTRAINT github_issue_link_pkey PRIMARY KEY (company_id, repository, issue_number),
  -- The half of the key that may be empty: a link with no record is a link somebody synced before
  -- they linked it, and a partial index keeps those rows out of the record lookup's plan.
  CONSTRAINT github_issue_link_record_present CHECK (record_id IS NULL OR record_type IS NOT NULL)
);

-- The lookup behind `github.custom-field.repository` and `github.custom-field.head-sha`: "the link
-- that names this Alran record". `company_id` first, like every key and every index in this file —
-- an index that led with `record_id` would let one company's maintenance query walk another's rows.
CREATE INDEX IF NOT EXISTS github_issue_link_by_company_record
  ON public.github_issue_link (company_id, record_type, record_id)
  WHERE record_id IS NOT NULL;

-- The sweep behind `data.retention_on_uninstall` and behind the report's "not read in 90 days"
-- question, if anybody ever asks it. Same order as the column list it filters.
CREATE INDEX IF NOT EXISTS github_issue_link_by_company_linked
  ON public.github_issue_link (company_id, linked_at DESC);

-- Row-level security, in the shape the Platform generates: the same ENABLE, the same FORCE and the
-- same policy name as every table in this directory. `secureSchema` adds the first two when they are
-- missing and keys the third on `polname`, so this file and the generator agree on the end state —
-- and the promise is readable here, in the app's own migration, instead of only in a generator on
-- the other side of the tree.
ALTER TABLE public.github_issue_link ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.github_issue_link FORCE ROW LEVEL SECURITY;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
     WHERE schemaname = 'public'
       AND tablename = 'github_issue_link'
       AND policyname = 'ottili_company_isolation'
  ) THEN
    EXECUTE
      'CREATE POLICY ottili_company_isolation ON public.github_issue_link AS PERMISSIVE FOR ALL
         USING (company_id = NULLIF(current_setting(''ottili.company_id'', true), ''''))
         WITH CHECK (company_id = NULLIF(current_setting(''ottili.company_id'', true), ''''))';
  END IF;
END
$$;

-- Not in this file: the sweep that deletes rows after `data.retention_on_uninstall` has passed.
-- That value is one window for all six classes (`docs/platform-gaps.md`, entry 18), so a per-table
-- sweep written today would be a retention rule the manifest does not promise and nobody can turn
-- off. The index above is the one such a sweep will want; the sweep itself belongs to the pass that
-- resolves entry 18.
