import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import type { ContextResult, MatchView } from '../src/api/client';
const output = '../tmp/ui-validation';
test('same-interval regeneration retires old evidence before a replacement result is shown', async ({
  page,
}) => {
  await page.goto('/');
  await expect(page.getByTestId('match-view')).toBeVisible();
  const boundedResponse = page.waitForResponse((r) => r.url().includes('/view?'));
  await seek(page, 1500);
  const bounded: MatchView = await (await boundedResponse).json();
  const oldEvent = bounded.recent_events.at(-1)!;
  const newEvent = bounded.recent_events.at(-2)!;
  let calls = 0;
  let release!: () => void;
  const replacement = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/context', async (route) => {
    const response = await route.fetch();
    const result: ContextResult = await response.json();
    const first = calls++ === 0;
    if (!first) await replacement;
    const support = first ? oldEvent : newEvent;
    const summary = first ? 'Resumen anterior.' : 'Resumen regenerado.';
    // Explicitly controlled transport over the real bounded API; no live provider.
    await route.fulfill({
      response,
      json: {
        ...result,
        mode: first ? 'factual' : 'scripted',
        status: first ? 'factual' : 'verified',
        summary,
        cards: [],
        facts: [],
        evidence_ids: [support.event_id],
        summary_claims: [
          {
            claim_id: 'support',
            kind: 'observed',
            text: summary,
            event_ids: [support.event_id],
            fact_ids: [],
            limitations: [],
          },
        ],
      },
    });
  });
  await page.getByRole('button', { name: 'Ponerme al día' }).click();
  await expect(page.locator('.recap-summary')).toHaveText('Resumen anterior.');
  await page.getByRole('button', { name: 'Ver evidencia', exact: true }).click();
  await expect(
    page.getByRole('dialog').getByText(oldEvent.event_id, { exact: false }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button', { name: 'Ponerme al día' }).click();
  await expect(page.locator('.recap-summary')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Ver evidencia', exact: true })).toHaveCount(0);
  await expect(page.getByTestId('playback-clock')).toHaveText('25:00');
  release();
  await expect(page.locator('.recap-summary')).toHaveText('Resumen regenerado.');
  await page.getByRole('button', { name: 'Ver evidencia', exact: true }).click();
  await expect(
    page.getByRole('dialog').getByText(newEvent.event_id, { exact: false }),
  ).toBeVisible();
  await expect(page.getByRole('dialog').getByText(oldEvent.event_id, { exact: false })).toHaveCount(
    0,
  );
  expect(calls).toBe(2);
});
test('studio evidence drawer is finite, reduced-motion safe and cannot retain context during a rewind', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.goto('/');
  await expect(page.getByTestId('match-view')).toBeVisible();
  await seek(page, 1500);
  await page.getByRole('button', { name: 'Ponerme al día' }).click();
  await expect(page.locator('.shot-comparison')).toBeVisible();
  const meters = page.getByRole('meter');
  await expect(meters).toHaveCount(2);
  const trigger = page.getByRole('button', { name: 'Ver evidencia', exact: true });
  await trigger.click();
  const drawer = page.getByRole('dialog');
  await expect(drawer).toBeVisible();
  await expect
    .poll(async () =>
      Math.round((await drawer.boundingBox())!.x + (await drawer.boundingBox())!.width),
    )
    .toBe(page.viewportSize()!.width);
  expect(await drawer.evaluate((node) => getComputedStyle(node).transitionDuration)).toContain(
    '0.24s',
  );
  expect((await drawer.boundingBox())!.y).toBe(0);
  await page.keyboard.press('Escape');
  await expect(drawer).toHaveCount(0);
  await expect(trigger).toBeFocused();
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await trigger.click();
  await expect(drawer).toBeVisible();
  expect(await drawer.evaluate((node) => getComputedStyle(node).transitionDuration)).toBe('0s');
  await page.keyboard.press('Escape');
  await expect(drawer).toHaveCount(0);
  await seek(page, 0);
  await expect(page.locator('.shot-comparison')).toHaveCount(0);
  await expect(drawer).toHaveCount(0);
});
test('event motion is finite, respects reduced motion and removes the previous event immediately on rewind', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.goto('/');
  await expect(page.getByTestId('match-view')).toBeVisible();
  const received = page.waitForResponse((r) => r.url().includes('/view?'));
  await seek(page, 1500);
  const bounded: MatchView = await (await received).json();
  await page.locator('.moment-button').nth(1).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('slider', { name: 'Minuto del partido' })).toBeFocused();
  await expect(page.getByTestId('match-view')).toBeVisible();
  const pass = bounded.recent_events.find(
    (event, index, events) =>
      event.kind === 'pass' && events[index + 1]?.available_second > event.available_second + 1,
  )!;
  expect(pass).toBeDefined();
  await seek(page, pass.available_second);
  await expect(page.locator('.event-mark')).toHaveClass(/event-arriving/);
  expect(
    await page.locator('.trajectory').evaluate((el) => getComputedStyle(el).animationDuration),
  ).toBe('0.45s');
  await seek(page, pass.available_second + 1);
  await expect(page.locator('.event-mark')).not.toHaveClass(/event-arriving/);
  await seek(page, 1500);
  await page.route('**/view?to_sequence=0', async (route) => {
    const response = await route.fetch(),
      body = await response.body();
    await new Promise((resolve) => setTimeout(resolve, 500));
    await route.fulfill({ body, status: response.status(), headers: response.headers() });
  });
  const oldEvent = await page.locator('.event-mark').elementHandle();
  const wasRunning = await page.evaluate(() => {
    const cue = document.querySelector('.event-halo')!.getAnimations()[0];
    // Place the real CSS animation inside its finite timeline, then dispatch the
    // rewind in the same task: no timing gap can turn this into an idle-state test.
    cue.currentTime = 100;
    cue.play();
    const running = cue.playState === 'running';
    const control = document.querySelector('#match-time')!;
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(control, '0');
    control.dispatchEvent(new Event('input', { bubbles: true }));
    return running;
  });
  expect(wasRunning).toBe(true);
  await expect(page.locator('.event-mark')).toHaveCount(0);
  expect(await oldEvent!.evaluate((el) => el.isConnected)).toBe(false);
  await expect(page.getByTestId('score')).toHaveCount(0);
  await expect(page.getByRole('img', { name: /Cargando el minuto/ })).toBeVisible();
  await expect(page.getByTestId('match-view')).toHaveAttribute('data-cutoff', '0');
  await page.unroute('**/view?to_sequence=0');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await seek(page, pass.available_second);
  expect(
    await page.locator('.trajectory').evaluate((el) => getComputedStyle(el).animationName),
  ).toBe('none');
  expect(
    await page.locator('.trajectory').evaluate((el) => getComputedStyle(el).strokeDashoffset),
  ).toBe('0px');
});
test('playback completes slow bounded reads without cancelling them on every tick', async ({
  page,
}) => {
  await page.goto('/');
  await expect(page.getByTestId('match-view')).toBeVisible();
  await page.route('**/view?*', async (route) => {
    const response = await route.fetch();
    const body = await response.body(),
      status = response.status(),
      headers = response.headers();
    await new Promise((resolve) => setTimeout(resolve, 1200));
    if (!page.isClosed()) await route.fulfill({ body, status, headers }).catch(() => {});
  });
  await page.getByRole('button', { name: 'Reproducir', exact: true }).click();
  await expect
    .poll(
      async () => {
        const [minutes, seconds] = (await page.getByTestId('playback-clock').innerText())
          .split(':')
          .map(Number);
        return minutes * 60 + seconds;
      },
      { timeout: 8000, intervals: [100, 250, 500] },
    )
    .toBeGreaterThanOrEqual(2);
  await expect(page.getByTestId('match-view')).toBeVisible({ timeout: 5000 });
  await expect(page.getByRole('button', { name: 'Pausar', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Pausar', exact: true }).click();
  await page.unroute('**/view?*');
});
test('automatic playback keeps the committed score, pitch and recent sequence visible between slow reads', async ({
  page,
}) => {
  await page.goto('/');
  await expect(page.getByTestId('match-view')).toBeVisible();
  await seek(page, 1400);
  await page.route('**/view?*', async (route) => {
    const response = await route.fetch();
    const body = await response.body();
    await new Promise((resolve) => setTimeout(resolve, 1200));
    if (!page.isClosed())
      await route
        .fulfill({ body, status: response.status(), headers: response.headers() })
        .catch(() => {});
  });
  const score = await page.getByTestId('score').elementHandle();
  const pitch = await page.locator('.pitch').elementHandle();
  const rail = await page.locator('.moment-rail').elementHandle();
  await page.getByRole('button', { name: 'Reproducir', exact: true }).click();
  const read = await page.waitForRequest((r) => r.url().includes('/view?'));
  expect(read).toBeDefined();
  await expect(page.getByTestId('playback-clock')).toHaveText('23:20');
  await expect(page.getByTestId('score')).toBeVisible();
  expect(await score!.evaluate((node) => node.isConnected && node.dataset.testid === 'score')).toBe(
    true,
  );
  expect(await pitch!.evaluate((node) => node.isConnected)).toBe(true);
  expect(await rail!.evaluate((node) => node.isConnected)).toBe(true);
  await expect(page.getByRole('img', { name: /Cargando el minuto/ })).toHaveCount(0);
  await expect(page.getByTestId('playback-clock')).toHaveText('23:21', { timeout: 5000 });
  await page.getByRole('button', { name: 'Pausar', exact: true }).click();
  expect(await score!.evaluate((node) => node.isConnected)).toBe(true);
  expect(await pitch!.evaluate((node) => node.isConnected)).toBe(true);
  expect(await rail!.evaluate((node) => node.isConnected)).toBe(true);
});
async function seek(page: Page, second: number) {
  const input = page.getByRole('slider', { name: /Minuto del partido|Match minute/ });
  await input.evaluate((element, second) => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(
      element,
      String(second),
    );
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
  }, second);
  await expect(page.getByTestId('playback-clock')).toHaveText(
    new RegExp(
      `${Math.floor(second / 60)
        .toString()
        .padStart(2, '0')}:${(second % 60).toString().padStart(2, '0')}`,
    ),
  );
  await expect(page.getByTestId('match-view')).toBeVisible();
}
test('real bounded API, bilingual recap, evidence, rewind and preferences-only storage', async ({
  page,
}, info) => {
  const requests: { path: string; method: string }[] = [];
  page.on('request', (request) => {
    if (request.url().includes('/api/'))
      requests.push({ path: request.url(), method: request.method() });
  });
  await page.goto('/');
  await expect(page.getByTestId('playback-clock')).toHaveText('00:00');
  await expect(page.getByTestId('match-view')).toHaveAttribute('data-cutoff', '0');
  expect(
    requests
      .filter((r) => r.path.includes('/view?'))
      .every((r) => r.path.endsWith('to_sequence=0')),
  ).toBe(true);
  expect(requests.some((r) => /fixture|events|ingest|advance|tick/.test(r.path))).toBe(false);
  await seek(page, 1500);
  const resultPromise = page.waitForResponse((response) => response.url().endsWith('/api/context'));
  await page.getByRole('button', { name: 'Ponerme al día' }).click();
  const result: ContextResult = await (await resultPromise).json();
  expect(result.mode).toBe('scripted');
  expect(result.status).toBe('verified');
  expect(result.cards.length).toBeGreaterThan(0);
  await expect(page.getByText('Prueba guiada · texto programado', { exact: true })).toBeVisible();
  await expect(page.locator('.recap-summary')).toHaveText(result.summary);
  const viewResponse = await page.request.get(
    `/api/matches/${result.request.match_id}/view?to_sequence=${result.request.to_sequence}`,
  );
  const view: MatchView = await viewResponse.json();
  expect(
    view.recent_events.every(
      (event) => event.sequence <= result.request.to_sequence && event.available_second <= 1500,
    ),
  ).toBe(true);
  const evidencePromise = page.waitForResponse((response) =>
    response.url().endsWith('/api/evidence'),
  );
  const trigger = page.getByRole('button', { name: 'Ver evidencia', exact: true });
  await trigger.click();
  const evidence = await (await evidencePromise).json();
  expect(evidence.snapshot_id).toBe(result.snapshot_id);
  expect(
    evidence.events.every(
      (event: { sequence: number; available_second: number }) =>
        event.sequence <= result.request.to_sequence && event.available_second <= 1500,
    ),
  ).toBe(true);
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await expect(trigger).toBeFocused();
  await expect(page.getByTestId('playback-clock')).toHaveText('25:00');
  await page.getByText('Personalizar', { exact: true }).click();
  await page.getByLabel('Idioma', { exact: true }).selectOption('en');
  await expect(page.getByTestId('playback-clock')).toHaveText('25:00');
  await expect(page.locator('.recap-summary')).toHaveCount(0);
  const englishPromise = page.waitForResponse((response) =>
    response.url().endsWith('/api/context'),
  );
  await page.getByRole('button', { name: 'Catch me up' }).click();
  const english: ContextResult = await (await englishPromise).json();
  expect(english.request.language).toBe('en');
  expect(english.mode).toBe('scripted');
  await expect(page.locator('.recap-summary')).toHaveText(english.summary);
  await page.getByText('Personalize', { exact: true }).click();
  mkdirSync(output, { recursive: true });
  await page.screenshot({ path: `${output}/${info.project.name}-recap.png`, fullPage: true });
  await seek(page, 0);
  await expect(page.getByTestId('match-view')).toHaveAttribute('data-cutoff', '0');
  await expect(page.getByTestId('score')).toHaveText('0 – 0');
  await expect(page.locator('.recap-summary')).toHaveCount(0);
  await expect(page.locator('.event-mark')).toHaveCount(0);
  const storage = await page.evaluate(() => ({ ...localStorage }));
  expect(Object.keys(storage)).toEqual(['match-context.preferences.v1']);
  expect(JSON.parse(storage['match-context.preferences.v1'])).toEqual({
    language: 'en',
    depth: 'simple',
    favorite_team_id: null,
  });
  expect(
    requests
      .filter((r) => r.method === 'POST')
      .every((r) => /\/api\/(context|evidence)$/.test(r.path)),
  ).toBe(true);
  await page.reload();
  await expect(page.getByTestId('playback-clock')).toHaveText('00:00');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
});

test('pause and speed do not stop shared ingestion; keyboard controls work', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('match-view')).toBeVisible();
  const metadata = await (await page.request.get('/api/matches')).json();
  const head = () =>
    page.request
      .get(`/api/matches/${metadata[0].match_id}/head`)
      .then((response) => response.json());
  const before = await head();
  await page.getByLabel('Velocidad', { exact: true }).selectOption('5');
  await page.getByRole('button', { name: 'Reproducir', exact: true }).click();
  await expect(page.getByTestId('playback-clock')).toHaveText('00:05');
  await page.getByRole('button', { name: 'Pausar', exact: true }).click();
  const paused = await page.getByTestId('playback-clock').textContent();
  await expect
    .poll(async () => (await head()).available_second)
    .toBeGreaterThan(before.available_second + 2);
  await expect(page.getByTestId('playback-clock')).toHaveText(paused!);
  const slider = page.getByRole('slider', { name: 'Minuto del partido' });
  await slider.focus();
  await page.keyboard.press('Home');
  await expect(page.getByTestId('playback-clock')).toHaveText('00:00');
  await page.keyboard.press('ArrowRight');
  await expect(page.getByTestId('playback-clock')).toHaveText('00:01');
});

