import type { ContextResult } from '../../api/client';
import { professionalCopy } from './copy';
export function TracePanel({ result }: { result: ContextResult }) {
  const p = professionalCopy[result.request.language];
  const roles = { analyst: p.analyst, writer: p.writer, reviewer: p.reviewer, system: p.system };
  const decisions: Record<string, string> = {
    started: p.started,
    candidates_prefetched: p.prefetched,
    repair_requested: p.repair,
    accepted: p.accepted,
    rejected: p.rejected,
    factual_fallback: p.fallback,
  };
  return (
    <details className="trace-panel">
      <summary>{p.trace}</summary>
      {result.trace?.steps.length ? (
        <ol>
          {result.trace.steps.map((step, i) => (
            <li key={i}>
              <strong>{roles[step.role]}</strong>
              <span>{decisions[step.decision] || p.step}</span>
            </li>
          ))}
        </ol>
      ) : (
        <p className="caption">{p.noTrace}</p>
      )}
      <div className="trace-counts">
        <p>
          {p.modelCalls}: {result.trace?.model_calls ?? '—'}
        </p>
        <p>
          {p.toolCalls}: {result.trace?.tool_calls ?? '—'}
        </p>
      </div>
      {!!result.rejection_codes.length && <p className="caption">{p.rejectedNote}</p>}
    </details>
  );
}
