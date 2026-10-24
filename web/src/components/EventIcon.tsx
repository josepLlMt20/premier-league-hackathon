import type { SVGProps } from 'react';
import type { MatchEvent } from '../api/client';
import { ArrowRightLineIcon, CloseLineIcon, FootballLineIcon, TargetLineIcon } from './icons';
export function EventIcon({
  kind,
  ...props
}: SVGProps<SVGSVGElement> & { kind: MatchEvent['kind'] }) {
  const Icon =
    kind === 'pass' || kind === 'turnover'
      ? ArrowRightLineIcon
      : kind === 'shot' || kind === 'pressure'
        ? TargetLineIcon
        : kind === 'correction'
          ? CloseLineIcon
          : FootballLineIcon;
  return <Icon className="event-icon" aria-hidden="true" {...props} />;
}
