// Bad consumer: deep import into internals, a `padding` prop that Card does not export,
// and raw design values that are not in the token file.
import { Button } from '@ottili/foundation-ui/dist/components/Button';
import { tokens } from '@ottili/foundation-ui/tokens';

export function OrderCard() {
  return (
    <Card padding={tokens.spacing.md}>
      <Button variant="primary">Save</Button>
    </Card>
  );
}
