import type { components } from './api/schema';
export const metadata: components['schemas']['MatchMetadata'] = {
  match_id: 'match-test',
  duration_seconds: 5400,
  teams: [
    { team_id: 'home', name: 'Harbour FC', players: [{ player_id: 'h1', name: 'Alex Reed' }] },
    { team_id: 'away', name: 'Valley United', players: [{ player_id: 'a1', name: 'Sam Lane' }] },
  ],
  attack_directions: [],
};
export const event: components['schemas']['MatchEvent'] = {
  match_id: 'match-test',
  event_id: 'event-1',
  sequence: 1,
  occurred_second: 400,
  available_second: 400,
  period: 1,
  kind: 'pass',
  team_id: 'home',
  player_id: 'h1',
  start: { x: 40, y: 30 },
  end: { x: 60, y: 35 },
  attributes: { recipient_id: 'h2', completed: true, under_pressure: false },
};
export const view: components['schemas']['MatchView'] = {
  match_id: 'match-test',
  cutoff_sequence: 1,
  snapshot_id: 'match-test:1:hash',
  available_second: 400,
  metadata,
  score: [
    { team_id: 'home', goals: 0 },
    { team_id: 'away', goals: 0 },
  ],
  recent_events: [event],
  facts: [],
  annulled_event_ids: [],
};
export const context: components['schemas']['ContextResult'] = {
  request: {
    match_id: 'match-test',
    from_sequence: 0,
    to_sequence: 1,
    role: 'fan',
    depth: 'simple',
    language: 'es',
    favorite_team_id: null,
  },
  snapshot_id: view.snapshot_id,
  status: 'verified',
  mode: 'scripted',
  summary: 'Harbour recupera más arriba.',
  summary_claims: [],
  cards: [],
  facts: [],
  evidence_ids: [event.event_id],
  rejection_codes: [],
  trace_id: 'cached-trace',
  trace: {
    steps: [],
    tool_names: [],
    model_calls: 0,
    tool_calls: 0,
    input_tokens: 0,
    output_tokens: 0,
    elapsed_seconds: 0,
  },
};
