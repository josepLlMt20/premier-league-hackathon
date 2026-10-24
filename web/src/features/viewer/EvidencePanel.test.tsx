import { fireEvent, render, screen, within } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { EvidencePanel } from './EvidencePanel';
import * as api from '../../api/client';
import { metadata, context, view } from '../../test-fixtures';
vi.mock('../../api/client', async (original) => ({
  ...(await original<typeof api>()),
  fetchEvidence: vi.fn(),
}));
beforeEach(() =>
  vi.mocked(api.fetchEvidence).mockResolvedValue({
    snapshot_id: view.snapshot_id,
    cutoff_sequence: 1,
    events: [],
    annulled_event_ids: [],
  }),
);
it.each(['es', 'en'] as const)(
  'explains the shot-quality measurement with its supplied unit and method in %s',
  async (language) => {
    const result: api.ContextResult = {
      ...context,
      facts: [
        {
          fact_id: 'quality',
          snapshot_id: view.snapshot_id,
          cutoff_sequence: 1,
          team_id: 'home',
          name: 'shot_quality_total',
          value: 19.5,
          unit: 'heuristic points',
          interval: { start_sequence: 0, end_sequence: 1 },
          sample_count: 2,
          event_ids: [],
          method: 'Sum of distance-and-pressure shot-quality heuristic; not calibrated xG.',
          limitations: ['Simulator heuristic, not a goal probability.'],
        },
      ],
      summary_claims: [
        {
          claim_id: 'claim',
          kind: 'observed',
          text: 'Quality',
          fact_ids: ['quality'],
          event_ids: [],
          limitations: [],
        },
      ],
    };
    render(
      <EvidencePanel
        open
        result={result}
        metadata={metadata}
        language={language}
        close={() => {}}
        returnFocus={null}
      />,
    );
    const dialog = within(await screen.findByRole('dialog'));
    expect(
      dialog.getByText(language === 'es' ? '19,5 puntos heurísticos' : '19.5 heuristic points'),
    ).toBeVisible();
    fireEvent.click(
      dialog.getByText(language === 'es' ? 'Definición' : 'Definition', { exact: true }),
    );
    expect(
      dialog.getByText(
        language === 'es'
          ? 'Suma de una heurística de calidad de tiro basada en distancia y presión; no es xG calibrado.'
          : result.facts[0].method,
      ),
    ).toBeVisible();
  },
);
