import type { MatchView } from '../api/client';
import { clock } from '../domain/playback';
import { copy, eventName, type Language } from '../domain/copy';
export function Timeline({ view, language }: { view: MatchView; language: Language }) {
  const t = copy[language];
  return (
    <details className="recent">
      <summary>
        {t.recent}
        <span className="mono">{view.recent_events.length}</span>
      </summary>
      <p className="caption">{t.recentNote}</p>
      {view.recent_events.length ? (
        <ol className="event-list">
          {[...view.recent_events].reverse().map((event) => (
            <li key={event.event_id}>
              <time className="mono">{clock(event.occurred_second)}</time>
              <span>
                {eventName(event.kind, language)}
                {view.annulled_event_ids.includes(event.event_id) && ` · ${t.annulled}`}
              </span>
              <span className="muted">
                {view.metadata.teams.find((t) => t.team_id === event.team_id)?.name}
              </span>
            </li>
          ))}
        </ol>
      ) : (
        <p>{t.noRecent}</p>
      )}
    </details>
  );
}
