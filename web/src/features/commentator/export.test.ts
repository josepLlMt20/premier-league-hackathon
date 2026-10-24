import { expect, it } from 'vitest';
import { exportBriefing, overlayFor, canExportBriefing } from './export';
import { professionalFrame, professionalResult, briefingCard } from './fixtures';
import { view } from '../../test-fixtures';
const readBlob = (blob: Blob) =>
  new Promise<any>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(JSON.parse(reader.result as string));
    reader.onerror = reject;
    reader.readAsText(blob);
  });
it('exports the captured score, cutoff, intervals, rendered claims and limitations without reading current state', async () => {
  const blob = exportBriefing(professionalFrame);
  const later = {
    ...view,
    cutoff_sequence: 9,
    snapshot_id: 'later',
    score: [
      { team_id: 'home', goals: 9 },
      { team_id: 'away', goals: 0 },
    ],
  };
  expect(later.score[0].goals).toBe(9);
  const payload = await readBlob(blob);
  expect(payload.snapshot_id).toBe(view.snapshot_id);
  expect(payload.cutoff_sequence).toBe(1);
  expect(payload.displayed_second).toBe(400);
  expect(payload.score).toEqual(view.score);
  expect(payload.cards[0].limitations).toEqual(briefingCard.limitations);
  expect(payload.cards[0].claims[1].kind).toBe('interpretation');
  expect(JSON.stringify(payload)).not.toContain('{{');
  expect(payload.cards[0].current_interval).toEqual(briefingCard.current_interval);
});
it('keeps validated overlay text unchanged and carries its evidence, time and limitations', () => {
  const overlay = overlayFor(professionalFrame, briefingCard.story_id);
  expect(overlay.text).toBe(briefingCard.overlay_text);
  expect(overlay.limitations).toEqual(briefingCard.limitations);
  expect(overlay.event_ids).toEqual(['event-1']);
  expect(overlay.cutoff_sequence).toBe(1);
  expect(overlay.displayed_second).toBe(400);
});
it.each(['factual', 'insufficient'] as const)(
  'blocks %s results even if they contain a spurious card',
  (status) => {
    const frame = { ...professionalFrame, result: { ...professionalResult, status } };
    expect(canExportBriefing(frame)).toBe(false);
    expect(() => exportBriefing(frame)).toThrow();
  },
);
it.each([
  {
    ...professionalFrame,
    result: {
      ...professionalResult,
      request: { ...professionalResult.request, role: 'fan' as const },
    },
  },
  { ...professionalFrame, view: { ...view, snapshot_id: 'other' } },
  { ...professionalFrame, view: { ...view, cutoff_sequence: 2 } },
  { ...professionalFrame, second: 100 },
  { ...professionalFrame, result: { ...professionalResult, cards: [] } },
  { ...professionalFrame, result: { ...professionalResult, evidence_ids: [] } },
])('rejects a missing or incompatible receipt (%#)', (frame) => {
  expect(canExportBriefing(frame)).toBe(false);
});
it('cannot export an unknown/rejected story even when another accepted story exists', () => {
  expect(() => overlayFor(professionalFrame, 'rejected-story')).toThrow();
  expect(
    canExportBriefing({
      ...professionalFrame,
      result: { ...professionalResult, rejection_codes: ['another_story_rejected'] },
    }),
  ).toBe(true);
});
it('counts Unicode code points and refuses an oversized overlay instead of truncating it', () => {
  const frame = {
    ...professionalFrame,
    result: { ...professionalResult, cards: [{ ...briefingCard, overlay_text: '⚽'.repeat(140) }] },
  };
  expect(overlayFor(frame, briefingCard.story_id).text).toBe('⚽'.repeat(140));
  expect(
    canExportBriefing({
      ...frame,
      result: { ...frame.result, cards: [{ ...briefingCard, overlay_text: '⚽'.repeat(141) }] },
    }),
  ).toBe(false);
});
