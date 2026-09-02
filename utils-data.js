const { chromium } = require('playwright');

const BASE_URL = process.env.TARGET_URL || 'https://navigare-one.vercel.app';
const TOTAL_SESSIONS = parseInt(process.env.SESSIONS) || 200;
const CONCURRENCY = parseInt(process.env.CONCURRENCY) || 3;
const DELAY_BETWEEN_SESSIONS = parseInt(process.env.DELAY) || 2000;
const ONBOARD_RATE = parseFloat(process.env.ONBOARD_RATE) || 0.36;

async function simulateGuestSession(sessionId, browser) {
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    viewport: { width: 1366, height: 768 },
    locale: 'en-US',
    timezoneId: 'America/New_York',
  });

  const page = await context.newPage();
  const shouldOnboard = Math.random() < ONBOARD_RATE;

  try {
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });

    const guestButton = page.locator('button:has-text("Use Without Account"), button:has-text("Continue as Guest"), a:has-text("Use Without Account")').first();
    
    await guestButton.waitFor({ state: 'visible', timeout: 30000 });
    await guestButton.click();

    await page.waitForURL('**/dashboard/upload**', { timeout: 30000 });
    await page.waitForTimeout(2000);

    if (shouldOnboard) {
      try {
        const skipButton = page.locator('button:has-text("Skip for now")');
        await skipButton.waitFor({ state: 'visible', timeout: 5000 });
        await skipButton.click();
        await page.waitForTimeout(2000);
      } catch {}
    }

    return true;

  } catch (error) {
    return false;
  } finally {
    await context.close();
  }
}

async function runSessionWorker(sessionIds, browser) {
  let success = 0;
  let failed = 0;
  
  for (const id of sessionIds) {
    const result = await simulateGuestSession(id, browser);
    if (result) success++; else failed++;
    await new Promise(resolve => setTimeout(resolve, DELAY_BETWEEN_SESSIONS));
  }
  
  return { success, failed };
}

async function main() {
  console.log(`Starting ${TOTAL_SESSIONS} guest sessions on ${BASE_URL}`);
  console.log(`Onboard rate: ${ONBOARD_RATE * 100}%`);

  const browser = await chromium.launch({
    headless: true,
    args: ['--disable-blink-features=AutomationControlled', '--no-sandbox', '--disable-setuid-sandbox'],
  });

  const sessionIds = Array.from({ length: TOTAL_SESSIONS }, (_, i) => i + 1);
  const chunks = [];
  
  for (let i = 0; i < sessionIds.length; i += CONCURRENCY) {
    chunks.push(sessionIds.slice(i, i + CONCURRENCY));
  }

  const workers = chunks.map(chunk => runSessionWorker(chunk, browser));
  const results = await Promise.all(workers);

  await browser.close();

  const totalSuccess = results.reduce((sum, r) => sum + r.success, 0);
  const totalFailed = results.reduce((sum, r) => sum + r.failed, 0);
  const expectedOnboarded = Math.floor(totalSuccess * ONBOARD_RATE);
  
  console.log(`\nSuccess: ${totalSuccess}, Failed: ${totalFailed}`);
  console.log(`Expected onboarded: ~${expectedOnboarded}`);
}

main().catch(console.error);