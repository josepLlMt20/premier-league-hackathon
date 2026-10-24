import { defineConfig, devices } from '@playwright/test';
import { existsSync } from 'node:fs';
import { fileURLToPath, URL } from 'node:url';
const root = fileURLToPath(new URL('..', import.meta.url));
const python =
  process.env.E2E_PYTHON ||
  (existsSync(`${root}/.venv/Scripts/python.exe`)
    ? '.venv/Scripts/python.exe'
    : '.venv/bin/python');
export default defineConfig({
  testDir: './e2e',
  outputDir: '../tmp/ui-validation/test-results',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30000,
  reporter: [['list'], ['html', { outputFolder: '../tmp/ui-validation/report', open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    reducedMotion: 'reduce',
  },
  projects: [
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1100 } },
    },
    { name: 'mobile', use: { ...devices['Pixel 7'], viewport: { width: 390, height: 844 } } },
  ],
  webServer: [
    {
      command: `"${python}" -m tests.e2e_server --port 8765`,
      cwd: root,
      url: 'http://127.0.0.1:8765/healthz',
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: 'npm run dev -- --port 5173 --strictPort',
      url: 'http://127.0.0.1:5173',
      env: { MATCH_CONTEXT_API: 'http://127.0.0.1:8765' },
      reuseExistingServer: false,
    },
  ],
});
