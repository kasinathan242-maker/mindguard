import { expect, test } from '@playwright/test';
import { expectAccessible } from './a11y';

const APP_ROUTES = [
  '/app',
  '/app/chat',
  '/app/assessments',
  '/app/assessments/PHQ9',
  '/app/wellness',
  '/app/privacy',
];
const PUBLIC_ROUTES = ['/', '/start', '/start/under-18', '/login'];

for (const scheme of ['light', 'dark'] as const) {
  for (const locale of ['English', 'தமிழ்'] as const) {
    test(`every screen passes axe (${scheme}, ${locale})`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto('/');
      await page
        .getByRole('button', { name: new RegExp(locale) })
        .first()
        .click();
      for (const path of PUBLIC_ROUTES) {
        await page.goto(path);
        await expectAccessible(page);
      }
      await page.goto('/start');
      await page.getByRole('button').filter({ hasText: /18/ }).first().click();
      await page.getByRole('switch').first().click();
      await page.locator('form button[type="submit"]').click();
      await expect(page).toHaveURL(/\/app$/);
      for (const path of APP_ROUTES) {
        await page.goto(path);
        await page.waitForLoadState('networkidle');
        await expectAccessible(page);
      }
    });
  }
}

test('HSTS and CSP are sent by the web server', async ({ request }) => {
  const headers = (await request.get('/')).headers();
  expect(headers['strict-transport-security']).toContain('max-age=31536000');
  expect(headers['content-security-policy']).toContain("frame-ancestors 'none'");
});
