import { useId } from 'react';
import type { MatchMetadata, MatchView } from '../api/client';
import { clock } from '../domain/playback';
import { copy, eventName, type Language } from '../domain/copy';
import { EventIcon } from './EventIcon';
import { FootballLineIcon } from './icons';
export function Pitch({
  view,
  metadata,
  language,
  animateEvent = false,
}: {
  view: MatchView | null;
  metadata: MatchMetadata;
  language: Language;
  animateEvent?: boolean;
}) {
  const t = copy[language],
    id = useId().replaceAll(':', '');
  const event = view?.recent_events.at(-1);
  const annulled = event && view?.annulled_event_ids.includes(event.event_id);
  const team = metadata.teams.find((team) => team.team_id === event?.team_id);
  const player = team?.players.find((player) => player.player_id === event?.player_id);
  const label = event?.start
    ? {
        x: Math.max(1, Math.min(66, event.start.x - 26)),
        y: event.start.y > 15 ? event.start.y - 12 : event.start.y + 5,
        text: `${eventName(event.kind, language)} · ${player?.name || team?.name}${annulled ? ` · ${t.annulled}` : ''}`,
      }
    : null;
  return (
    <figure className="pitch-figure">
      <div className="pitch-heading">
        <span>{t.pitch}</span>
        <span className="mono">{event ? clock(event.occurred_second) : '00:00'}</span>
      </div>
      <div className="pitch-wrap">
        <svg
          className="pitch"
          viewBox="-5 -5 115 78"
          role="img"
          aria-labelledby={`${id}-title ${id}-desc`}
        >
          <title id={`${id}-title`}>
            {event
              ? `${eventName(event.kind, language)} · ${team?.name} · ${clock(event.occurred_second)}`
              : view
                ? t.noEvent
                : t.buffering}
          </title>
          <desc id={`${id}-desc`}>{t.pitchNote}</desc>
          <defs>
            <pattern id={`${id}-stripes`} width="21" height="68" patternUnits="userSpaceOnUse">
              <rect width="10.5" height="68" className="pitch-stripe" />
            </pattern>
            <marker
              id={`${id}-arrow`}
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="4"
              markerHeight="4"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" className="trajectory-head" />
            </marker>
          </defs>
          <rect x="-5" y="-5" width="115" height="78" rx="3" className="pitch-grass" />
          <rect width="105" height="68" fill={`url(#${id}-stripes)`} />
          <g className="pitch-lines">
            <rect width="105" height="68" />
            <path d="M52.5 0v68" />
            <circle cx="52.5" cy="34" r="9.15" />
            <rect y="13.84" width="16.5" height="40.32" />
            <rect x="88.5" y="13.84" width="16.5" height="40.32" />
            <rect y="24.84" width="5.5" height="18.32" />
            <rect x="99.5" y="24.84" width="5.5" height="18.32" />
            <rect x="-2" y="30.34" width="2" height="7.32" />
            <rect x="105" y="30.34" width="2" height="7.32" />
          </g>
          <g className="pitch-spots">
            <circle cx="52.5" cy="34" r=".5" />
            <circle cx="11" cy="34" r=".5" />
            <circle cx="94" cy="34" r=".5" />
          </g>
          {event?.start && (
            <g
              key={event.event_id}
              className={`event-mark${annulled ? ' event-annulled' : ''}${animateEvent ? ' event-arriving' : ''}`}
            >
              {event.end && (
                <line
                  className="trajectory"
                  pathLength="1"
                  x1={event.start.x}
                  y1={event.start.y}
                  x2={event.end.x}
                  y2={event.end.y}
                  markerEnd={`url(#${id}-arrow)`}
                />
              )}
              <circle className="event-halo" cx={event.start.x} cy={event.start.y} r="3" />
              <circle className="event-point" cx={event.start.x} cy={event.start.y} r="1.6" />
              {event.end && (
                <circle className="event-endpoint" cx={event.end.x} cy={event.end.y} r="1.2" />
              )}
              {label && (
                <g className="pitch-callout" aria-hidden="true">
                  <line
                    x1={Math.min(label.x + 34, event.start.x)}
                    y1={label.y + (label.y < event.start.y ? 5.5 : 0)}
                    x2={event.start.x}
                    y2={event.start.y}
                    className="callout-leader"
                  />
                  <rect
                    x={label.x}
                    y={label.y}
                    width="36"
                    height="5.5"
                    rx="0.5"
                    className="callout-surface"
                  />
                  <text x={label.x + 1.2} y={label.y + 3.7} className="callout-text">
                    {label.text.length > 27 ? `${label.text.slice(0, 26)}…` : label.text}
                  </text>
                </g>
              )}
            </g>
          )}
        </svg>
        {!event && (
          <div className="pitch-empty" aria-hidden="true">
            <FootballLineIcon />
          </div>
        )}
      </div>
      <figcaption>
        <div className="event-caption">
          {event ? (
            <>
              <span
                className={`event-symbol ${metadata.teams[0].team_id === event.team_id ? 'event-home' : 'event-away'}`}
              >
                <EventIcon kind={event.kind} />
              </span>
              <strong>
                {eventName(event.kind, language)}
                {annulled ? ` · ${t.annulled}` : ''}
              </strong>
              <span>{player?.name || team?.name}</span>
            </>
          ) : (
            <span role={view ? undefined : 'status'}>{view ? t.noEvent : t.buffering}</span>
          )}
        </div>
        <p className="caption">{t.pitchNote}</p>
      </figcaption>
    </figure>
  );
}
