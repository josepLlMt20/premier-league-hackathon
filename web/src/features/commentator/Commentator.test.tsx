import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { Commentator } from './Commentator';
import { initialPlayback } from '../../domain/playback';
import { metadata, view } from '../../test-fixtures';
import { professionalResult, briefingCard } from './fixtures';
const props = () => ({
  state: {
    ...initialPlayback(),
    role: 'commentator' as const,
    second: 400,
    view,
    context: professionalResult,
  },
  metadata,
  loading: false,
  error: null,
  generate: vi.fn(),
  cancel: vi.fn(),
  dispatch: vi.fn(),
  openEvidence: vi.fn(),
});
const writeText = vi.fn();
beforeEach(() => {
  writeText.mockReset().mockResolvedValue(undefined);
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
});
it('shows an editorial card, claim class, intervals and evidence, then copies the phrase with its limitations', async () => {
  const p = props();
  render(<Commentator {...p} />);
  expect(screen.getByRole('heading', { name: briefingCard.headline })).toBeVisible();
  expect(screen.getAllByText('Interpretación').length).toBeGreaterThan(0);
  expect(screen.getAllByText('05:00 – 06:40').length).toBeGreaterThan(0);
  fireEvent.click(screen.getByRole('button', { name: 'Ver evidencia · 1' }));
  expect(p.openEvidence).toHaveBeenCalledWith(briefingCard.story_id, expect.any(HTMLElement));
  fireEvent.click(screen.getByRole('button', { name: 'Copiar frase' }));
  await waitFor(() => expect(writeText).toHaveBeenCalled());
  expect(writeText.mock.calls[0][0]).toContain(briefingCard.suggested_line);
  expect(writeText.mock.calls[0][0]).toContain(briefingCard.limitations[0]);
  expect(screen.getByRole('button', { name: 'Descargar briefing JSON' })).toBeEnabled();
  expect(screen.getByRole('button', { name: 'Descargar overlay JSON' })).toBeEnabled();
});
it('offers useful factual data without making an editorial export available', () => {
  const p = props();
  render(
    <Commentator
      {...p}
      state={{
        ...p.state,
        context: { ...professionalResult, status: 'factual', mode: 'factual', cards: [] },
      }}
    />,
  );
  expect(screen.getByRole('button', { name: 'Descargar briefing JSON' })).toBeDisabled();
  expect(screen.queryByRole('button', { name: 'Descargar overlay JSON' })).not.toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: briefingCard.headline })).not.toBeInTheDocument();
  expect(screen.getByText(/No hay tarjetas editoriales verificadas/)).toBeVisible();
});
it('keeps text usable when clipboard permission is denied', async () => {
  writeText.mockRejectedValue(new Error('denied'));
  render(<Commentator {...props()} />);
  fireEvent.click(screen.getByRole('button', { name: 'Copiar frase' }));
  await screen.findByText(/No se ha podido copiar/);
  expect(screen.getByText(briefingCard.suggested_line, { selector: 'blockquote' })).toBeVisible();
});
it('makes scripted trace provenance and zero real model calls explicit', () => {
  render(<Commentator {...props()} />);
  fireEvent.click(screen.getByText('Cómo se preparó'));
  expect(screen.getByText('Revisor')).toBeVisible();
  expect(screen.getByText('Prueba guiada · texto programado', { exact: true })).toBeVisible();
  expect(screen.getByText('Llamadas al modelo: 0')).toBeVisible();
});

it('does not invent zero calls or claim no workflow when the trace is unavailable', () => {
  const p = props();
  render(
    <Commentator {...p} state={{ ...p.state, context: { ...professionalResult, trace: undefined } }} />,
  );
  fireEvent.click(screen.getByText('Cómo se preparó'));
  expect(screen.getByText('No hay una traza disponible para este resultado.')).toBeVisible();
  expect(screen.getByText('Llamadas al modelo: —')).toBeVisible();
});
