import { Button } from '../../components/ui/button';
import { clock } from '../../domain/playback';
import { professionalCopy } from './copy';
import { overlayFor, type ContextFrame, type OverlayPayload } from './export';
export function OverlayPreview({
  frame,
  storyId,
  download,
}: {
  frame: ContextFrame;
  storyId: string;
  download: (blob: Blob, filename: string) => void;
}) {
  const p = professionalCopy[frame.result.request.language];
  let overlay: OverlayPayload;
  try {
    overlay = overlayFor(frame, storyId);
  } catch {
    return (
      <p className="caption" role="status">
        {p.invalidOverlay}
      </p>
    );
  }
  return (
    <section className="overlay-preview" aria-labelledby="overlay-heading">
      <div className="section-heading">
        <h3 id="overlay-heading">{p.overlay}</h3>
        <span className="caption mono">{Array.from(overlay.text).length}/140</span>
      </div>
      <div className="overlay-stage">
        <p className="overlay-stage-note">{p.previewNote}</p>
        <div key={overlay.story_id} className="overlay-graphic">
          <div className="overlay-meta">
            <span>{p.synthetic}</span>
            <time className="mono">{clock(overlay.displayed_second)}</time>
          </div>
          <strong>{overlay.text}</strong>
          <span className="overlay-kind">
            {overlay.claim_kind === 'interpretation' ? p.interpretation : p.observed}
          </span>
          <ul>
            {overlay.limitations.map((limit) => (
              <li key={limit}>{limit}</li>
            ))}
          </ul>
        </div>
      </div>
      <Button
        variant="outline"
        onClick={() =>
          download(
            new Blob([JSON.stringify(overlay, null, 2) + '\n'], {
              type: 'application/json;charset=utf-8',
            }),
            `touchline-overlay-${overlay.cutoff_sequence}.json`,
          )
        }
      >
        {p.downloadOverlay}
      </Button>
    </section>
  );
}
