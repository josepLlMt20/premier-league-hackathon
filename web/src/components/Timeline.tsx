import type { MatchView } from '../api/client';
import { clock } from '../domain/playback';
import { copy, eventName, type Language } from '../domain/copy';
import { Button } from './ui/button';
import { EventIcon } from './EventIcon';
export function Timeline({
  view,
  language,
  onSeek,
}: {
  view: MatchView;
  language: Language;
  onSeek: (second: number) => void;
}) {
  const t = copy[language];
  return (
    <div className="match-timeline">
      {!!view.recent_events.length && (
        <>
          <div className="sequence-heading">
            <h2>{language === 'es' ? 'Secuencia reciente' : 'Recent sequence'}</h2>
            <span className="caption">
              {language === 'es' ? 'Por orden de recepción' : 'In received order'}
            </span>
          </div>
          <div className="moment-rail" role="group" aria-label={t.moments}>
            {view.recent_events.slice(-3).map((event, index, events) => (
              <Button
                key={event.event_id}
                variant="outline"
                className="moment-button"
                aria-current={index === events.length - 1 ? 'step' : undefined}
                aria-label={`${t.seekEvent} ${eventName(event.kind, language)} · ${clock(event.available_second)}`}
                onClick={() => onSeek(event.available_second)}
              >
                <EventIcon kind={event.kind} />
                <span>
                  <time className="mono">{clock(event.available_second)}</time>
                  <span>{eventName(event.kind, language)}</span>
                </span>
              </Button>
            ))}
          </div>
        </>
      )}
      <details className="recent">
        <summary>
          {t.recent}
          <span className="mono">{view.recent_events.length}</span>
        </summary>
        <p className="caption">{t.recentNote}</p>
        {view.recent_events.length ? (
          <ol className="event-list" tabIndex={0} aria-label={t.recent}>
            {[...view.recent_events].reverse().map((event) => (
              <li key={event.event_id}>
                <time className="mono">{clock(event.occurred_second)}</time>
                <span className="event-kind">
                  <EventIcon kind={event.kind} />
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
    </div>
  );
}
