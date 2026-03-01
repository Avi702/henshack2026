const puppeteer = require('puppeteer');

(async () => {
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();

    page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
    page.on('pageerror', error => console.error('BROWSER ERROR:', error.message));

    await page.goto('http://localhost:3002/3d/placeholder.html?type=bench');
    await page.waitForTimeout(2000);
    await browser.close();
})();
