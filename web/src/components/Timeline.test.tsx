import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { Timeline } from './Timeline';
import { event, view } from '../test-fixtures';
it('seeks a received correction at its availability time, preserving its annulled target label', () => {
  const seek = vi.fn();
  const bounded = {
    ...view,
    cutoff_sequence: 3,
    available_second: 500,
    recent_events: [
      event,
      {
        ...event,
        event_id: 'late-correction',
        sequence: 3,
        kind: 'correction' as const,
        occurred_second: 410,
        available_second: 500,
        start: null,
        end: null,
        attributes: { target_event_id: event.event_id, action: 'annul' as const },
      },
    ],
    annulled_event_ids: [event.event_id],
  };
  render(<Timeline view={bounded} language="es" onSeek={seek} />);
  fireEvent.click(screen.getByRole('button', { name: 'Ir a Corrección · 08:20' }));
  expect(seek).toHaveBeenCalledWith(500);
  fireEvent.click(screen.getByText(/Acciones recientes/));
  expect(screen.getAllByText(/Anulado/).length).toBeGreaterThan(0);
});
it('offers only three received events and has no navigation for an empty prefix', () => {
  const seek = vi.fn();
  const { rerender } = render(
    <Timeline
      view={{
        ...view,
        recent_events: [1, 2, 3, 4].map((n) => ({
          ...event,
          event_id: `e${n}`,
          sequence: n,
          occurred_second: n * 10,
          available_second: n * 10,
        })),
      }}
      language="en"
      onSeek={seek}
    />,
  );
  expect(screen.getAllByRole('button')).toHaveLength(3);
  expect(screen.getAllByRole('button').map((button) => button.getAttribute('aria-label'))).toEqual([
    'Go to Pass · 00:20',
    'Go to Pass · 00:30',
    'Go to Pass · 00:40',
  ]);
  expect(screen.getAllByRole('button').at(-1)).toHaveAttribute('aria-current', 'step');
  expect(screen.queryByRole('button', { name: 'Go to Pass · 00:10' })).not.toBeInTheDocument();
  rerender(<Timeline view={{ ...view, recent_events: [] }} language="en" onSeek={seek} />);
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
});
