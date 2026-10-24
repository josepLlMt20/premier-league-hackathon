import { useEffect, useState } from 'react';
import type { MatchMetadata } from '../../api/client';
import { clock, type PlaybackState, type Action } from '../../domain/playback';
import { copy } from '../../domain/copy';
import { Button } from '../../components/ui/button';
import { NativeSelect } from '../../components/ui/native-select';
import { Status } from '../../components/Status';
import { ArrowRightLineIcon, SettingsLineIcon } from '../../components/icons';
export type ContextControlsProps = {
  state: PlaybackState;
  metadata: MatchMetadata;
  loading: boolean;
  error: string | null;
  generate: () => void;
  cancel: () => void;
  dispatch: React.Dispatch<Action>;
  actionLabel?: string;
  busyLabel?: string;
  cancelLabel?: string;
};
export function ContextControls({
  state,
  metadata,
  loading,
  error,
  generate,
  cancel,
  dispatch,
  actionLabel,
  busyLabel,
  cancelLabel,
}: ContextControlsProps) {
  const prefs = state.preferences,
    t = copy[prefs.language];
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    setSlow(false);
    if (!loading) return;
    const timer = setTimeout(() => setSlow(true), 10000);
    return () => clearTimeout(timer);
  }, [loading]);
  return (
    <>
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
        {loading ? busyLabel || t.generating : actionLabel || t.action}
        <ArrowRightLineIcon className="action-arrow" aria-hidden="true" />
      </Button>
      {loading && (
        <Button variant="secondary" className="cancel-action" onClick={cancel}>
          {cancelLabel || t.cancel}
        </Button>
      )}
      {error && (
        <Status language={prefs.language} error>
          {error}
        </Status>
      )}
      {loading && (
        <p role="status" className="caption pending">
          {slow ? t.slow : busyLabel || t.generating}
        </p>
      )}
    </>
  );
}
