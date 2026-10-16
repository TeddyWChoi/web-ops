const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  p.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
  const url = 'file://' + process.cwd() + '/web-ops.html';
  for (const h of ['overview','p-sf2','p-latale','p-closers','p-uwo','p-admin','minutes','team']) {
    await p.goto(url + '#' + h); await p.waitForTimeout(300);
    await p.screenshot({ path: `s-${h}.png`, fullPage: true });
  }
  // mobile
  const m = await b.newPage({ viewport: { width: 390, height: 844 } });
  await m.goto(url + '#overview'); await m.waitForTimeout(300);
  await m.screenshot({ path: 's-mobile.png', fullPage: false });
  const sw = await m.evaluate(() => document.documentElement.scrollWidth);
  console.log('mobile scrollWidth', sw, 'errors', JSON.stringify(errs));
  await b.close();
})();
