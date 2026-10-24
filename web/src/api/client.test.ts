import { afterEach, expect, it, vi } from 'vitest';
import { ApiError, fetchHead, fetchView, requestContext } from './client';
import { context } from '../test-fixtures';
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
it('reads only the requested prefix and disables HTTP caching', async () => {
  const fetch = vi.fn().mockResolvedValue(new Response('{}'));
  vi.stubGlobal('fetch', fetch);
  const controller = new AbortController();
  await fetchView('a/b', 12, controller.signal);
  expect(fetch).toHaveBeenCalledWith(
    '/api/matches/a%2Fb/view?to_sequence=12',
    expect.objectContaining({ cache: 'no-store', signal: expect.any(AbortSignal) }),
  );
});
it('propagates admission errors without exposing provider output', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ error: { code: 'generation_busy' } }), { status: 429 }),
      ),
  );
  await expect(requestContext(context.request, new AbortController().signal)).rejects.toEqual(
    new ApiError(429, 'generation_busy'),
  );
});
it('times out a stalled read so the UI can offer recovery', async () => {
  vi.useFakeTimers();
  let captured!: AbortSignal;
  vi.stubGlobal(
    'fetch',
    vi.fn((_, options) => {
      captured = options.signal;
      return new Promise((_resolve, reject) =>
        captured.addEventListener('abort', () => reject(captured.reason)),
      );
    }),
  );
  const controller = new AbortController();
  const request = fetchHead('match', controller.signal).catch((error) => error);
  await vi.advanceTimersByTimeAsync(15000);
  try {
    expect(captured.aborted).toBe(true);
  } finally {
    controller.abort();
    await request;
  }
});
