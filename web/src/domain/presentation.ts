import type { ContextResult } from '../api/client';
import { clock } from './playback';
export function formatInterval(interval: ContextResult['facts'][number]['interval']) {
  return interval.start_second != null && interval.end_second != null
    ? `${clock(interval.start_second)} – ${clock(interval.end_second)}`
    : `#${interval.start_sequence} – #${interval.end_sequence}`;
}
export function factValue(fact: ContextResult['facts'][number], language: 'es' | 'en') {
  const value =
    fact.value == null
      ? '—'
      : new Intl.NumberFormat(language, { maximumFractionDigits: 3 }).format(fact.value);
  const unit =
    fact.unit === 'ratio'
      ? '(0–1)'
      : fact.unit === 'heuristic points'
        ? language === 'es'
          ? 'puntos heurísticos'
          : fact.unit
        : ['%', 'm'].includes(fact.unit)
          ? fact.unit
          : '';
  return `${value}${unit ? ` ${unit}` : ''}`;
}
