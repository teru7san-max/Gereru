// Render week1-tn.html → PDF (one card per page) and week1-tn-print.html → A4 PDF.
// usage: node print.js   (needs playwright; NODE_PATH may need the global node_modules)
const { chromium } = require('playwright');
const path = require('path');

const jobs = [
  ['week1-tn.html', 'October_2026_W1_TN.pdf'],
  ['week1-tn-print.html', 'October_2026_W1_TN_print_A4_reversed.pdf'],
];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const [src, out] of jobs) {
    await page.goto('file://' + path.join(__dirname, src), { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.pdf({ path: path.join(__dirname, out), preferCSSPageSize: true, printBackground: true });
    console.log('wrote', out);
  }
  await browser.close();
})();
