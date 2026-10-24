import type { MatchMetadata, MatchView } from '../api/client';
import { copy, type Language } from '../domain/copy';
export function Scoreboard({
  metadata,
  view,
  second,
  language,
}: {
  metadata: MatchMetadata;
  view: MatchView | null;
  second: number;
  language: Language;
}) {
  const t = copy[language];
  return (
    <div className="scoreboard">
      <span className="team home-team">
        <span className="team-monogram" aria-hidden="true">
          {metadata.teams[0].name.slice(0, 2).toUpperCase()}
        </span>
        <strong>{metadata.teams[0].name}</strong>
      </span>
      <div className="score-stack">
        <strong className="score mono" data-testid={view ? 'score' : undefined}>
          {view
            ? metadata.teams
                .map(
                  (team) => view.score.find((score) => score.team_id === team.team_id)?.goals ?? 0,
                )
                .join(' – ')
            : '— – —'}
        </strong>
        <span className="score-period">{second < 2700 ? t.firstHalf : t.secondHalf}</span>
      </div>
      <span className="team away-team">
        <span className="team-monogram" aria-hidden="true">
          {metadata.teams[1].name.slice(0, 2).toUpperCase()}
        </span>
        <strong>{metadata.teams[1].name}</strong>
      </span>
    </div>
  );
}
