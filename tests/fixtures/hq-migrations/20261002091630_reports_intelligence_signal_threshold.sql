-- One threshold per signal kind per company, with the moment it started counting (DESIGN 4.6, I8).
--
-- `since` is the whole reason this is a table and not a number on the signal row. Blueprint 43.7
-- lists "configurable alert thresholds" as a capability, and a configurable threshold has a date:
-- on 1 March the company moved "delivery late" from 5 to 3 days. Signals raised in February still
-- show `threshold.value = 5, threshold.since = <February>`, because a signal that changes its own
-- justification after the fact is a signal nobody can argue with. The threshold takes effect on the
-- *next* run; the row that is already open keeps the number that produced it.
--
-- The unique key is `(company_id, signal_key)` - one live threshold per signal kind. Not one per
-- rule and not one per domain: `purchasing.supplier.delayed` is one question with one answer, and a
-- second row for the same key would be two answers with no way to say which one applies.
CREATE TABLE reports_intelligence_signal_threshold (
  company_id       text          NOT NULL,
  id               text          NOT NULL,
  signal_key       text          NOT NULL,
  -- The machine name of the rule that raised the signal. Separate from signal_key because a rule
  -- may be more specific than the signal it produces (one rule, several signals, or the reverse).
  rule_id          text          NOT NULL,
  -- `gt`, `gte`, `lt`, `lte`, `eq`. Named rather than encoded as a sign, because the units differ
  -- per signal and a minus sign would lie about half of them.
  comparator       text          NOT NULL,
  -- The limit. numeric and not bigint because a threshold can be days (7), cents (250000) or a
  -- percentage (12.5) depending on the signal; the unit lives in `unit`.
  value            numeric       NOT NULL,
  unit             text          NOT NULL,
  -- How far back the rule looks when it evaluates.
  window_minutes   integer       NOT NULL,
  -- The severity a hit gets. Compared only inside this signal_key (signal I2).
  severity         text          NOT NULL,
  -- The moment this value took effect (I8). Not nullable on purpose: a threshold without a start
  -- cannot be compared with the signal it produced.
  since            timestamptz   NOT NULL DEFAULT now(),
  created_at       timestamptz   NOT NULL DEFAULT now(),
  created_by       text          NOT NULL DEFAULT '',
  updated_at       timestamptz   NOT NULL DEFAULT now(),
  updated_by       text          NOT NULL DEFAULT '',
  deleted_at       timestamptz,
  PRIMARY KEY (company_id, id),
  CONSTRAINT reports_intelligence_signal_threshold_key_check UNIQUE (company_id, signal_key),
  CONSTRAINT reports_intelligence_signal_threshold_comparator_check
    CHECK (comparator IN ('gt', 'gte', 'lt', 'lte', 'eq')),
  CONSTRAINT reports_intelligence_signal_threshold_severity_check
    CHECK (severity IN ('low', 'medium', 'high')),
  CONSTRAINT reports_intelligence_signal_threshold_window_check
    CHECK (window_minutes > 0),
  CONSTRAINT reports_intelligence_signal_threshold_signal_key_check
    CHECK (signal_key ~ '^[a-z0-9]+(\.[a-z0-9_-]+){2,3}$'),
  CONSTRAINT reports_intelligence_signal_threshold_unit_check
    CHECK (btrim(unit) <> '')
);

-- "Which thresholds changed since the last run?" reads this; the list route sorts by the same
-- column the keyset cursor uses.
CREATE INDEX reports_intelligence_signal_threshold_list
  ON reports_intelligence_signal_threshold (company_id, since DESC, id);

-- The rules that produce one signal kind, for the signal inbox to explain itself.
CREATE INDEX reports_intelligence_signal_threshold_rule
  ON reports_intelligence_signal_threshold (company_id, rule_id, id);

ALTER TABLE reports_intelligence_signal_threshold ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports_intelligence_signal_threshold FORCE ROW LEVEL SECURITY;

CREATE POLICY reports_intelligence_signal_threshold_tenant_isolation ON reports_intelligence_signal_threshold
  USING (company_id = current_setting('app.company_id', true))
  WITH CHECK (company_id = current_setting('app.company_id', true));
