// Good consumer: named import from the public package surface, token-derived values,
// `Card.padded` (the real prop) instead of a `padding` prop that does not exist.
import { Button, Card } from '@ottili/foundation-ui';
import { duration, density } from '@ottili/foundation-ui/tokens';

export function OrderCard() {
  return (
    <Card padded tone="elevated">
      <Button variant="primary" style={{ transitionDuration: duration('fast') }}>
        Save
      </Button>
    </Card>
  );
}
