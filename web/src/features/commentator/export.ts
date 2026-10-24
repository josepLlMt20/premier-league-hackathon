import type { ContextResult, MatchView } from '../../api/client';

export type ContextFrame = Readonly<{ result: ContextResult; view: MatchView; second: number }>;
type Card = ContextResult['cards'][number];
type Interval = Card['current_interval'];
const fields = ['headline', 'explanation', 'suggested_line', 'overlay_text'] as const;

function assertFrame({ result, view, second }: ContextFrame) {
  if (
    result.status !== 'verified' ||
    result.mode === 'factual' ||
    result.request.role !== 'commentator' ||
    result.snapshot_id !== view.snapshot_id ||
    result.request.to_sequence !== view.cutoff_sequence ||
    result.request.match_id !== view.match_id ||
    view.match_id !== view.metadata.match_id ||
    !Number.isSafeInteger(second) ||
    second < view.available_second ||
    second > view.metadata.duration_seconds ||
    !result.cards.length ||
    result.cards.length > 3 ||
    new Set(result.cards.map((card) => card.story_id)).size !== result.cards.length
  ) {
    throw new Error('A verified, matching professional receipt is required.');
  }
}
function validInterval(interval: Interval, frame: ContextFrame) {
  return (
    Number.isSafeInteger(interval.start_sequence) &&
    Number.isSafeInteger(interval.end_sequence) &&
    interval.start_sequence >= 0 &&
    interval.start_sequence <= interval.end_sequence &&
    interval.end_sequence <= frame.result.request.to_sequence &&
    ((interval.start_second == null && interval.end_second == null) ||
      (interval.start_second != null &&
        interval.end_second != null &&
        interval.start_second >= 0 &&
        interval.start_second <= interval.end_second &&
        interval.end_second <= frame.second))
  );
}
function cardData(frame: ContextFrame, storyId: string) {
  assertFrame(frame);
  const card = frame.result.cards.find((candidate) => candidate.story_id === storyId);
  if (
    !card ||
    card.claims.length !== 4 ||
    fields.some((field) => !card[field].trim()) ||
    Array.from(card.overlay_text).length > 140 ||
    !validInterval(card.current_interval, frame) ||
    !validInterval(card.comparison_interval, frame)
  ) {
    throw new Error('This editorial card cannot be exported.');
  }
  const factIds = [...new Set(card.claims.flatMap((claim) => claim.fact_ids || []))];
  const facts = factIds.map((id) => {
    const matches = frame.result.facts.filter((fact) => fact.fact_id === id);
    const fact = matches[0];
    if (
      matches.length !== 1 ||
      fact.snapshot_id !== frame.result.snapshot_id ||
      fact.cutoff_sequence !== frame.result.request.to_sequence ||
      !validInterval(fact.interval, frame)
    ) {
      throw new Error('A cited fact does not belong to this receipt.');
    }
    return fact;
  });
  const eventIds = [
    ...new Set([
      ...card.claims.flatMap((claim) => claim.event_ids || []),
      ...facts.flatMap((fact) => fact.event_ids),
    ]),
  ];
  if (
    (!eventIds.length && !factIds.length) ||
    !eventIds.every((id) => frame.result.evidence_ids.includes(id))
  ) {
    throw new Error('The source references are missing from this receipt.');
  }
  return { card, factIds, eventIds, facts };
}
function receipt(frame: ContextFrame) {
  return {
    schema_version: 1,
    match_id: frame.result.request.match_id,
    snapshot_id: frame.result.snapshot_id,
    cutoff_sequence: frame.result.request.to_sequence,
    displayed_second: frame.second,
    score: frame.view.score.map((score) => ({ ...score })),
    language: frame.result.request.language,
    provenance: { mode: frame.result.mode, status: frame.result.status },
  } as const;
}
export function overlayFor(frame: ContextFrame, storyId: string) {
  const { card, factIds, eventIds } = cardData(frame, storyId);
  return {
    ...receipt(frame),
    kind: 'touchline.overlay' as const,
    story_id: card.story_id,
    text: card.overlay_text,
    claim_kind: card.claims[3].kind,
    current_interval: card.current_interval,
    comparison_interval: card.comparison_interval,
    fact_ids: factIds,
    event_ids: eventIds,
    limitations: [...card.limitations],
  };
}
export type OverlayPayload = ReturnType<typeof overlayFor>;
export function briefingPayload(frame: ContextFrame) {
  assertFrame(frame);
  return {
    ...receipt(frame),
    kind: 'touchline.briefing' as const,
    request: frame.result.request,
    summary: frame.result.summary,
    cards: frame.result.cards.map((source) => {
      const { card, facts, factIds, eventIds } = cardData(frame, source.story_id);
      return {
        story_id: card.story_id,
        headline: card.headline,
        explanation: card.explanation,
        suggested_line: card.suggested_line,
        overlay_text: card.overlay_text,
        current_interval: card.current_interval,
        comparison_interval: card.comparison_interval,
        limitations: [...card.limitations],
        facts,
        fact_ids: factIds,
        event_ids: eventIds,
        // Source claims contain templates. Consumers receive their rendered field,
        // class and references instead of accidentally displaying raw placeholders.
        claims: card.claims.map((claim, index) => ({
          claim_id: claim.claim_id,
          field: fields[index],
          kind: claim.kind,
          text: card[fields[index]],
          fact_ids: claim.fact_ids,
          event_ids: claim.event_ids,
        })),
      };
    }),
    trace_id: frame.result.trace_id,
    trace: frame.result.trace,
  };
}
export function canExportBriefing(frame: ContextFrame) {
  try {
    briefingPayload(frame);
    return true;
  } catch {
    return false;
  }
}
export function exportBriefing(frame: ContextFrame): Blob {
  return new Blob([JSON.stringify(briefingPayload(frame), null, 2) + '\n'], {
    type: 'application/json;charset=utf-8',
  });
}
