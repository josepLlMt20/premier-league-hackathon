import { Button } from '../../components/ui/button';
import { PlayLineIcon, PauseLineIcon, FastRewindLineIcon } from '../../components/icons';
import { clock, type PlaybackState, type Action } from '../../domain/playback';
import { copy } from '../../domain/copy';
export function PlaybackControls({
  state,
  headSecond,
  dispatch,
}: {
  state: PlaybackState;
  headSecond: number;
  dispatch: React.Dispatch<Action>;
}) {
  const t = copy[state.preferences.language];
  return (
    <div className="playback-controls">
      <label className="range-label" htmlFor="match-time">
        <span>{t.time}</span>
        <output className="mono" data-testid="playback-clock">
          {clock(state.second)}
        </output>
      </label>
      <input
        id="match-time"
        className="time-range"
        type="range"
        aria-label={t.time}
        min="0"
        max={headSecond}
        step="1"
        value={state.second}
        aria-valuetext={clock(state.second)}
        onChange={(event) => dispatch({ type: 'seek', second: Number(event.target.value) })}
      />
      <div className="playback-row">
        <Button
          className="play-button"
          variant="secondary"
          aria-label={t.rewind}
          title={t.rewind}
          disabled={state.second === 0}
          onClick={() => dispatch({ type: 'seek', second: Math.max(0, state.second - 30) })}
        >
          <FastRewindLineIcon aria-hidden="true" />
        </Button>
        <Button
          variant="secondary"
          disabled={!headSecond}
          onClick={() => dispatch({ type: 'playing', playing: !state.playing })}
        >
          {state.playing ? (
            <PauseLineIcon aria-hidden="true" />
          ) : (
            <PlayLineIcon aria-hidden="true" />
          )}
          {state.playing ? t.pause : t.play}
        </Button>
        <label className="speed-label" htmlFor="speed">
          {t.speed}
          <select
            aria-label={t.speed}
            id="speed"
            value={state.speed}
            onChange={(event) => dispatch({ type: 'speed', speed: Number(event.target.value) })}
          >
            {[1, 5, 15, 30].map((speed) => (
              <option key={speed} value={speed}>
                {speed}×
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="received-row">
        <span>
          {t.received} <strong className="mono">{clock(headSecond)}</strong>
        </span>
        <Button
          variant="ghost"
          disabled={state.second === headSecond}
          onClick={() => dispatch({ type: 'seek', second: headSecond })}
        >
          {t.latest}
        </Button>
      </div>
    </div>
  );
}
