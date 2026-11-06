const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  // 折叠动画中途
  const p = await b.newPage({ viewport: { width: 749, height: 827 }, deviceScaleFactor: 2 });
  await p.goto('file://' + path.resolve(__dirname, 'index.html') + '#dev');
  await p.waitForFunction(() => !!window.__FP);
  await p.click('#btnGo'); await p.waitForTimeout(300);
  await p.evaluate(() => { window.__FP.level(12); window.__FP.fold('L', 4); });
  await p.waitForTimeout(95);
  await p.screenshot({ path: 'shot-anim.png' });
  await p.waitForTimeout(400);

  // 窄屏
  const p2 = await b.newPage({ viewport: { width: 360, height: 640 }, deviceScaleFactor: 3 });
  await p2.goto('file://' + path.resolve(__dirname, 'index.html') + '#dev');
  await p2.waitForFunction(() => !!window.__FP);
  await p2.click('#btnGo'); await p2.waitForTimeout(300);
  await p2.evaluate(() => window.__FP.level(8));
  await p2.waitForTimeout(300);
  await p2.screenshot({ path: 'shot-narrow.png' });
  await b.close();
})();
