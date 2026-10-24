import { useState } from 'react';
import { Card } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { copy } from '../../domain/copy';
import type { ContextPanelProps } from '../viewer/CatchUpPanel';
import { ContextControls } from '../viewer/ContextControls';
import { ShotComparison } from '../viewer/ShotComparison';
import { BriefingCard } from './BriefingCard';
import { OverlayPreview } from './OverlayPreview';
import { TracePanel } from './TracePanel';
import { professionalCopy } from './copy';
import { canExportBriefing, exportBriefing } from './export';
export function Commentator(props: ContextPanelProps) {
  const { state, metadata, loading, error, openEvidence } = props;
  const result = state.context,
    language = state.preferences.language,
    p = professionalCopy[language],
    t = copy[language];
  const [selection, setSelection] = useState('');
  const [exportError, setExportError] = useState(false);
  const frame = result && state.view ? { result, view: state.view, second: state.second } : null;
  const cards = result?.status === 'verified' ? result.cards.slice(0, 3) : [];
  const selected = cards.find((card) => card.story_id === selection) || cards[0];
  const publishable = !!frame && canExportBriefing(frame);
  function download(blob: Blob, filename: string) {
    let url: string | undefined;
    try {
      url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.append(link);
      link.click();
      link.remove();
      setExportError(false);
      const created = url;
      window.setTimeout(() => URL.revokeObjectURL(created), 1000);
    } catch {
      if (url) URL.revokeObjectURL(url);
      setExportError(true);
    }
  }
  return (
    <Card className="commentator-panel">
      <section aria-labelledby="professional-heading">
        <header>
          <p className="window-bar">{p.workspace}</p>
          <h2 id="professional-heading">{p.title}</h2>
          <p className="muted professional-hint">{p.hint}</p>
        </header>
        <div className="professional-controls">
          <ContextControls
            {...props}
            actionLabel={p.action}
            busyLabel={p.generating}
            cancelLabel={p.cancel}
          />
        </div>
        <div className="briefing-export">
          <Button
            variant="outline"
            disabled={!publishable}
            onClick={() => {
              if (frame)
                download(
                  exportBriefing(frame),
                  `touchline-briefing-${result!.request.to_sequence}.json`,
                );
            }}
          >
            {p.download}
          </Button>
          {!publishable && <p className="caption">{p.exportBlocked}</p>}
        </div>
        {exportError && (
          <p role="alert" className="caption">
            {p.exportFailed}
          </p>
        )}
        {!result && !loading && !error && <p className="recap-empty">{p.empty}</p>}
        {result && (
          <div className="professional-result" aria-live="polite">
            <Badge>
              {result.mode === 'scripted'
                ? t.scripted
                : result.status === 'verified'
                  ? t.verified
                  : result.status === 'insufficient'
                    ? t.insufficient
                    : t.factual}
            </Badge>
            {cards.length ? (
              <p className="recap-summary-count caption">{p.stories(cards.length)}</p>
            ) : (
              <p className="recap-summary">{result.summary}</p>
            )}
            {frame &&
              cards.map((card, index) => (
                <BriefingCard
                  key={card.story_id}
                  card={card}
                  frame={frame}
                  index={index}
                  selected={selected?.story_id === card.story_id}
                  select={() => setSelection(card.story_id)}
                  openEvidence={openEvidence}
                />
              ))}
            {!cards.length && (
              <div className="professional-fallback">
                <p>{p.noCards}</p>
                <ShotComparison result={result} metadata={metadata} language={language} />
                {!!result.evidence_ids.length && (
                  <Button
                    variant="outline"
                    onClick={(event) => openEvidence(undefined, event.currentTarget)}
                  >
                    {t.evidence}
                  </Button>
                )}
              </div>
            )}
            {frame && selected && (
              <OverlayPreview frame={frame} storyId={selected.story_id} download={download} />
            )}
            <TracePanel result={result} />
          </div>
        )}
      </section>
    </Card>
  );
}
