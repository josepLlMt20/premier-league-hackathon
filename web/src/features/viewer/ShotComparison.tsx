import type { ContextResult, MatchMetadata } from '../../api/client';
import type { Language } from '../../domain/copy';

export function ShotComparison({
  result,
  metadata,
  language,
}: {
  result: ContextResult;
  metadata: MatchMetadata;
  language: Language;
}) {
  if (metadata.match_id !== result.request.match_id || metadata.teams.length !== 2) return null;
  const counts = metadata.teams.map((team) => {
    const facts = result.facts.filter(
      (fact) =>
        fact.name === 'shots' &&
        fact.team_id === team.team_id &&
        fact.interval.start_sequence === result.request.from_sequence &&
        fact.interval.end_sequence === result.request.to_sequence &&
        fact.interval.start_second == null &&
        fact.interval.end_second == null,
    );
    const fact = facts[0];
    return facts.length === 1 &&
      fact.snapshot_id === result.snapshot_id &&
      fact.cutoff_sequence === result.request.to_sequence &&
      fact.unit === 'shots' &&
      fact.value != null &&
      Number.isSafeInteger(fact.value) &&
      fact.value >= 0
      ? fact.value
      : null;
  });
  if (counts.some((count) => count == null)) return null;
  const [home, away] = counts as [number, number];
  const max = Math.max(home, away, 1);
  const shots = language === 'es' ? 'tiros' : 'shots';
  return (
    <section
      className="shot-comparison"
      aria-label={language === 'es' ? 'Tiros en el tramo' : 'Shots in this interval'}
    >
      <h3>
        {home} {shots} {language === 'es' ? 'frente a' : 'to'} {away}
      </h3>
      {metadata.teams.map((team, index) => (
        <div className={`shot-row ${index ? 'shot-away' : 'shot-home'}`} key={team.team_id}>
          <span className="club-dot" aria-hidden="true" />
          <span className="shot-team">{team.name}</span>
          <strong className="mono">{counts[index]}</strong>
          <meter
            min={0}
            max={max}
            value={counts[index]!}
            aria-label={`${team.name}: ${counts[index]} ${shots}`}
          />
        </div>
      ))}
    </section>
  );
}
