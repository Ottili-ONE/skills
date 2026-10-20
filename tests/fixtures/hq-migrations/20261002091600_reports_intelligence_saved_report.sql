-- The "My Work" definition of one person, and the delivery plan that hangs on it (DESIGN 4.4).
--
-- Delivery is a jsonb value object and not a seventh entity. That is a decision with a consequence:
-- there is exactly one place in the product that answers "when does X get the report", and it is
-- this row. A separate schedule table would create a second answer that could disagree with the
-- first - and the disagreement would be discovered by a customer.
--
-- What this file refuses to model is the delivery itself. `delivery.recipients` names role
-- templates and subjects *inside the company*; it never holds an address. HQ does not host mail
-- (Blueprint non-goals), and a stored address would be a mailing list that no service is allowed to
-- use. The CHECK at the bottom is a blunt net for that; the authoritative rule is in the store,
-- which names the offending recipient instead of the document.
CREATE TABLE reports_intelligence_saved_report (
  company_id        text        NOT NULL,
  id                text        NOT NULL,
  report_key        text        NOT NULL,
  name              text        NOT NULL,
  owner_subject_id  text        NOT NULL,
  visibility        text        NOT NULL DEFAULT 'private',
  -- A named view of records from settings-governance (Blueprint 24.2), never a raw filter.
  record_scope      text        NOT NULL,
  filters           jsonb       NOT NULL DEFAULT '{}'::jsonb,
  columns           text[]      NOT NULL DEFAULT '{}',
  group_by          text[]      NOT NULL DEFAULT '{}',
  sort              jsonb       NOT NULL DEFAULT '{}'::jsonb,
  pinned            boolean     NOT NULL DEFAULT false,
  -- `{ enabled, schedule, recipients, format, subject_line, artifact_naming }`.
  delivery          jsonb       NOT NULL,
  status            text        NOT NULL DEFAULT 'active',
  revision          integer     NOT NULL DEFAULT 1,
  last_run_at       timestamptz,
  -- Recomputed in the company timezone after every run (I5). Never "last run plus 24 hours": a
  -- daylight-saving day is 23 or 25 hours long and the next run follows the wall clock.
  next_run_at       timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  created_by        text        NOT NULL DEFAULT '',
  updated_at        timestamptz NOT NULL DEFAULT now(),
  updated_by        text        NOT NULL DEFAULT '',
  -- I6: `archived` is reversible, there is no delete edge. This column is what a withdrawn row
  -- keeps so that its run history stays explainable.
  deleted_at        timestamptz,
  PRIMARY KEY (company_id, id),
  -- One name per owner per company. Two people may both call theirs "Open items".
  CONSTRAINT reports_intelligence_saved_report_owner_name_key UNIQUE (company_id, owner_subject_id, name),
  CONSTRAINT reports_intelligence_saved_report_visibility_check
    CHECK (visibility IN ('private', 'team', 'company')),
  CONSTRAINT reports_intelligence_saved_report_status_check
    CHECK (status IN ('active', 'paused', 'archived')),
  CONSTRAINT reports_intelligence_saved_report_name_check
    CHECK (btrim(name) <> ''),
  CONSTRAINT reports_intelligence_saved_report_delivery_check
    CHECK (
      jsonb_typeof(delivery) = 'object'
      AND jsonb_typeof(delivery -> 'enabled') = 'boolean'
      AND jsonb_typeof(delivery -> 'schedule') = 'object'
      AND jsonb_typeof(delivery -> 'recipients') = 'array'
      AND jsonb_array_length(delivery -> 'recipients') > 0
    ),
  -- I4: a delivery produces a job and an artifact in Platform Files, never a send. The format is
  -- the artifact format, and there is no "email" here to name.
  CONSTRAINT reports_intelligence_saved_report_delivery_format_check
    CHECK (delivery ->> 'format' IN ('csv', 'xlsx', 'json')),
  -- I3, blunt half: no key named address/email anywhere in the delivery value. A hand-written row
  -- that smuggles in an address is refused here; the store is what tells a caller *which* recipient
  -- was wrong, because a constraint can only say that the document is.
  CONSTRAINT reports_intelligence_saved_report_no_address_check
    CHECK (delivery::text !~* '"(address|email|email_address|mail_to)"\s*:'),
  -- A paused or archived row has no next run. Carrying a stale next_run_at on a paused delivery is
  -- how a paused report keeps arriving.
  CONSTRAINT reports_intelligence_saved_report_paused_check
    CHECK (status = 'active' OR next_run_at IS NULL),
  CONSTRAINT reports_intelligence_saved_report_revision_check
    CHECK (revision >= 1)
);

-- The due-work index. Partial on purpose: only an active row with a scheduled moment is ever asked
-- for, and an index over paused rows is an index that pays for rows nobody reads.
CREATE INDEX reports_intelligence_saved_report_due
  ON reports_intelligence_saved_report (company_id, next_run_at, id)
  WHERE next_run_at IS NOT NULL AND status = 'active' AND deleted_at IS NULL;

-- The owner's list, which is what "My Work" reads: pinned first, then most recently touched.
CREATE INDEX reports_intelligence_saved_report_owner
  ON reports_intelligence_saved_report (company_id, owner_subject_id, pinned DESC, updated_at DESC, id);

-- The team/company list, for a shared report. visibility is the filter, so it leads.
CREATE INDEX reports_intelligence_saved_report_shared
  ON reports_intelligence_saved_report (company_id, visibility, updated_at DESC, id)
  WHERE visibility <> 'private' AND deleted_at IS NULL;

ALTER TABLE reports_intelligence_saved_report ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports_intelligence_saved_report FORCE ROW LEVEL SECURITY;

CREATE POLICY reports_intelligence_saved_report_tenant_isolation ON reports_intelligence_saved_report
  USING (company_id = current_setting('app.company_id', true))
  WITH CHECK (company_id = current_setting('app.company_id', true));
