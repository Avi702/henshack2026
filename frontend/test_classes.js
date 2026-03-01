const puppeteer = require('puppeteer');
(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    await page.goto('http://localhost:3002/');
    await new Promise(r => setTimeout(r, 2000));
    
    const elements = await page.$$eval('.animate-page-enter', els => els.length);
    console.log('Number of animate-page-enter elements found:', elements);
    
    const opacity = await page.$eval('.animate-page-enter', el => window.getComputedStyle(el).opacity);
    console.log('Opacity of animate-page-enter:', opacity);
    
    await browser.close();
})();
