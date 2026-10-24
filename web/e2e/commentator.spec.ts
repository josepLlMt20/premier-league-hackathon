import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, readFileSync } from 'node:fs';
import type { ContextResult } from '../src/api/client';
const output = '../docs/evidence/commentator-2026-10-24';
async function prepare(page: Page) {
  await page.goto('/');
  await expect(page.getByTestId('match-view')).toBeVisible();
  await page.getByRole('slider', { name: 'Minuto del partido' }).fill('1500');
  await expect(page.getByTestId('playback-clock')).toHaveText('25:00');
  await expect(page.getByTestId('match-view')).toBeVisible();
  const score = await page.getByTestId('score').innerText();
  await page.getByRole('button', { name: 'Profesional', exact: true }).click();
  await expect(page.getByTestId('playback-clock')).toHaveText('25:00');
  await expect(page.getByTestId('score')).toHaveText(score);
}
async function generate(page: Page): Promise<ContextResult> {
  const response = page.waitForResponse((r) => r.url().endsWith('/api/context'));
  await page.getByRole('button', { name: 'Preparar briefing', exact: true }).click();
  const result = await (await response).json();
  await expect(page.locator('.professional-result')).toBeVisible();
  return result;
}
test('professional receipts export bounded briefing and overlay, with evidence and truthful provenance', async ({
  page,
}, info) => {
  await prepare(page);
  const result = await generate(page);
  expect(result.request.role).toBe('commentator');
  expect(result.mode).toBe('scripted');
  expect(result.cards.length).toBeGreaterThan(0);
  await expect(page.locator('.professional-result .recap-summary')).toHaveCount(0);
  for (const card of result.cards) {
    expect(new Set([card.headline, card.explanation, card.suggested_line]).size).toBe(3);
    const names = card.claims
      .flatMap((claim) => claim.fact_ids || [])
      .map((id) => result.facts.find((fact) => fact.fact_id === id)?.name);
    if (names.includes('shot_quality_total')) {
      expect(card.explanation).toContain('índice sintético de tiro');
      expect(card.explanation).toContain('puntos');
      expect(card.suggested_line).toContain('tiros');
    }
  }
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Descargar briefing JSON', exact: true }).click();
  const briefing = JSON.parse(readFileSync((await (await download).path())!, 'utf8'));
  expect(briefing.snapshot_id).toBe(result.snapshot_id);
  expect(briefing.cutoff_sequence).toBe(result.request.to_sequence);
  expect(briefing.displayed_second).toBe(1500);
  expect(briefing.cards[0].suggested_line).toBe(result.cards[0].suggested_line);
  expect(briefing.cards[0].limitations).toEqual(result.cards[0].limitations);
  const overlayDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Descargar overlay JSON', exact: true }).click();
  const overlay = JSON.parse(readFileSync((await (await overlayDownload).path())!, 'utf8'));
  expect(overlay.text).toBe(result.cards[0].overlay_text);
  expect(Array.from(overlay.text).length).toBeLessThanOrEqual(140);
  expect(overlay.score).toEqual(briefing.score);
  expect(overlay.snapshot_id).toBe(briefing.snapshot_id);
  expect(overlay.limitations).toEqual(result.cards[0].limitations);
  await page.getByText('Cómo se preparó', { exact: true }).click();
  await expect(page.getByText('Llamadas al modelo: 0', { exact: true })).toBeVisible();
  await expect(page.getByText('Prueba guiada · texto programado', { exact: true })).toBeVisible();
  const a11y = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(a11y.violations).toEqual([]);
  mkdirSync(output, { recursive: true });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `${output}/${info.project.name}-overview.png` });
  await page.screenshot({ path: `${output}/${info.project.name}-studio.png`, fullPage: true });
  await page
    .locator('.overlay-preview')
    .screenshot({ path: `${output}/${info.project.name}-overlay.png` });
  const evidence = page.getByRole('button', { name: 'Ver evidencia · 1', exact: true });
  await evidence.click();
  await expect(page.getByRole('dialog')).toBeVisible();
  for (const factId of result.cards[0].claims[0].fact_ids || []) {
    await expect(page.getByRole('dialog')).toContainText(factId);
  }
  const modalA11y = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(modalA11y.violations).toEqual([]);
  await page.screenshot({ path: `${output}/${info.project.name}-evidence.png`, fullPage: true });
  await page.keyboard.press('Escape');
  await expect(evidence).toBeFocused();
  await page.setViewportSize({ width: 320, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `${output}/${info.project.name}-320.png`, fullPage: true });
  await page.getByRole('button', { name: 'Aficionado', exact: true }).click();
  await expect(page.locator('.professional-result')).toHaveCount(0);
  await expect(page.getByTestId('playback-clock')).toHaveText('25:00');
  await expect(page.getByTestId('score')).toHaveText(
    briefing.score.map((s: { goals: number }) => s.goals).join(' – '),
  );
});
test('factual fallback cannot become an editorial export and language changes retire the receipt', async ({
  page,
}) => {
  await prepare(page);
  await page.route('**/api/context', async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    await route.fulfill({
      response,
      json: { ...body, status: 'factual', mode: 'factual', cards: [] },
    });
  });
  await generate(page);
  await expect(
    page.getByRole('button', { name: 'Descargar briefing JSON', exact: true }),
  ).toBeDisabled();
  await expect(page.getByText(/No hay tarjetas editoriales verificadas/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Descargar overlay JSON' })).toHaveCount(0);
  await page.locator('.preferences summary').click();
  await page.getByLabel('Idioma', { exact: true }).selectOption('en');
  await expect(page.getByRole('heading', { name: 'Match briefing' })).toBeVisible();
  await expect(page.locator('.professional-result')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Download briefing JSON' })).toBeDisabled();
});
test('clipboard and download failures leave readable commentary and recoverable controls', async ({
  page,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: () => Promise.reject(new Error('denied')) },
    });
    URL.createObjectURL = () => {
      throw new Error('blocked');
    };
  });
  await prepare(page);
  const result = await generate(page);
  await page.getByRole('button', { name: 'Copiar frase', exact: true }).first().click();
  await expect(page.getByText(/No se ha podido copiar/)).toBeVisible();
  await expect(page.locator('blockquote').first()).toHaveText(result.cards[0].suggested_line);
  await page.getByRole('button', { name: 'Descargar briefing JSON', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('No se ha podido descargar');
  await expect(
    page.getByRole('button', { name: 'Descargar briefing JSON', exact: true }),
  ).toBeEnabled();
});