test('accessible responsive rendering, fonts, measured spacing and real DOM', async ({
  page,
}, info) => {
  await page.goto('/');
  await expect(page.getByTestId('match-view')).toBeVisible();
  await seek(page, 1500);
  await page.getByRole('button', { name: 'Ponerme al día' }).click();
  await expect(page.locator('.recap-summary')).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  const fonts = await page.evaluate(() => ({
    family: getComputedStyle(document.body).fontFamily,
    loaded: document.fonts.check('16px "IBM Plex Sans"'),
  }));
  expect(fonts.loaded).toBe(true);
  expect(fonts.family).toContain('IBM Plex Sans');
  await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
  const a11y = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze();
  mkdirSync(output, { recursive: true });
  writeFileSync(
    `${output}/${info.project.name}-axe.json`,
    JSON.stringify({ violations: a11y.violations, passes: a11y.passes.length, fonts }, null, 2),
  );
  expect(a11y.violations).toEqual([]);
  const dimensions = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    viewport: innerWidth,
  }));
  expect(dimensions.scroll).toBeLessThanOrEqual(dimensions.viewport);
  const capture = await page.evaluate(() => ({
    name: 'fan-recap',
    viewport: { width: innerWidth, height: innerHeight, devicePixelRatio },
    elements: [
      ...document.querySelectorAll(
        '.app-shell,.viewer-grid,.match-panel,.catchup-panel,.window-bar,.catchup-body,.playback-controls,button,select,input,summary',
      ),
    ].map((element, index) => {
      const rect = element.getBoundingClientRect(),
        style = getComputedStyle(element);
      return {
        id: `e-${index}`,
        label: element.textContent?.trim().slice(0, 60),
        tag: element.tagName.toLowerCase(),
        interactive: element.matches('button,select,input,summary'),
        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
        scrollWidth: element.scrollWidth,
        clientWidth: element.clientWidth,
        style: {
          display: style.display,
          columnGap: style.columnGap,
          rowGap: style.rowGap,
          padding: {
            top: parseFloat(style.paddingTop),
            right: parseFloat(style.paddingRight),
            bottom: parseFloat(style.paddingBottom),
            left: parseFloat(style.paddingLeft),
          },
        },
      };
    }),
  }));
  writeFileSync(`${output}/${info.project.name}-spacing.json`, JSON.stringify(capture));
  for (const width of [...new Set([page.viewportSize()!.width, 1440, 1728, 390])]) {
    await page.setViewportSize({ width, height: 1100 });
    await page.evaluate(() => window.scrollTo(0, 0));
    const state = await page.evaluate(
      readFileSync(new URL('./capture-spacing.js', import.meta.url), 'utf8'),
    );
    writeFileSync(`${output}/spacing-${width}.json`, JSON.stringify(state));
  }
  await page.setViewportSize(info.project.use.viewport!);
  await page.screenshot({ path: `${output}/${info.project.name}-spanish.png`, fullPage: true });
  await page.getByRole('button', { name: 'Ver evidencia', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  const modalA11y = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'])
    .analyze();
  expect(modalA11y.violations).toEqual([]);
  await page.screenshot({ path: `${output}/${info.project.name}-evidence.png`, fullPage: true });
  await page.keyboard.press('Escape');
  await page.getByRole('link', { name: 'Ir al partido' }).focus();
  await expect(page.getByRole('link', { name: 'Ir al partido' })).toBeInViewport();
  expect(
    (await page.getByRole('link', { name: 'Ir al partido' }).boundingBox())!.height,
  ).toBeGreaterThanOrEqual(44);
  await page.keyboard.press('Tab');
  await page.setViewportSize({ width: 320, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `${output}/${info.project.name}-320.png`, fullPage: true });
});
