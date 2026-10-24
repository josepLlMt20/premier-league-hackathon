import type { components } from './schema';
export type MatchMetadata = components['schemas']['MatchMetadata'];
export type MatchView = components['schemas']['MatchView'];
export type MatchHead = components['schemas']['MatchHead'];
export type ResolvedCursor = components['schemas']['ResolvedCursor'];
export type ContextRequest = components['schemas']['ContextRequest'];
export type ContextResult = components['schemas']['ContextResult'];
export type EvidenceBundle = components['schemas']['EvidenceBundle'];
export type MatchEvent = components['schemas']['MatchEvent'];
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
  ) {
    super(code);
  }
}
async function json<T>(path: string, signal: AbortSignal, body?: unknown): Promise<T> {
  const deadline = new AbortController();
  const timer = setTimeout(
    () => deadline.abort(new DOMException('Request timed out', 'TimeoutError')),
    path === '/api/context' ? 30000 : 15000,
  );
  try {
    const response = await fetch(path, {
      signal: AbortSignal.any([signal, deadline.signal]),
      cache: 'no-store',
      ...(body === undefined
        ? {}
        : {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => null);
      throw new ApiError(response.status, error?.error?.code || 'unavailable');
    }
    return (await response.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}
const matchPath = (id: string) => `/api/matches/${encodeURIComponent(id)}`;
export const fetchMatches = (signal: AbortSignal) =>
  json<readonly MatchMetadata[]>('/api/matches', signal);
export const fetchHead = (id: string, signal: AbortSignal) =>
  json<MatchHead>(`${matchPath(id)}/head`, signal);
export const resolveCursor = (matchId: string, second: number, signal: AbortSignal) =>
  json<ResolvedCursor>(`${matchPath(matchId)}/cursor?available_second=${second}`, signal);
export const fetchView = (matchId: string, cutoff: number, signal: AbortSignal) =>
  json<MatchView>(`${matchPath(matchId)}/view?to_sequence=${cutoff}`, signal);
export const requestContext = (request: ContextRequest, signal: AbortSignal) =>
  json<ContextResult>('/api/context', signal, request);
export const fetchEvidence = (
  matchId: string,
  cutoff: number,
  eventIds: readonly string[],
  signal: AbortSignal,
) =>
  json<EvidenceBundle>('/api/evidence', signal, {
    match_id: matchId,
    to_sequence: cutoff,
    event_ids: eventIds,
  });
