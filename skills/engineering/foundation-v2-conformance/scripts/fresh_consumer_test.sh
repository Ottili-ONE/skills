#!/bin/bash
# fresh_consumer_test.sh — build a throwaway app that imports a named Foundation
# component and asserts it renders with documented props only.
#
# Usage: fresh_consumer_test.sh <component-name> <output-dir>
# Foreground only: no '&', nohup, setsid (shared-host rule).
set -euo pipefail
COMPONENT="${1:?usage: fresh_consumer_test.sh <component> <outdir>}"
OUTDIR="${2:?usage: fresh_consumer_test.sh <component> <outdir>}"
mkdir -p "$OUTDIR"

# A fresh-consumer test must import ONLY the public package surface. Reaching into
# dist/ or internals is a unit test in disguise and fails here.
cat > "$OUTDIR/consumer.test.tsx" <<EOF
import { test, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ${COMPONENT} } from '@ottili/foundation-ui';

test('${COMPONENT} renders with documented props only', () => {
  const { container } = render(<${COMPONENT} label="ottili" />);
  expect(screen.getByText('ottili')).toBeInTheDocument();
  // A fresh consumer must not reach into internals:
  expect(container.innerHTML).not.toContain('__foundation_internal');
});

cd "$OUTDIR"
npm init -y >/dev/null 2>&1
npm install --no-save @ottili/foundation-ui vitest @testing-library/react >/dev/null 2>&1 || {
  echo "ERROR: cannot install Foundation package — is the consumer online?" >&2
  exit 1
}
npx vitest run consumer.test.tsx --reporter=default > test.log 2>&1
echo "EXIT=$?" >> test.log
tail -5 test.log
