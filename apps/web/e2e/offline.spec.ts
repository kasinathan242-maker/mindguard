import { expect, test } from '@playwright/test';

test('breathing guide and crisis numbers work offline after the first visit', async ({
  page,
  context,
}) => {
  await page.goto('/');
  await page.evaluate(async () => {
    await navigator.serviceWorker.ready;
  });
  await page.reload(); // now controlled by the service worker
  await context.setOffline(true);
  await page.reload();

  await expect(page.getByRole('button', { name: /Pause|Resume/ })).toBeVisible();
  await expect(page.getByRole('link', { name: /Tele-MANAS 14416/ })).toHaveAttribute(
    'href',
    'tel:14416',
  );
  await context.setOffline(false);
});
