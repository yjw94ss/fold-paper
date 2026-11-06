const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 749, height: 827 }, deviceScaleFactor: 2 });
  await p.goto('file://' + path.resolve(__dirname, 'index.html') + '#dev');
  await p.waitForFunction(() => !!window.__FP);
  await p.waitForTimeout(400);
  await p.screenshot({ path: 'shot-start.png' });

  await p.click('#btnGo'); await p.waitForTimeout(400);
  await p.evaluate(() => window.__FP.level(0));
  await p.waitForTimeout(200);
  await p.screenshot({ path: 'shot-l1.png' });

  // 拖到折痕预览状态
  const h = await p.evaluate(() => {
    const hh = window.__FP.handle('U'), r = document.getElementById('cv').getBoundingClientRect();
    const s = window.__FP.toScreen(0, 0);
    return { x: r.left + hh.x, y: r.top + hh.y, cs: s.cs, top: r.top + s.y };
  });
  await p.mouse.move(h.x, h.y); await p.mouse.down();
  await p.mouse.move(h.x, h.top + h.cs * 0.95, { steps: 8 });
  await p.waitForTimeout(220);
  await p.screenshot({ path: 'shot-drag.png' });
  await p.mouse.up(); await p.waitForTimeout(1400);
  await p.screenshot({ path: 'shot-win.png' });
  await p.click('#bList'); await p.waitForTimeout(400);
  await p.screenshot({ path: 'shot-list.png' });
  await p.click('#bClose'); await p.waitForTimeout(300);

  // 大关中途
  await p.evaluate(() => {
    window.__FP.level(15);
    window.__FP.foldNow('U', 2); window.__FP.foldNow('U', 3);
  });
  await p.waitForTimeout(300);
  await p.screenshot({ path: 'shot-l16.png' });
  await b.close();
})();
