import type { ContextResult } from '../../api/client';
import { copy, limitText } from '../../domain/copy';
import { formatInterval } from '../../domain/presentation';
import { Button } from '../../components/ui/button';
import { Card } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { TargetLineIcon } from '../../components/icons';
import { ShotComparison } from './ShotComparison';
import { ContextControls, type ContextControlsProps } from './ContextControls';
export type ContextPanelProps = ContextControlsProps & {
  openEvidence: (storyId?: string, trigger?: HTMLElement) => void;
};
export function CatchUpPanel(props: ContextPanelProps) {
  const { state, loading, error, openEvidence, metadata } = props;
  const t = copy[state.preferences.language],
    result: ContextResult | null = state.context;
  const prefs = state.preferences;
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
          <ContextControls {...props} />
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
