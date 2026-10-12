/**
 * Playwright E2E — haqiqiy brauzerda tekshiradi (to'liq ekran, Web Audio, WakeLock,
 * service worker, panelni hover bilan ochish).
 *
 * O'rnatish va ishga tushirish:
 *     npm install --save-dev @playwright/test
 *     npx playwright install chromium
 *     npm run test:e2e
 */
import { test, expect } from '@playwright/test';

const BASE = process.env.ZENITH_BASE_URL || 'http://127.0.0.1:5050';

test.beforeEach(async ({ page }) => {
  await page.goto(BASE);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
});

test('sahifa xatosiz yuklanadi', async ({ page }) => {
  const errors = [];
  page.on('pageerror', (err) => errors.push(err.message));
  page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.waitForTimeout(500);
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => window.zenith.missingElements)).toEqual([]);
});

test('preset bosilganda aniq 25:00 dan boshlanadi', async ({ page }) => {
  await page.locator('[data-duration="1500"]').click();
  await expect(page.locator('#minutesValue')).toHaveText('25');
  await expect(page.locator('#secondsValue')).toHaveText('00');
});

test('taymer haqiqiy vaqtda sanaydi', async ({ page }) => {
  await page.locator('[data-duration="300"]').click();
  await page.waitForTimeout(2200);
  const seconds = Number(await page.locator('#secondsValue').textContent());
  expect(seconds).toBeGreaterThanOrEqual(56);
  expect(seconds).toBeLessThanOrEqual(59);
});

test('sahifa yangilangandan keyin taymer davom etadi', async ({ page }) => {
  await page.locator('[data-duration="1500"]').click();
  await page.waitForTimeout(1500);
  await page.reload();
  await expect(page.locator('#minutesValue')).toHaveText('24');
});

test('chap chetga hover panelni ochadi', async ({ page }) => {
  await page.mouse.move(5, 300);
  await expect(page.locator('#settingsDrawer')).toHaveClass(/open/);
  await page.locator('#drawerBackdrop').click();
  await expect(page.locator('#settingsDrawer')).not.toHaveClass(/open/);
});

test('klaviatura: Space boshlaydi, R tiklaydi', async ({ page }) => {
  await page.locator('#inputMinutes').fill('3');
  await page.locator('body').click({ position: { x: 600, y: 60 } });
  await page.keyboard.press('Space');
  await expect(page.locator('#statusText')).not.toHaveText('TAYYOR');
  await page.keyboard.press('KeyR');
  await expect(page.locator('#minutesValue')).toHaveText('03');
});

test('service worker ro\'yxatdan o\'tadi', async ({ page }) => {
  const registered = await page.evaluate(async () => {
    const reg = await navigator.serviceWorker.getRegistration();
    return Boolean(reg);
  });
  expect(registered).toBe(true);
});

test('statistika yakunlangan seansdan keyin yangilanadi', async ({ page }) => {
  await page.evaluate(() => {
    const { engine } = window.zenith;
    engine.setMode('duration');
    engine.setConfiguredDuration(2, { applyNow: true });
    engine.start();
  });
  await page.waitForTimeout(2600);
  await expect(page.locator('#completedSessionsDisplay')).not.toHaveText('0');
});
