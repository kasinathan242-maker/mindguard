import { expect, test, type Page } from '@playwright/test';
import { expectAccessible } from './a11y';

async function startAnonymously(page: Page) {
  await page.goto('/start');
  await page.getByRole('button', { name: "Yes, I'm 18 or older" }).click();
  await page.getByRole('switch', { name: /Store my check-in answers/ }).click();
  await page.getByRole('button', { name: 'Continue anonymously' }).click();
  await expect(page).toHaveURL(/\/app$/);
}

/** Tap the visible option label, as a person would; the radio input itself is visually hidden. */
async function choose(page: Page, label: string) {
  const option = page.locator('label').filter({ hasText: new RegExp(`^${label}$`) });
  await option.click();
  await expect(option.getByRole('radio')).toBeChecked();
}

async function answerPhq9(page: Page, picks: string[]) {
  for (const pick of picks) {
    await choose(page, pick);
    await page.getByRole('button', { name: 'Next' }).click();
  }
}

test.describe('self-checks', () => {
  test('PHQ-9 item 9 opens the crisis card before any result', async ({ page }) => {
    await startAnonymously(page);
    await page.getByRole('link', { name: 'Self-checks' }).first().click();
    await expectAccessible(page);
    await page.getByRole('link', { name: 'Start' }).first().click();

    await expect(
      page.getByRole('heading', { name: 'Little interest or pleasure in doing things' }),
    ).toBeVisible();
    await expectAccessible(page);

    await answerPhq9(page, Array<string>(8).fill('Not at all'));
    await choose(page, 'Several days');

    const dialog = page.getByRole('dialog', { name: "You don't have to go through this alone." });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole('link', { name: /Call Tele-MANAS now: 14416/ })).toHaveAttribute(
      'href',
      'tel:14416',
    );
    await expect(dialog.getByRole('link', { name: /Call 112/ })).toHaveAttribute('href', 'tel:112');
    await expectAccessible(page);

    // The result has not been shown yet: the person is still on item 9.
    await dialog.getByRole('button', { name: 'Close' }).click();
    await expect(
      page.getByRole('heading', { name: /Thoughts that you would be better off dead/ }),
    ).toBeVisible();

    await page.getByRole('button', { name: 'Next' }).click();
    await page.getByRole('button', { name: 'Skip' }).click();
    await expect(page.getByRole('heading', { name: 'Minimal range' })).toBeVisible();
    await expect(page.getByText('This is a screening result, not a diagnosis.')).toBeVisible();
    await expect(page.getByRole('region', { name: 'Support right now' })).toBeVisible();
    await expectAccessible(page);
  });

  test('GAD-7 scores into the right band and appears in history', async ({ page }) => {
    await startAnonymously(page);
    await page.goto('/app/assessments/GAD7');
    for (let i = 0; i < 7; i += 1) {
      await choose(page, 'More than half the days');
      await page.getByRole('button', { name: 'Next' }).click();
    }
    await choose(page, 'Very difficult');
    await page.getByRole('button', { name: 'See my result' }).click();

    await expect(page.getByRole('heading', { name: 'Moderate range' })).toBeVisible();
    await expect(page.getByText('14', { exact: true })).toBeVisible();
    await expect(page.getByRole('dialog')).toBeHidden();

    await page.getByRole('link', { name: 'Back to self-checks' }).click();
    await expect(page.getByText(/Last time: 14 of 21, Moderate/)).toBeVisible();
  });

  test('"Need help now?" opens the crisis card from the dashboard', async ({ page }) => {
    await startAnonymously(page);
    await page.getByRole('button', { name: 'Need help now?' }).click();
    await expect(
      page.getByRole('dialog', { name: "You don't have to go through this alone." }),
    ).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).toBeHidden();
  });
});
