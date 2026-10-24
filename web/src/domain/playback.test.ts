import { describe, expect, it } from 'vitest';
import { initialPlayback, reducePlayback, applyContext, type PlaybackState } from './playback';
import { context, view } from '../test-fixtures';

describe('temporal playback', () => {
  it('keeps the committed moment visible until the next automatic frame is ready', () => {
    const state = { ...initialPlayback(), second: 400, view, context, playing: true };
    const pending = reducePlayback(state, { type: 'advance', headSecond: 1500 });
    expect(pending.second).toBe(400);
    expect(pending.view).toBe(view);
    expect(pending.context).toBe(context);
    expect(pending.requestKey).toBe(state.requestKey);
    expect(reducePlayback(pending, { type: 'advance', headSecond: 1500 })).toBe(pending);
  });
  it('cancels an automatic frame on pause without blanking or accepting its late response', () => {
    const state = { ...initialPlayback(), second: 400, view, playing: true };
    const pending = reducePlayback(state, { type: 'advance', headSecond: 1500 });
    const paused = reducePlayback(pending, { type: 'playing', playing: false });
    expect(paused.second).toBe(400);
    expect(paused.view).toBe(view);
    expect(
      reducePlayback(paused, { type: 'view', view, key: pending.requestKey, second: 401 }),
    ).toBe(paused);
  });
  it('immediately removes later score, context and evidence when rewinding', () => {
    const state = { ...initialPlayback(), second: 900, view, context, evidenceOpen: true };
    const next = reducePlayback(state, { type: 'seek', second: 300 });
    expect(next.second).toBe(300);
    expect(next.view).toBeNull();
    expect(next.context).toBeNull();
    expect(next.evidenceOpen).toBe(false);
    expect(next.requestKey).toBeGreaterThan(state.requestKey);
  });
  it('changes language without moving the cursor and invalidates the old result', () => {
    const state = { ...initialPlayback(), second: 900, view, context };
    const next = reducePlayback(state, {
      type: 'preferences',
      preferences: { ...state.preferences, language: 'en' },
    });
    expect(next.second).toBe(900);
    expect(next.context).toBeNull();
    expect(next.preferences.language).toBe('en');
  });
  it('ignores old responses even if their server trace ID is reused from cache', () => {
    const state = { ...initialPlayback(), view, requestKey: 8 };
    expect(applyContext(state, context, 7).context).toBeNull();
    expect(applyContext(state, context, 8).context).toBe(context);
    const rewound = reducePlayback(state, { type: 'seek', second: 2 });
    expect(applyContext(rewound, context, 8).context).toBeNull();
  });
  it('also rejects a mismatching snapshot for a current request key', () => {
    const state = { ...initialPlayback(), view, requestKey: 8 };
    expect(applyContext(state, { ...context, snapshot_id: 'later' }, 8).context).toBeNull();
  });
  it('pause and speed changes preserve the cursor and bounded data', () => {
    const state = { ...initialPlayback(), second: 400, view, playing: true };
    const next = reducePlayback(reducePlayback(state, { type: 'playing', playing: false }), {
      type: 'speed',
      speed: 5,
    });
    expect(next.second).toBe(400);
    expect(next.view).toBe(view);
    expect(next.playing).toBe(false);
    expect(next.speed).toBe(5);
  });
  it('an advancing shared head cannot restart or slow the viewer timer', () => {
    let state: PlaybackState = { ...initialPlayback(), view, playing: true, speed: 5 };
    state = reducePlayback(state, { type: 'advance', headSecond: 100 });
    state = reducePlayback(state, { type: 'view', view, key: state.requestKey, second: 5 });
    state = reducePlayback(state, { type: 'advance', headSecond: 200 });
    state = reducePlayback(state, { type: 'view', view, key: state.requestKey, second: 10 });
    expect(state.second).toBe(10);
    expect(state.requestKey).toBe(2);
    state = reducePlayback({ ...state, view }, { type: 'advance', headSecond: 12 });
    state = reducePlayback(state, { type: 'view', view, key: state.requestKey, second: 12 });
    expect(state.second).toBe(12);
    state = reducePlayback({ ...state, view }, { type: 'advance', headSecond: 12 });
    expect(state.playing).toBe(false);
    expect(reducePlayback(state, { type: 'advance', headSecond: 100 }).second).toBe(12);
  });
  it('buffers automatic playback while a bounded read is pending, without invalidating it', () => {
    const pending = {
      ...initialPlayback(),
      second: 400,
      playing: true,
      view: null,
      requestKey: 10,
    };
    const tick = reducePlayback(pending, { type: 'advance', headSecond: 1500 });
    expect(tick.second).toBe(400);
    expect(tick.requestKey).toBe(10);
    const rewind = reducePlayback(pending, { type: 'seek', second: 0 });
    expect(rewind.second).toBe(0);
    expect(rewind.requestKey).toBe(11);
  });
});
