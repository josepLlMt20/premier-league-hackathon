import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { ShotComparison } from './ShotComparison';
import type { ContextResult } from '../../api/client';
import { context, metadata } from '../../test-fixtures';

const fact = (team: string, value: number | null): ContextResult['facts'][number] => ({
  fact_id: `shots-${team}`,
  snapshot_id: context.snapshot_id,
  cutoff_sequence: 1,
  team_id: team,
  name: 'shots',
  value,
  unit: 'shots',
  interval: { start_sequence: 0, end_sequence: 1 },
  sample_count: value || 0,
  event_ids: [],
  method: 'Shot events.',
  limitations: [],
});
const result: ContextResult = { ...context, facts: [fact('home', 6), fact('away', 0)] };

it('compares only the two shot counts of the immutable context interval, including an empty zero meter', () => {
  render(<ShotComparison result={result} metadata={metadata} language="es" />);
  expect(screen.getByRole('heading', { name: '6 tiros frente a 0' })).toBeVisible();
  expect(screen.getByRole('meter', { name: 'Harbour FC: 6 tiros' })).toHaveAttribute('value', '6');
  expect(screen.getByRole('meter', { name: 'Valley United: 0 tiros' })).toHaveAttribute(
    'value',
    '0',
  );
});
it('does not imply a leader when both teams have no shots', () => {
  render(
    <ShotComparison
      result={{ ...result, facts: [fact('home', 0), fact('away', 0)] }}
      metadata={metadata}
      language="en"
    />,
  );
  expect(screen.getByRole('heading', { name: '0 shots to 0' })).toBeVisible();
  expect(screen.getAllByRole('meter').every((meter) => meter.getAttribute('value') === '0')).toBe(
    true,
  );
});
it.each(
  [
    [],
    [fact('home', 6)],
    [fact('home', null), fact('away', 0)],
    [fact('home', -1), fact('away', 0)],
    [fact('home', Infinity), fact('away', 0)],
    [fact('home', 1.5), fact('away', 0)],
    [fact('home', 6), fact('away', 0), { ...fact('home', 5), fact_id: 'duplicate' }],
    [{ ...fact('home', 6), snapshot_id: 'other' }, fact('away', 0)],
    [{ ...fact('home', 6), cutoff_sequence: 2 }, fact('away', 0)],
    [{ ...fact('home', 6), interval: { start_sequence: 1, end_sequence: 1 } }, fact('away', 0)],
    [{ ...fact('home', 6), unit: '%' }, fact('away', 0)],
  ].map((facts) => ({ facts })),
)(
  'omits incomplete or mismatched facts rather than substituting broader match totals (%#)',
  ({ facts }) => {
    const { container } = render(
      <ShotComparison result={{ ...result, facts }} metadata={metadata} language="es" />,
    );
    expect(container).toBeEmptyDOMElement();
  },
);
