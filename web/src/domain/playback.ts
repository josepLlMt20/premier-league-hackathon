import type { components } from '../api/schema';
export type Preferences = {
  language: 'es' | 'en';
  depth: 'simple' | 'detailed';
  favorite_team_id: string | null;
};
export type PlaybackState = {
  second: number;
  fromSecond: number;
  speed: number;
  playing: boolean;
  preferences: Preferences;
  requestKey: number;
  view: components['schemas']['MatchView'] | null;
  context: components['schemas']['ContextResult'] | null;
  evidenceOpen: boolean;
};
export type Action =
  | { type: 'seek'; second: number }
  | { type: 'preferences'; preferences: Preferences }
  | { type: 'playing'; playing: boolean }
  | { type: 'speed'; speed: number }
  | { type: 'from'; second: number }
  | { type: 'view'; view: PlaybackState['view']; key: number }
  | { type: 'context'; result: NonNullable<PlaybackState['context']>; key: number }
  | { type: 'advance'; headSecond: number }
  | { type: 'evidence'; open: boolean };
export function initialPlayback(): PlaybackState {
  return {
    second: 0,
    fromSecond: 0,
    speed: 1,
    playing: false,
    preferences: { language: 'es', depth: 'simple', favorite_team_id: null },
    requestKey: 0,
    view: null,
    context: null,
    evidenceOpen: false,
  };
}
export function reducePlayback(state: PlaybackState, action: Action): PlaybackState {
  switch (action.type) {
    case 'advance': {
      if (!state.playing) return state;
      const second = Math.min(action.headSecond, state.second + state.speed);
      return second === state.second
        ? { ...state, playing: false }
        : reducePlayback(state, { type: 'seek', second });
    }
    case 'seek':
      return {
        ...state,
        second: action.second,
        fromSecond: Math.min(state.fromSecond, action.second),
        view: null,
        context: null,
        evidenceOpen: false,
        requestKey: state.requestKey + 1,
      };
    case 'preferences':
      return {
        ...state,
        preferences: action.preferences,
        context: null,
        evidenceOpen: false,
        requestKey: state.requestKey + 1,
      };
    case 'from':
      return {
        ...state,
        fromSecond: Math.min(action.second, state.second),
        context: null,
        evidenceOpen: false,
        requestKey: state.requestKey + 1,
      };
    case 'playing':
      return { ...state, playing: action.playing };
    case 'speed':
      return { ...state, speed: action.speed };
    case 'view':
      return action.key === state.requestKey ? { ...state, view: action.view } : state;
    case 'context':
      return applyContext(state, action.result, action.key);
    case 'evidence':
      return { ...state, evidenceOpen: action.open };
  }
}
export function applyContext(
  state: PlaybackState,
  result: components['schemas']['ContextResult'],
  key: number,
): PlaybackState {
  return key === state.requestKey && result.snapshot_id === state.view?.snapshot_id
    ? { ...state, context: result }
    : state;
}
export function clock(second: number): string {
  return `${Math.floor(second / 60)
    .toString()
    .padStart(2, '0')}:${Math.floor(second % 60)
    .toString()
    .padStart(2, '0')}`;
}
export const preferenceKey = 'match-context.preferences.v1';
export function readPreferences(): Preferences {
  try {
    const raw = JSON.parse(localStorage.getItem(preferenceKey) || 'null');
    if (
      raw &&
      ['es', 'en'].includes(raw.language) &&
      ['simple', 'detailed'].includes(raw.depth) &&
      (raw.favorite_team_id === null || typeof raw.favorite_team_id === 'string')
    )
      return { language: raw.language, depth: raw.depth, favorite_team_id: raw.favorite_team_id };
  } catch {
    /* Private browsing or damaged preferences: keep a usable default. */
  }
  return initialPlayback().preferences;
}
