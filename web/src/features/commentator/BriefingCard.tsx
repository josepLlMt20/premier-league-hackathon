import { useState } from 'react';
import { Button } from '../../components/ui/button';
import { copy, limitText, metricName } from '../../domain/copy';
import { factValue, formatInterval } from '../../domain/presentation';
import { professionalCopy } from './copy';
import { canExportBriefing, type ContextFrame } from './export';
type Card = ContextFrame['result']['cards'][number];
export function BriefingCard({
  card,
  frame,
  index,
  selected,
  select,
  openEvidence,
}: {
  card: Card;
  frame: ContextFrame;
  index: number;
  selected: boolean;
  select: () => void;
  openEvidence: (storyId?: string, trigger?: HTMLElement) => void;
}) {
  const language = frame.result.request.language,
    p = professionalCopy[language],
    t = copy[language];
  const [copied, setCopied] = useState<'ok' | 'error' | null>(null);
  const factIds = new Set(card.claims.flatMap((claim) => claim.fact_ids || []));
  const facts = frame.result.facts.filter((fact) => factIds.has(fact.fact_id));
  const publishable = canExportBriefing(frame);
  async function copyLine() {
    try {
      await navigator.clipboard.writeText([card.suggested_line, ...card.limitations].join('\n'));
      setCopied('ok');
    } catch {
      setCopied('error');
    }
  }
  return (
    <article
      className={`briefing-card${selected ? ' briefing-selected' : ''}`}
      aria-labelledby={`briefing-${index}`}
    >
      <header className="briefing-card-header">
        <span className="story-number mono">{String(index + 1).padStart(2, '0')}</span>
        <span className="caption">{formatInterval(card.current_interval)}</span>
      </header>
      <h3 id={`briefing-${index}`}>{card.headline}</h3>
      <div className="briefing-section">
        <div className="briefing-label">
          <strong>{p.changed}</strong>
          <span>{card.claims[1]?.kind === 'interpretation' ? p.interpretation : p.observed}</span>
        </div>
        <p>{card.explanation}</p>
      </div>
      <div className="briefing-section">
        <div className="briefing-label">
          <strong>{p.line}</strong>
          <span>{card.claims[2]?.kind === 'interpretation' ? p.interpretation : p.observed}</span>
        </div>
        <blockquote>{card.suggested_line}</blockquote>
      </div>
      {!!facts.length && (
        <details className="briefing-facts">
          <summary>
            {p.facts} · {facts.length}
          </summary>
          <dl>
            {facts.map((fact) => (
              <div key={fact.fact_id}>
                <dt>
                  {metricName(fact.name, language)} ·{' '}
                  {frame.view.metadata.teams.find((team) => team.team_id === fact.team_id)?.name}
                </dt>
                <dd>
                  <strong className="mono">{factValue(fact, language)}</strong>
                  <span className="caption">{formatInterval(fact.interval)}</span>
                </dd>
              </div>
            ))}
          </dl>
        </details>
      )}
      <p className="caption briefing-intervals">
        {t.interval}: {formatInterval(card.current_interval)}
        <br />
        {t.comparison}: {formatInterval(card.comparison_interval)}
      </p>
      <ul className="limitations">
        {card.limitations.map((limit) => (
          <li key={limit}>{limitText(limit, language)}</li>
        ))}
      </ul>
      <div className="briefing-actions">
        <Button
          variant="outline"
          disabled={!publishable}
          onClick={() => {
            void copyLine();
          }}
        >
          {p.copy}
        </Button>
        <Button
          variant="ghost"
          onClick={(event) => openEvidence(card.story_id, event.currentTarget)}
        >
          {t.evidence} · {index + 1}
        </Button>
        <Button
          variant="secondary"
          aria-pressed={selected}
          disabled={!publishable}
          onClick={select}
        >
          {p.select}
        </Button>
      </div>
      {copied && (
        <p role="status" className="caption copy-status">
          {copied === 'ok' ? p.copied : p.copyFailed}
        </p>
      )}
    </article>
  );
}
