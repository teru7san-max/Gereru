// Print TN HTML files to PDF with Chromium.
// usage: node print.js in.html out.pdf [in2.html out2.pdf ...]
// (needs playwright; if it isn't found, run with NODE_PATH="$(npm root -g)")
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const args = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (let i = 0; i + 1 < args.length; i += 2) {
    await page.goto('file://' + path.resolve(args[i]), { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.pdf({ path: path.resolve(args[i + 1]), preferCSSPageSize: true, printBackground: true });
    console.log('wrote', path.basename(args[i + 1]));
  }
  await browser.close();
})();
