import { useEffect, useReducer, useRef, useState } from 'react';
import {
  ApiError,
  fetchHead,
  fetchView,
  requestContext,
  resolveCursor,
  type MatchHead,
  type MatchMetadata,
} from '../../api/client';
import {
  initialPlayback,
  reducePlayback,
  readPreferences,
  preferenceKey,
  clock,
} from '../../domain/playback';
import { copy } from '../../domain/copy';
import { Pitch } from '../../components/Pitch';
import { Timeline } from '../../components/Timeline';
import { Status } from '../../components/Status';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { PlaybackControls } from './PlaybackControls';
import { CatchUpPanel } from './CatchUpPanel';
import { EvidencePanel } from './EvidencePanel';
export function Viewer({
  metadata,
  onLanguageChange,
}: {
  metadata: MatchMetadata;
  onLanguageChange?: (language: 'es' | 'en') => void;
}) {
  const [state, dispatch] = useReducer(reducePlayback, undefined, () => {
    const preferences = readPreferences();
    if (!metadata.teams.some((team) => team.team_id === preferences.favorite_team_id))
      preferences.favorite_team_id = null;
    return { ...initialPlayback(), preferences };
  });
  const [head, setHead] = useState<MatchHead | null>(null),
    [headError, setHeadError] = useState(false);
  const [viewError, setViewError] = useState(false),
    [attempt, setAttempt] = useState(0);
  const [contextLoading, setContextLoading] = useState(false),
    [contextError, setContextError] = useState<string | null>(null);
  const [storyId, setStoryId] = useState<string | undefined>();
  const [evidenceSelected, setEvidenceSelected] = useState(false);
  const currentKey = useRef(state.requestKey);
  currentKey.current = state.requestKey;
  const generation = useRef<AbortController | null>(null),
    evidenceTrigger = useRef<HTMLElement | null>(null);
  const headSecond = useRef(0);
  headSecond.current = head?.available_second || 0;
  const t = copy[state.preferences.language];
  useEffect(() => {
    try {
      localStorage.setItem(preferenceKey, JSON.stringify(state.preferences));
    } catch {
      /* Storage is optional. */
    }
    document.documentElement.lang = state.preferences.language;
    onLanguageChange?.(state.preferences.language);
  }, [state.preferences, onLanguageChange]);
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const next = await fetchHead(metadata.match_id, controller.signal);
        if (active) {
          setHead(next);
          setHeadError(false);
        }
      } catch {
        if (active) setHeadError(true);
      } finally {
        if (active)
          timer = setTimeout(() => {
            void poll();
          }, 2000);
      }
    }
    void poll();
    return () => {
      active = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [metadata.match_id]);
  useEffect(() => {
    if (!head) return;
    const controller = new AbortController(),
      key = state.requestKey;
    let active = true;
    setViewError(false);
    void resolveCursor(metadata.match_id, state.second, controller.signal)
      .then((cursor) => {
        if (!active || currentKey.current !== key) return null;
        return fetchView(metadata.match_id, cursor.to_sequence, controller.signal);
      })
      .then((view) => {
        if (view && active && currentKey.current === key) dispatch({ type: 'view', view, key });
      })
      .catch(() => {
        if (active && currentKey.current === key) setViewError(true);
      });
    return () => {
      active = false;
      controller.abort();
    };
    // A newly polled head must not reload an already selected historical frame.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metadata.match_id, state.requestKey, !!head, attempt]);
  useEffect(() => {
    generation.current?.abort();
    setContextLoading(false);
    setContextError(null);
    return () => generation.current?.abort();
  }, [state.requestKey]);
  useEffect(() => {
    if (!state.playing || state.evidenceOpen) return;
    const timer = window.setInterval(() => {
      dispatch({ type: 'advance', headSecond: headSecond.current });
    }, 1000);
    return () => clearInterval(timer);
  }, [state.playing, state.evidenceOpen]);
  async function generate() {
    if (!state.view) return;
    generation.current?.abort();
    const controller = new AbortController();
    generation.current = controller;
    const key = state.requestKey,
      view = state.view;
    dispatch({ type: 'playing', playing: false });
    setContextLoading(true);
    setContextError(null);
    try {
      const from = await resolveCursor(metadata.match_id, state.fromSecond, controller.signal);
      if (controller.signal.aborted || key !== currentKey.current) return;
      const result = await requestContext(
        {
          match_id: metadata.match_id,
          from_sequence: from.to_sequence,
          to_sequence: view.cutoff_sequence,
          role: 'fan',
          ...state.preferences,
        },
        controller.signal,
      );
      if (!controller.signal.aborted && key === currentKey.current) {
        if (result.snapshot_id !== view.snapshot_id) throw new Error('Context snapshot mismatch');
        dispatch({ type: 'context', result, key });
      }
    } catch (error) {
      if (!controller.signal.aborted && key === currentKey.current)
        setContextError(error instanceof ApiError && error.status === 429 ? t.busy : t.unavailable);
    } finally {
      if (!controller.signal.aborted && key === currentKey.current) setContextLoading(false);
    }
  }
  return (
    <>
      <div className="match-intro">
        <div>
          <Badge>{t.synthetic}</Badge>
          <h1>{t.tagline}</h1>
        </div>
        <span className="intro-note">{t.watch}</span>
      </div>
      <div className="viewer-grid">
        <Card className="match-panel">
          <section aria-label={t.match}>
            <div className="window-bar">
              <span>
                {t.watching} <strong className="mono">{clock(state.second)}</strong>
              </span>
              <Badge>{state.playing ? t.playing : t.paused}</Badge>
            </div>
            {viewError ? (
              <Status
                language={state.preferences.language}
                error
                retry={() => setAttempt((n) => n + 1)}
              >
                {t.unavailable}
              </Status>
            ) : state.view ? (
              <div data-testid="match-view" data-cutoff={state.view.cutoff_sequence}>
                <div className="scoreboard">
                  <span className="team home-team">
                    <span className="team-monogram" aria-hidden="true">
                      {metadata.teams[0].name.slice(0, 1)}
                    </span>
                    <strong>{metadata.teams[0].name}</strong>
                  </span>
                  <strong className="score mono" data-testid="score">
                    {metadata.teams
                      .map(
                        (team) =>
                          state.view!.score.find((score) => score.team_id === team.team_id)
                            ?.goals ?? 0,
                      )
                      .join(' – ')}
                  </strong>
                  <span className="team away-team">
                    <span className="team-monogram" aria-hidden="true">
                      {metadata.teams[1].name.slice(0, 1)}
                    </span>
                    <strong>{metadata.teams[1].name}</strong>
                  </span>
                </div>
                <Pitch view={state.view} language={state.preferences.language} />
              </div>
            ) : (
              <Status language={state.preferences.language}>{t.loading}</Status>
            )}
            {head && (
              <PlaybackControls
                state={state}
                headSecond={head.available_second}
                dispatch={dispatch}
              />
            )}
            {headError && (
              <Status language={state.preferences.language} error>
                {t.headError}
              </Status>
            )}
            {head?.ingestion_state === 'failed' && (
              <Status language={state.preferences.language} error>
                {t.failed}
              </Status>
            )}
            {head?.ingestion_state === 'complete' && (
              <p className="caption ingestion-note">{t.complete}</p>
            )}
            {state.view && !viewError && (
              <Timeline view={state.view} language={state.preferences.language} />
            )}
          </section>
        </Card>
        <CatchUpPanel
          state={state}
          metadata={metadata}
          loading={contextLoading}
          error={contextError}
          generate={() => {
            void generate();
          }}
          cancel={() => {
            generation.current?.abort();
            setContextLoading(false);
          }}
          dispatch={dispatch}
          openEvidence={(id, trigger) => {
            evidenceTrigger.current = trigger || null;
            setEvidenceSelected(true);
            setStoryId(id);
            dispatch({ type: 'evidence', open: true });
          }}
        />
      </div>
      {evidenceSelected && state.context && (
        <EvidencePanel
          open={state.evidenceOpen}
          key={`${state.requestKey}:${storyId || 'summary'}`}
          result={state.context}
          storyId={storyId}
          metadata={metadata}
          language={state.preferences.language}
          close={() => dispatch({ type: 'evidence', open: false })}
          returnFocus={evidenceTrigger.current}
        />
      )}
    </>
  );
}
