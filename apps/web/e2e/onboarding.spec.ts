import { expect, test } from '@playwright/test';
import { expectAccessible } from './a11y';

test.describe('onboarding', () => {
  test('a visitor starts anonymously, sets consents, then upgrades to an account', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(
      page.getByRole('heading', { level: 1, name: 'Check in with yourself, privately.' }),
    ).toBeVisible();
    await expectAccessible(page);

    await page.getByRole('link', { name: 'Start anonymously' }).first().click();
    await expect(page).toHaveURL(/\/start$/);
    await expectAccessible(page);
    await page.getByRole('button', { name: "Yes, I'm 18 or older" }).click();

    await expect(page).toHaveURL(/\/start\/consent$/);
    await expectAccessible(page);
    await page.getByRole('switch', { name: /Store my check-in answers/ }).click();
    await page.getByRole('switch', { name: 'Keep chat history' }).click();
    await page.getByRole('button', { name: 'Continue anonymously' }).click();

    await expect(page).toHaveURL(/\/app$/);
    await expect(
      page.getByRole('heading', { name: "You're using MindGuard anonymously" }),
    ).toBeVisible();
    await expectAccessible(page);

    await page.getByRole('link', { name: 'Save my account' }).click();
    await expect(page).toHaveURL(/\/app\/privacy#account$/);
    await expect(page.getByRole('switch', { name: 'Keep chat history' })).toHaveAttribute(
      'aria-checked',
      'true',
    );
    await expectAccessible(page);

    // Change a consent from the Privacy page.
    const voice = page.getByRole('switch', { name: 'Voice check-ins' });
    await voice.click();
    await expect(voice).toHaveAttribute('aria-checked', 'true');
    await expect(page.getByText('Saved', { exact: true })).toBeVisible();

    const email = `e2e-${Date.now()}-${test.info().project.name}@example.in`;
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill('a calm long passphrase');
    await page.getByRole('button', { name: 'Save my account' }).click();
    await expect(page.getByText(`Signed in as ${email}`)).toBeVisible();

    // The upgraded account survives sign-out and keeps its consents.
    await page.getByRole('button', { name: 'Sign out' }).click();
    await expect(page).toHaveURL(/\/$/);
    await page.getByRole('link', { name: 'Sign in' }).first().click();
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password').fill('a calm long passphrase');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL(/\/app$/);
    await page.goto('/app/privacy');
    await expect(page.getByRole('switch', { name: 'Voice check-ins' })).toHaveAttribute(
      'aria-checked',
      'true',
    );
  });

  test('people under 18 get support information and no account', async ({ page }) => {
    await page.goto('/start');
    await page.getByRole('button', { name: "No, I'm under 18" }).click();
    await expect(page).toHaveURL(/\/start\/under-18$/);
    await expect(page.getByRole('link', { name: /Tele-MANAS 14416/ })).toHaveAttribute(
      'href',
      'tel:14416',
    );
    await expectAccessible(page);

    const me = await page.request.get('/api/v1/auth/me');
    expect(me.status()).toBe(401);
  });

  test('the dashboard is not reachable without a session', async ({ page }) => {
    await page.goto('/app');
    await expect(page).toHaveURL(/\/$/);
  });

  test('the interface switches to Tamil', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /தமிழ்/ }).first().click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'ta');
    await expect(
      page.getByRole('link', { name: 'அடையாளமின்றித் தொடங்குங்கள்' }).first(),
    ).toBeVisible();
    await expectAccessible(page);
  });

  test('the dark theme keeps every screen readable', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    for (const path of ['/', '/start', '/start/under-18', '/login']) {
      await page.goto(path);
      await expectAccessible(page);
    }
  });

  test('security headers are present', async ({ request }) => {
    const response = await request.get('/');
    const headers = response.headers();
    expect(headers['content-security-policy']).toContain("default-src 'self'");
    expect(headers['x-content-type-options']).toBe('nosniff');
    expect(headers['referrer-policy']).toBe('no-referrer');
    expect(headers['x-frame-options']).toBe('DENY');
  });
});
