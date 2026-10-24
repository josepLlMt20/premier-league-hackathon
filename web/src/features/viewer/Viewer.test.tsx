import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { Viewer } from './Viewer';
import { App } from '../../App';
import * as api from '../../api/client';
import { metadata, view, context, event } from '../../test-fixtures';
import { preferenceKey } from '../../domain/playback';
vi.mock('../../api/client', async (original) => ({
  ...(await original<typeof api>()),
  fetchMatches: vi.fn(),
  fetchHead: vi.fn(),
  resolveCursor: vi.fn(),
  fetchView: vi.fn(),
  requestContext: vi.fn(),
  fetchEvidence: vi.fn(),
}));
const deferred = <T,>() => {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
};
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.fetchMatches).mockResolvedValue([metadata]);
  localStorage.clear();
  vi.mocked(api.fetchHead).mockResolvedValue({
    match_id: metadata.match_id,
    sequence: 3,
    available_second: 1500,
    ingestion_state: 'running',
  });
  vi.mocked(api.resolveCursor).mockImplementation(async (_, second) => ({
    match_id: metadata.match_id,
    available_second: second,
    to_sequence: second >= 400 ? 1 : 0,
    last_event_second: second >= 400 ? 400 : 0,
  }));
  vi.mocked(api.fetchView).mockImplementation(async (_, cutoff) =>
    cutoff
      ? view
      : {
          ...view,
          cutoff_sequence: 0,
          snapshot_id: 'zero',
          available_second: 0,
          recent_events: [],
        },
  );
  vi.mocked(api.requestContext).mockResolvedValue(context);
  vi.mocked(api.fetchEvidence).mockResolvedValue({
    snapshot_id: view.snapshot_id,
    cutoff_sequence: 1,
    events: [event],
    annulled_event_ids: [],
  });
});
async function ready() {
  render(<Viewer metadata={metadata} />);
  await screen.findByRole('slider', { name: 'Minuto del partido' });
  await waitFor(() => expect(api.fetchView).toHaveBeenCalled());
}
async function seek(second: number) {
  fireEvent.change(screen.getByRole('slider', { name: 'Minuto del partido' }), {
    target: { value: String(second) },
  });
  await waitFor(() =>
    expect(screen.getByTestId('match-view')).toHaveAttribute(
      'data-cutoff',
      second >= 400 ? '1' : '0',
    ),
  );
}
it('starts at zero and loads only cursor-bounded views', async () => {
  await ready();
  expect(screen.getByTestId('playback-clock')).toHaveTextContent('00:00');
  expect(api.resolveCursor).toHaveBeenCalledWith(metadata.match_id, 0, expect.any(AbortSignal));
  expect(api.fetchView).toHaveBeenCalledWith(metadata.match_id, 0, expect.any(AbortSignal));
  expect(api.requestContext).not.toHaveBeenCalled();
});
it('keeps a neutral pitch while a rewound frame loads, with no old player or score', async () => {
  await ready();
  await seek(400);
  const pending = deferred<api.MatchView>();
  vi.mocked(api.fetchView).mockReturnValueOnce(pending.promise);
  fireEvent.change(screen.getByRole('slider', { name: 'Minuto del partido' }), {
    target: { value: '0' },
  });
  await waitFor(() => expect(api.fetchView).toHaveBeenCalledTimes(3));
  expect(screen.getByRole('img', { name: /Cargando el minuto/ })).toBeInTheDocument();
  expect(screen.queryByText('Alex Reed')).not.toBeInTheDocument();
  expect(screen.queryByTestId('score')).not.toBeInTheDocument();
  expect(document.querySelector('.event-mark')).toBeNull();
  await act(async () =>
    pending.resolve({ ...view, cutoff_sequence: 0, snapshot_id: 'zero', recent_events: [] }),
  );
});
it('moves focus to the stable time control when a recent-action shortcut reloads the frame', async () => {
  await ready();
  await seek(400);
  const shortcut = screen.getByRole('button', { name: 'Ir a Pase · 06:40' });
  shortcut.focus();
  fireEvent.click(shortcut);
  await waitFor(() => expect(screen.getByTestId('match-view')).toHaveAttribute('data-cutoff', '1'));
  expect(screen.getByRole('slider', { name: 'Minuto del partido' })).toHaveFocus();
});
it('aborts the later view and ignores it even if the transport still resolves', async () => {
  await ready();
  await seek(400);
  const late = deferred<api.MatchView>();
  vi.mocked(api.fetchView).mockImplementationOnce(() => late.promise);
  fireEvent.change(screen.getByRole('slider', { name: 'Minuto del partido' }), {
    target: { value: '800' },
  });
  await waitFor(() => expect(api.fetchView).toHaveBeenCalledTimes(3));
  const signal = vi.mocked(api.fetchView).mock.calls.at(-1)![2];
  await seek(0);
  expect(signal.aborted).toBe(true);
  await act(async () =>
    late.resolve({
      ...view,
      snapshot_id: 'future',
      score: [
        { team_id: 'home', goals: 9 },
        { team_id: 'away', goals: 0 },
      ],
    }),
  );
  expect(screen.getByTestId('match-view')).toHaveAttribute('data-cutoff', '0');
  expect(screen.getByTestId('score')).toHaveTextContent('0 – 0');
  expect(screen.queryByText('Alex Reed')).not.toBeInTheDocument();
});
it('preserves time on language change and discards pending old-language context', async () => {
  await ready();
  await seek(400);
  const late = deferred<api.ContextResult>();
  vi.mocked(api.requestContext).mockReturnValueOnce(late.promise);
  fireEvent.click(screen.getByRole('button', { name: 'Ponerme al día' }));
  await waitFor(() => expect(api.requestContext).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByText('Personalizar'));
  fireEvent.change(screen.getByLabelText('Idioma'), { target: { value: 'en' } });
  expect(screen.getByTestId('playback-clock')).toHaveTextContent('06:40');
  expect(vi.mocked(api.requestContext).mock.calls[0][1].aborted).toBe(true);
  await act(async () => late.resolve(context));
  expect(screen.queryByText(context.summary)).not.toBeInTheDocument();
  expect(JSON.parse(localStorage.getItem(preferenceKey)!)).toEqual({
    language: 'en',
    depth: 'simple',
    favorite_team_id: null,
  });
  expect(localStorage.length).toBe(1);
});
it('opens evidence on demand and closes it without moving playback', async () => {
  await ready();
  await seek(400);
  fireEvent.click(screen.getByRole('button', { name: 'Ponerme al día' }));
  await screen.findByText(context.summary);
  expect(api.fetchEvidence).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Ver evidencia' }));
  const dialog = await screen.findByRole('dialog');
  await within(dialog).findByText('Alex Reed');
  fireEvent.click(screen.getByRole('button', { name: 'Volver al resumen' }));
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  expect(screen.getByTestId('playback-clock')).toHaveTextContent('06:40');
  expect(screen.getByRole('button', { name: 'Ver evidencia' })).toHaveFocus();
});
it('offers retry on a failed view instead of showing an empty match', async () => {
  vi.mocked(api.fetchView).mockRejectedValueOnce(new Error('offline'));
  await ready();
  await screen.findByRole('alert');
  fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
  await screen.findByTestId('match-view');
});
it('lets the fan cancel generation and retry without moving the minute', async () => {
  await ready();
  await seek(400);
  const pending = deferred<api.ContextResult>();
  vi.mocked(api.requestContext).mockReturnValueOnce(pending.promise);
  fireEvent.click(screen.getByRole('button', { name: 'Ponerme al día' }));
  await waitFor(() => expect(api.requestContext).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getByRole('button', { name: 'Cancelar resumen' }));
  expect(vi.mocked(api.requestContext).mock.calls[0][1].aborted).toBe(true);
  expect(screen.getByTestId('playback-clock')).toHaveTextContent('06:40');
  expect(screen.getByRole('button', { name: 'Ponerme al día' })).toBeEnabled();
  await act(async () => pending.resolve(context));
  expect(screen.queryByText(context.summary)).not.toBeInTheDocument();
});
it('shows an error rather than silently accepting context from a different snapshot', async () => {
  await ready();
  await seek(400);
  vi.mocked(api.requestContext).mockResolvedValueOnce({ ...context, snapshot_id: 'wrong' });
  fireEvent.click(screen.getByRole('button', { name: 'Ponerme al día' }));
  await screen.findByRole('alert');
  expect(screen.queryByText(context.summary)).not.toBeInTheDocument();
});
it('never overlaps slow shared-head polls', async () => {
  vi.useFakeTimers();
  try {
    const first = deferred<api.MatchHead>();
    vi.mocked(api.fetchHead).mockReturnValueOnce(first.promise);
    render(<Viewer metadata={metadata} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500);
    });
    expect(api.fetchHead).toHaveBeenCalledTimes(1);
    await act(async () =>
      first.resolve({
        match_id: metadata.match_id,
        sequence: 3,
        available_second: 1500,
        ingestion_state: 'running',
      }),
    );
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(api.fetchHead).toHaveBeenCalledTimes(2);
  } finally {
    vi.useRealTimers();
  }
});
it('explains a slow recap after ten seconds and keeps cancellation available', async () => {
  await ready();
  await seek(400);
  vi.useFakeTimers();
  try {
    vi.mocked(api.requestContext).mockReturnValueOnce(new Promise(() => {}));
    await act(async () => fireEvent.click(screen.getByRole('button', { name: 'Ponerme al día' })));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10001);
    });
    expect(
      screen.getByText(
        'Está tardando más de lo habitual. Puedes cancelar y seguir viendo el partido.',
      ),
    ).toBeVisible();
    expect(screen.getByRole('button', { name: 'Cancelar resumen' })).toBeEnabled();
  } finally {
    vi.useRealTimers();
  }
});
it('keeps the metric unit, interval, sample and caveat visible in evidence', async () => {
  await ready();
  await seek(400);
  vi.mocked(api.requestContext).mockResolvedValueOnce({
    ...context,
    summary_claims: [
      {
        claim_id: 'claim',
        kind: 'observed',
        text: 'Territorio',
        fact_ids: ['fact'],
        event_ids: [],
        limitations: [],
      },
    ],
    facts: [
      {
        fact_id: 'fact',
        snapshot_id: view.snapshot_id,
        cutoff_sequence: 1,
        team_id: 'home',
        name: 'territorial_share',
        value: 42.5,
        unit: '%',
        interval: { start_sequence: 0, end_sequence: 1, start_second: 0, end_second: 400 },
        denominator: 40,
        sample_count: 80,
        event_ids: ['event-1'],
        method: 'Team attacking-third completed passes / both teams.',
        limitations: [
          'Synthetic events; descriptive evidence does not establish tactical causation.',
        ],
      },
    ],
  });
  fireEvent.click(screen.getByRole('button', { name: 'Ponerme al día' }));
  await screen.findByText(context.summary);
  fireEvent.click(screen.getByRole('button', { name: 'Ver evidencia' }));
  const dialog = await screen.findByRole('dialog');
  expect(within(dialog).getByText('42,5 %')).toBeVisible();
  expect(within(dialog).getByText('00:00 – 06:40')).toBeVisible();
  expect(within(dialog).getByText('Eventos de la muestra: 80 · n = 40')).toBeVisible();
  expect(
    within(dialog).getByText(
      'Eventos sintéticos; los datos descriptivos no demuestran una causa táctica.',
    ),
  ).toBeVisible();
});

it('updates the outer shell language without resetting the viewer', async () => {
  render(<App />);
  await screen.findByRole('slider', { name: 'Minuto del partido' });
  await seek(400);
  fireEvent.click(screen.getByText('Personalizar'));
  fireEvent.change(screen.getByLabelText('Idioma'), { target: { value: 'en' } });
  expect(screen.getByRole('link', { name: 'Skip to match' })).toBeInTheDocument();
  expect(screen.getByTestId('playback-clock')).toHaveTextContent('06:40');
});
