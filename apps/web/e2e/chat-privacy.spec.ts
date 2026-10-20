import { expect, test, type Page } from '@playwright/test';
import { expectAccessible } from './a11y';

async function startAnonymously(page: Page, chatHistory = false) {
  await page.goto('/start');
  await page.getByRole('button', { name: "Yes, I'm 18 or older" }).click();
  await page.getByRole('switch', { name: /Store my check-in answers/ }).click();
  if (chatHistory) await page.getByRole('switch', { name: 'Keep chat history' }).click();
  await page.getByRole('button', { name: 'Continue anonymously' }).click();
  await expect(page).toHaveURL(/\/app$/);
}

test('chat replies, and an urgent message shows the crisis card instead of a reply', async ({
  page,
}) => {
  await startAnonymously(page);
  await page.goto('/app/chat');
  await expect(page.getByText("This chat isn't saved.")).toBeVisible();
  await expectAccessible(page);

  const input = page.getByLabel('Your message');
  await input.fill('I feel anxious about tomorrow');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect(page.getByRole('log').getByText(/breathe in for four/)).toBeVisible();

  await input.fill('I want to kill myself');
  await page.getByRole('button', { name: 'Send' }).click();
  const log = page.getByRole('log');
  await expect(log.getByRole('link', { name: /Call Tele-MANAS now: 14416/ })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Support resources' })).toBeVisible();
  await expectAccessible(page);
});

test('a daily check-in is saved and listed', async ({ page }) => {
  await startAnonymously(page);
  const card = page.locator('form').filter({ has: page.getByText('Mood (1 low, 5 good)') });
  await card.locator('label').filter({ hasText: /^4$/ }).first().click();
  await card.locator('fieldset').nth(1).locator('label').filter({ hasText: /^3$/ }).click();
  await page.getByLabel('Hours of sleep (optional)').fill('7');
  await page.getByRole('button', { name: 'Save check-in' }).click();
  await expect(page.getByText('Saved. Thank you for checking in.')).toBeVisible();
  await expect(page.getByText(/mood 4, energy 3/)).toBeVisible();
  await expectAccessible(page);
});

test('people can export their data and delete their account for good', async ({ page }) => {
  await startAnonymously(page, true);
  await page.goto('/app/privacy');
  await expectAccessible(page);

  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download my data' }).click();
  expect((await download).suggestedFilename()).toBe('mindguard-export.json');

  await page.getByRole('button', { name: 'Delete my account' }).click();
  await page.getByRole('button', { name: 'Yes, I want to delete it' }).click();
  await page.getByRole('button', { name: 'Delete everything now' }).click();
  await expect(page).toHaveURL(/\/$/);
  expect((await page.request.get('/api/v1/auth/me')).status()).toBe(401);
});
