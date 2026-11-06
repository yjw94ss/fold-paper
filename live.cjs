const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 749, height: 827 }, deviceScaleFactor: 2 });
  const errs = [], reqs = [];
  p.on('pageerror', e => errs.push('pageerror: ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  p.on('request', r => reqs.push(r.url()));

  // 1. 正式入口（无 #dev）不应暴露测试钩子
  await p.goto('https://yjw94ss.github.io/fold-paper/', { waitUntil: 'load' });
  await p.waitForTimeout(1200);
  const prod = await p.evaluate(() => ({
    hook: typeof window.__FP,
    title: document.title,
    veil: !document.getElementById('veil').classList.contains('hide')
  }));
  console.log('正式入口:', JSON.stringify(prod));

  // 2. 带 #dev 跑一遍真实折叠
  await p.goto('https://yjw94ss.github.io/fold-paper/#dev', { waitUntil: 'load' });
  await p.reload({ waitUntil: 'load' });          // 仅改 hash 不会重跑脚本，强制重载
  await p.waitForFunction(() => !!window.__FP, null, { timeout: 15000 });
  await p.click('#btnGo'); await p.waitForTimeout(300);
  const h = await p.evaluate(() => {
    const hh = window.__FP.handle('U'), r = document.getElementById('cv').getBoundingClientRect();
    const s = window.__FP.toScreen(0, 0);
    return { x: r.left + hh.x, y: r.top + hh.y, top: r.top + s.y, cs: s.cs };
  });
  await p.mouse.move(h.x, h.y); await p.mouse.down();
  await p.mouse.move(h.x, h.top + h.cs * 0.9, { steps: 8 });
  await p.mouse.up(); await p.waitForTimeout(1400);
  const st = await p.evaluate(() => window.__FP.state());
  const ui = await p.evaluate(() => window.__FP.ui());
  console.log('线上折叠:', JSON.stringify({ steps: st.steps, holes: st.holes.length, w: st.w, h: st.h }));
  console.log('过关面板:', ui.veil, '|', ui.veilText.slice(0, 26));

  // 3. 截一张线上首屏
  await p.goto('https://yjw94ss.github.io/fold-paper/', { waitUntil: 'load' });
  await p.waitForTimeout(900);
  await p.screenshot({ path: 'live-shot.png' });

  const ext = reqs.filter(u => !u.startsWith('https://yjw94ss.github.io') && !u.startsWith('data:'));
  console.log('外部请求:', ext.length, ext.slice(0, 3));
  console.log('错误:', errs.length, errs.slice(0, 3));
  await b.close();
  process.exit(errs.length ? 1 : 0);
})();
