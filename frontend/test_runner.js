const { exec } = require('child_process');
const server = exec('npx serve -p 3005 public/3d');

setTimeout(() => {
  const puppeteer = require('puppeteer');
  (async () => {
      const browser = await puppeteer.launch();
      const page = await browser.newPage();
      page.on('console', msg => console.log('PAGE LOG:', msg.text()));
      page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
      
      await page.goto('http://localhost:3005/placeholder.html?type=bench');
      await new Promise(r => setTimeout(r, 1000));
      await browser.close();
      server.kill();
      process.exit(0);
  })();
}, 3000);
