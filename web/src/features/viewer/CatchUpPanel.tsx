import { useEffect, useState } from 'react';
import type { ContextResult, MatchMetadata } from '../../api/client';
import { clock, type PlaybackState, type Action } from '../../domain/playback';
import { copy, limitText } from '../../domain/copy';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { NativeSelect } from '../../components/ui/native-select';
import { Status } from '../../components/Status';
import { ShotComparison } from './ShotComparison';
import { ArrowRightLineIcon, SettingsLineIcon, TargetLineIcon } from '../../components/icons';
export function CatchUpPanel({
  state,
  metadata,
  loading,
  error,
  generate,
  cancel,
  dispatch,
  openEvidence,
}: {
  state: PlaybackState;
  metadata: MatchMetadata;
  loading: boolean;
  error: string | null;
  generate: () => void;
  cancel: () => void;
  dispatch: React.Dispatch<Action>;
  openEvidence: (storyId?: string, trigger?: HTMLElement) => void;
}) {
  const t = copy[state.preferences.language],
    result: ContextResult | null = state.context;
  const prefs = state.preferences;
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    setSlow(false);
    if (!loading) return;
    const timer = setTimeout(() => setSlow(true), 10000);
    return () => clearTimeout(timer);
  }, [loading]);
  return (
    <Card className="catchup-panel">
      <section aria-labelledby="catchup-heading">
        <div className="window-bar">
          <span className="recap-heading">
            {prefs.language === 'es' ? 'Contexto del tramo' : 'Interval context'}
          </span>
        </div>
        <div className="catchup-body">
          <h2 id="catchup-heading">{t.catchup}</h2>
          <p className="muted">{t.catchupHint}</p>
          <div className="recap-range">
            <div className="recap-range-labels">
              <label htmlFor="from-time">{t.from}</label>
              <span>{t.to}</span>
            </div>
            <div className="interval-control">
              <output className="mono" htmlFor="from-time">
                {clock(state.fromSecond)}
              </output>
              <input
                id="from-time"
                aria-label={t.from}
                type="range"
                className="time-range"
                min="0"
                max={state.second}
                step="1"
                value={state.fromSecond}
                aria-valuetext={clock(state.fromSecond)}
                onChange={(event) => dispatch({ type: 'from', second: Number(event.target.value) })}
              />
              <span className="interval-end mono" aria-label={`${t.to} ${clock(state.second)}`}>
                {clock(state.second)}
              </span>
            </div>
          </div>
          <details className="preferences">
            <summary>
              <SettingsLineIcon aria-hidden="true" />
              {t.personalize}
              <ArrowRightLineIcon className="disclosure-arrow" aria-hidden="true" />
            </summary>
            <div className="preference-fields">
              <label htmlFor="language">
                {t.language}
                <NativeSelect
                  aria-label={t.language}
                  id="language"
                  value={prefs.language}
                  onChange={(e) =>
                    dispatch({
                      type: 'preferences',
                      preferences: { ...prefs, language: e.target.value as 'es' | 'en' },
                    })
                  }
                >
                  <option value="es">Español</option>
                  <option value="en">English</option>
                </NativeSelect>
              </label>
              <label htmlFor="depth">
                {t.depth}
                <NativeSelect
                  aria-label={t.depth}
                  id="depth"
                  value={prefs.depth}
                  onChange={(e) =>
                    dispatch({
                      type: 'preferences',
                      preferences: { ...prefs, depth: e.target.value as 'simple' | 'detailed' },
                    })
                  }
                >
                  <option value="simple">{t.simple}</option>
                  <option value="detailed">{t.detailed}</option>
                </NativeSelect>
              </label>
              <label className="favorite-field" htmlFor="favorite">
                {t.team}
                <NativeSelect
                  aria-label={t.team}
                  id="favorite"
                  value={prefs.favorite_team_id || ''}
                  onChange={(e) =>
                    dispatch({
                      type: 'preferences',
                      preferences: { ...prefs, favorite_team_id: e.target.value || null },
                    })
                  }
                >
                  <option value="">{t.neutral}</option>
                  {metadata.teams.map((team) => (
                    <option key={team.team_id} value={team.team_id}>
                      {team.name}
                    </option>
                  ))}
                </NativeSelect>
              </label>
            </div>
          </details>
          <Button
            className="catchup-action"
            size="lg"
            disabled={!state.view || state.second === state.fromSecond || loading}
            onClick={generate}
          >
            {loading ? t.generating : t.action}
            <ArrowRightLineIcon className="action-arrow" aria-hidden="true" />
          </Button>
          {loading && (
            <Button variant="secondary" className="cancel-action" onClick={cancel}>
              {t.cancel}
            </Button>
          )}
          {error && (
            <Status language={prefs.language} error>
              {error}
            </Status>
          )}
          {loading && (
            <p role="status" className="caption pending">
              {slow ? t.slow : t.generating}
            </p>
          )}
          {!result && !loading && !error && <p className="recap-empty">{t.ready}</p>}
          {result && (
            <div key={state.requestKey} className="recap-result" aria-live="polite">
              <Badge>
                {result.mode === 'scripted'
                  ? t.scripted
                  : result.status === 'verified'
                    ? t.verified
                    : result.status === 'insufficient'
                      ? t.insufficient
                      : t.factual}
              </Badge>
              <ShotComparison result={result} metadata={metadata} language={prefs.language} />
              <p className="recap-summary">{result.summary}</p>
              {result.status === 'factual' && <p className="caption">{t.factualNote}</p>}
              {result.status === 'insufficient' && <p className="caption">{t.insufficientNote}</p>}
              {!!result.evidence_ids.length && (
                <Button
                  variant="outline"
                  onClick={(event) => openEvidence(undefined, event.currentTarget)}
                >
                  <TargetLineIcon aria-hidden="true" />
                  {t.evidence}
                </Button>
              )}
              {result.cards.map((card, index) => (
                <article className="story" key={card.story_id}>
                  <span className="story-number mono">{String(index + 1).padStart(2, '0')}</span>
                  <h3>{card.headline}</h3>
                  <p>{card.explanation}</p>
                  <p className="caption">
                    {t.interval}: {formatInterval(card.current_interval)}
                    <br />
                    {t.comparison}: {formatInterval(card.comparison_interval)}
                  </p>
                  {!!card.limitations.length && (
                    <ul className="limitations">
                      {card.limitations.map((limit) => (
                        <li key={limit}>{limitText(limit, prefs.language)}</li>
                      ))}
                    </ul>
                  )}
                  <Button
                    variant="outline"
                    onClick={(event) => openEvidence(card.story_id, event.currentTarget)}
                  >
                    {t.evidence} · {index + 1}
                  </Button>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </Card>
  );
}
export function formatInterval(interval: ContextResult['facts'][number]['interval']) {
  return interval.start_second != null && interval.end_second != null
    ? `${clock(interval.start_second)} – ${clock(interval.end_second)}`
    : `#${interval.start_sequence} – #${interval.end_sequence}`;
}
