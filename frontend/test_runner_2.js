const puppeteer = require('puppeteer');
const fs = require('fs');

let content = fs.readFileSync('/Users/avnee/henshack2026/frontend/public/3d/placeholder.html', 'utf-8');
content = content.replace("new URLSearchParams(location.search).get('type')", "'bench'");

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
    
    // Serve via data URI to bypass need for HTTP server
    const dataUri = 'data:text/html;charset=utf-8,' + encodeURIComponent(content);
    
    await page.goto(dataUri);
    await new Promise(r => setTimeout(r, 2000));
    await browser.close();
    process.exit(0);
})();
