import { test, expect } from '@playwright/test';

test('clear cache button', async ({ page }) => {
  await page.goto('./test');
  await expect(page.locator('#loadingScreen')).toHaveCount(0, { timeout: 15000 });
  // Register the response waiter before clicking: the cache-clear POST to the
  // local endpoint can resolve before a waiter added afterwards would subscribe.
  const [response] = await Promise.all([
    page.waitForResponse((res) => res.request().method() === 'POST'),
    page.click('#clearCacheButton'),
  ]);
  expect(response).toBeTruthy();
});


test('format button', async ({ page }) => {
  await page.goto('./test');
  await expect(page.locator('#loadingScreen')).toHaveCount(0, { timeout: 15000 });
  await page.getByRole('textbox', { name: 'Editor content' }).type('SELECT   * WHERE { ?s     ?p ?o}');
  await page.click('#formatButton');
  await expect(page.locator('.view-lines > div:nth-child(1)')).toHaveText('SELECT * WHERE {');
  await expect(page.locator('.view-lines > div:nth-child(2)')).toHaveText('?s ?p ?o');
  await expect(page.locator('.view-lines > div:nth-child(3)')).toHaveText('}');
});
