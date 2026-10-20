import { defineConfig, devices } from '@playwright/test';

/**
 * E2E tests run against the full Docker Compose stack (nginx + API + Postgres + Redis), so
 * cookies, proxying and security headers behave exactly as they do in production.
 * Start it first: `docker compose up -d --build --wait`.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:8080',
    trace: 'retain-on-failure',
    // Entrance animations fade content in; reduced motion renders the final state immediately so
    // accessibility scans measure real contrast instead of a frame mid-fade.
    contextOptions: { reducedMotion: 'reduce' },
  },
  projects: [
    { name: 'mobile', use: { ...devices['Pixel 7'], viewport: { width: 360, height: 780 } } },
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
  ],
});
