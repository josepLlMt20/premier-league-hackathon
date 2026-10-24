import { useEffect, useState } from 'react';
import {
  fetchEvidence,
  type ContextResult,
  type EvidenceBundle,
  type MatchMetadata,
} from '../../api/client';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '../../components/ui/dialog';
import { Button } from '../../components/ui/button';
import { Status } from '../../components/Status';
import {
  copy,
  eventName,
  limitText,
  metricName,
  methodText,
  type Language,
} from '../../domain/copy';
import { clock } from '../../domain/playback';
import { formatInterval } from './CatchUpPanel';
export function EvidencePanel({
  result,
  storyId,
  metadata,
  language,
  close,
  returnFocus,
  open,
}: {
  result: ContextResult;
  storyId?: string;
  metadata: MatchMetadata;
  language: Language;
  close: () => void;
  returnFocus: HTMLElement | null;
  open: boolean;
}) {
  const t = copy[language];
  const card = result.cards.find((card) => card.story_id === storyId);
  const claims = card?.claims || result.summary_claims;
  const factIds = new Set(claims.flatMap((claim) => claim.fact_ids || []));
  const facts = result.facts.filter((fact) => factIds.has(fact.fact_id));
  const eventIds = [
    ...new Set(
      card
        ? [
            ...claims.flatMap((claim) => claim.event_ids || []),
            ...facts.flatMap((fact) => fact.event_ids),
          ]
        : result.evidence_ids,
    ),
  ];
  const [bundle, setBundle] = useState<EvidenceBundle | null>(null),
    [error, setError] = useState(false),
    [attempt, setAttempt] = useState(0);
  // Each mount belongs to one immutable context/request key; unmount aborts and
  // ignores its response even for transports that finish after abort.
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    let current = true;
    setBundle(null);
    setError(false);
    async function load() {
      const chunks = eventIds.length
        ? Array.from({ length: Math.ceil(eventIds.length / 100) }, (_, i) =>
            eventIds.slice(i * 100, i * 100 + 100),
          )
        : [[]];
      const events = new Map<string, EvidenceBundle['events'][number]>(),
        annulled = new Set<string>();
      for (const chunk of chunks) {
        const part = await fetchEvidence(
          metadata.match_id,
          result.request.to_sequence,
          chunk,
          controller.signal,
        );
        if (!current) return;
        if (
          part.snapshot_id !== result.snapshot_id ||
          part.cutoff_sequence !== result.request.to_sequence
        )
          throw new Error('Evidence snapshot mismatch');
        part.events.forEach((event) => events.set(event.event_id, event));
        part.annulled_event_ids.forEach((id) => annulled.add(id));
      }
      if (current)
        setBundle({
          snapshot_id: result.snapshot_id,
          cutoff_sequence: result.request.to_sequence,
          events: [...events.values()].sort((a, b) => a.sequence - b.sequence),
          annulled_event_ids: [...annulled],
        });
    }
    void load().catch(() => {
      if (current) setError(true);
    });
    return () => {
      current = false;
      controller.abort();
    };
    // An EvidencePanel is keyed by requestKey and storyId in its parent.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt, open]);
  return (
    <Dialog
      open={open}
      onOpenChange={(open) => {
        if (!open) close();
      }}
    >
      <DialogContent
        className="evidence-dialog"
        finalFocus={() => returnFocus}
        closeLabel={language === 'es' ? 'Cerrar evidencia' : 'Close evidence'}
      >
        <DialogTitle>{t.evidenceTitle}</DialogTitle>
        <DialogDescription>{t.evidenceHint}</DialogDescription>
        <div className="evidence-scroll" role="region" aria-label={t.evidenceTitle} tabIndex={0}>
          <h3>{t.facts}</h3>
          {facts.length ? (
            <dl className="fact-list">
              {facts.map((fact) => (
                <div key={fact.fact_id}>
                  <dt>
                    {metricName(fact.name, language)} ·{' '}
                    {metadata.teams.find((team) => team.team_id === fact.team_id)?.name}
                  </dt>
                  <dd>
                    <strong className="fact-value mono">
                      {fact.value == null
                        ? '—'
                        : new Intl.NumberFormat(language, { maximumFractionDigits: 3 }).format(
                            fact.value,
                          )}{' '}
                      {fact.unit === 'ratio'
                        ? '(0–1)'
                        : fact.unit === 'heuristic points'
                          ? language === 'es'
                            ? 'puntos heurísticos'
                            : fact.unit
                          : ['%', 'm'].includes(fact.unit)
                            ? fact.unit
                            : ''}
                    </strong>
                    <span>{formatInterval(fact.interval)}</span>
                    <details className="metric-definition">
                      <summary>{language === 'es' ? 'Definición' : 'Definition'}</summary>
                      <p>{methodText(fact.method, language)}</p>
                    </details>
                    <span className="caption">
                      {t.sample}: {fact.sample_count}
                      {fact.denominator != null ? ` · n = ${fact.denominator}` : ''}
                    </span>
                    <ul className="limitations">
                      {fact.limitations.map((limit) => (
                        <li key={limit}>{limitText(limit, language)}</li>
                      ))}
                    </ul>
                    <code className="reference">{fact.fact_id}</code>
                  </dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="caption">{t.noFacts}</p>
          )}
          <h3>{t.events}</h3>
          {error ? (
            <Status language={language} error retry={() => setAttempt((n) => n + 1)}>
              {t.unavailable}
            </Status>
          ) : !bundle ? (
            <Status language={language}>{t.loading}</Status>
          ) : (
            <ol className="evidence-events">
              {bundle.events.map((event) => (
                <li key={event.event_id}>
                  <span className="mono">{clock(event.occurred_second)}</span>
                  <strong>
                    {eventName(event.kind, language)}
                    {bundle.annulled_event_ids.includes(event.event_id) && ` · ${t.annulled}`}
                  </strong>
                  <span>
                    {metadata.teams
                      .flatMap((t) => t.players)
                      .find((p) => p.player_id === event.player_id)?.name ||
                      metadata.teams.find((t) => t.team_id === event.team_id)?.name}
                  </span>
                  <code className="reference">
                    #{event.sequence} · {event.event_id}
                  </code>
                </li>
              ))}
            </ol>
          )}
        </div>
        <Button variant="secondary" onClick={close}>
          {t.back}
        </Button>
      </DialogContent>
    </Dialog>
  );
}
