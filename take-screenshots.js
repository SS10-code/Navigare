const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });

  await context.addCookies([
    { name: 'navigare_guest_mode', value: 'true', domain: 'localhost', path: '/' },
    { name: 'navigare_onboarded', value: 'false', domain: 'localhost', path: '/' },
  ]);

  const page = await context.newPage();
  await page.goto('http://localhost:3000/dashboard/upload', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '/tmp/nav-dashboard.png', fullPage: false });
  console.log('Captured: nav-dashboard');

  await page.goto('http://localhost:3000/feedback', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '/tmp/nav-feedback.png', fullPage: false });
  console.log('Captured: nav-feedback');

  await browser.close();
})();
