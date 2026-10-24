import type { ContextResult } from '../../api/client';
import { context, view } from '../../test-fixtures';
export const briefingCard: ContextResult['cards'][number] = {
  story_id: 'story-one', headline: 'Harbour recupera arriba.',
  explanation: 'Se observa un cambio en las recuperaciones.',
  suggested_line: 'Harbour recupera más arriba en este tramo.',
  overlay_text: 'Harbour recupera más arriba.',
  current_interval: { start_sequence: 0, end_sequence: 1, start_second: 300, end_second: 400 },
  comparison_interval: { start_sequence: 0, end_sequence: 0, start_second: 0, end_second: 300 },
  limitations: ['Datos sintéticos; la asociación no demuestra una causa.'],
  claims: ['headline', 'explanation', 'line', 'overlay'].map((field, index) => ({
    claim_id: `claim-${field}`, kind: index === 1 ? 'interpretation' as const : 'observed' as const,
    text: '{{entity:home}}: {{fact:source-template}}', fact_ids: [], event_ids: ['event-1'], limitations: [],
  })),
};
export const professionalResult: ContextResult = {
  ...context, request: { ...context.request, role: 'commentator' },
  cards: [briefingCard], summary: briefingCard.suggested_line, summary_claims: [briefingCard.claims[2]],
  trace: { ...context.trace!, steps: [{ role: 'analyst', decision: 'started' }, { role: 'writer', decision: 'started' }, { role: 'reviewer', decision: 'accepted' }] },
};
export const professionalFrame = { result: professionalResult, view, second: 400 };
