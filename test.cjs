/* FOLD PAPER 真机验收：Chromium 驱动真实交互 + 逐关对照 Python 标准答案 */
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const FIX = JSON.parse(fs.readFileSync(path.join(__dirname, 'tools/fixture.json'), 'utf8'));
const URL = 'file://' + path.resolve(__dirname, 'index.html') + '#dev';

let pass = 0, fail = 0;
function ok(cond, label, extra) {
  if (cond) { pass++; console.log('  ✓ ' + label + (extra ? '  ' + extra : '')); }
  else { fail++; console.log('  ✗ ' + label + '  ' + (extra || '')); }
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 749, height: 827 }, deviceScaleFactor: 2 });
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });

  await page.goto(URL, { waitUntil: 'load' });
  await page.waitForFunction(() => !!window.__FP, null, { timeout: 8000 });
  await page.waitForTimeout(350);

  /* ── 1. 首屏 ── */
  console.log('\n[1] 启动与首屏');
  const v0 = await page.evaluate(() => window.__FP.ui());
  ok(v0.veil === true, '开场遮罩可见');
  ok(/一纸/.test(v0.veilText), '标题正确', v0.veilText.slice(0, 12));
  const ink = await page.evaluate(() => {
    const c = document.getElementById('cv'), g = c.getContext('2d');
    const d = g.getImageData(0, 0, c.width, c.height).data;
    let n = 0, sum = 0;
    for (let i = 0; i < d.length; i += 40) { if (d[i + 3] > 8) { n++; sum += d[i] + d[i + 1] + d[i + 2]; } }
    return { n, avg: Math.round(sum / Math.max(1, n) / 3) };
  });
  ok(ink.n > 4000, '画布已绘制', '采样点=' + ink.n + ' 均亮=' + ink.avg);

  await page.click('#btnGo');
  await page.waitForTimeout(300);
  ok((await page.evaluate(() => window.__FP.ui().veil)) === false, '点开始后遮罩收起');

  /* ── 2. 真实拖动折叠（不借助测试钩子） ── */
  console.log('\n[2] 真实指针拖动');
  await page.evaluate(() => window.__FP.level(0));
  await page.waitForTimeout(120);
  const hp = await page.evaluate(() => {
    const h = window.__FP.handle('U'), r = document.getElementById('cv').getBoundingClientRect();
    const s = window.__FP.toScreen(0, 0);
    return { hx: r.left + h.x, hy: r.top + h.y, top: r.top + s.y - s.cs / 2, cs: s.cs };
  });
  await page.mouse.move(hp.hx, hp.hy);
  await page.mouse.down();
  // 分几步拖，模拟真实手感并触发中途的刻度反馈
  for (let s = 1; s <= 6; s++) {
    await page.mouse.move(hp.hx, hp.hy + (hp.top + hp.cs * 0.9 - hp.hy) * s / 6, { steps: 3 });
    await page.waitForTimeout(35);
  }
  const mid = await page.evaluate(() => window.__FP.state());
  await page.mouse.up();
  await page.waitForTimeout(500);
  const after = await page.evaluate(() => window.__FP.state());
  ok(mid.steps === 0, '拖动过程中尚未落子', 'steps=' + mid.steps);
  ok(after.steps === 1, '松手后计为 1 折', 'steps=' + after.steps);
  ok(after.holes.length === 1, '两个孔已合成一个', '孔=' + after.holes.length);
  ok(after.holes[0][0] === FIX[0].final[0] && after.holes[0][1] === FIX[0].final[1],
    '落孔坐标与标准答案一致', JSON.stringify(after.holes[0]) + ' vs ' + JSON.stringify(FIX[0].final));
  ok(after.w === FIX[0].endW && after.h === FIX[0].endH, '折后纸张尺寸正确',
    after.w + 'x' + after.h + ' vs ' + FIX[0].endW + 'x' + FIX[0].endH);

  /* ── 3. 胜利面板 ── */
  console.log('\n[3] 过关面板');
  await page.waitForTimeout(700);
  const win = await page.evaluate(() => window.__FP.ui());
  ok(win.veil === true, '过关后弹出面板');
  ok(/三星|★/.test(win.veilText) || /折成/.test(win.veilText), '面板含星级/标题', win.veilText.slice(0, 18));
  const starOn = await page.evaluate(() => document.querySelectorAll('#veil .stars i.on').length);
  ok(starOn === 3, '最优步数得三星', '亮星=' + starOn);

  /* ── 4. 撤销 / 重来 ── */
  console.log('\n[4] 撤销与重来');
  await page.evaluate(() => window.__FP.level(6));   // par=4，多孔关卡
  await page.waitForTimeout(100);
  const before = await page.evaluate(() => window.__FP.state());
  const undoBtn = await page.evaluate(() => window.__FP.ui().undoDisabled);
  ok(undoBtn === true, '开局撤销按钮为禁用');
  await page.evaluate(() => window.__FP.foldNow('L', 3));
  await page.waitForTimeout(60);
  const f1 = await page.evaluate(() => window.__FP.state());
  ok(f1.w * f1.h < before.w * before.h && f1.steps === 1, '折叠后纸面变小且计步',
    before.w + 'x' + before.h + ' → ' + f1.w + 'x' + f1.h);
  ok(f1.holes.length <= before.holes.length, '孔数不增加', before.holes.length + ' → ' + f1.holes.length);
  await page.evaluate(() => window.__FP.undo());
  await page.waitForTimeout(60);
  const f2 = await page.evaluate(() => window.__FP.state());
  ok(f2.holes.length === before.holes.length && f2.w === before.w && f2.steps === 0,
    '撤销完整还原', '孔=' + f2.holes.length + ' 宽=' + f2.w);
  await page.evaluate(() => { window.__FP.foldNow('L', 3); window.__FP.reset(); });
  await page.waitForTimeout(60);
  const f3 = await page.evaluate(() => window.__FP.state());
  ok(f3.holes.length === before.holes.length && f3.steps === 0, '重来还原到开局');

  /* ── 4b. 轻点折一格 / 拖回取消 ── */
  console.log('\n[4b] 轻点与取消');
  const hp2 = await page.evaluate(() => {
    const h = window.__FP.handle('D'), r = document.getElementById('cv').getBoundingClientRect();
    return { x: r.left + h.x, y: r.top + h.y };
  });
  await page.mouse.click(hp2.x, hp2.y);
  await page.waitForTimeout(420);
  const tapSt = await page.evaluate(() => window.__FP.state());
  ok(tapSt.steps === 1, '轻点手柄折一格', 'steps=' + tapSt.steps);

  await page.evaluate(() => window.__FP.level(2));
  await page.waitForTimeout(80);
  const hp3 = await page.evaluate(() => {
    const h = window.__FP.handle('L'), r = document.getElementById('cv').getBoundingClientRect();
    const s = window.__FP.toScreen(0, 0);
    return { x: r.left + h.x, y: r.top + h.y, cs: s.cs };
  });
  await page.mouse.move(hp3.x, hp3.y);
  await page.mouse.down();
  await page.mouse.move(hp3.x + hp3.cs * 2, hp3.y, { steps: 6 });
  await page.mouse.move(hp3.x, hp3.y, { steps: 6 });
  await page.mouse.up();
  await page.waitForTimeout(200);
  const cancelSt = await page.evaluate(() => window.__FP.state());
  ok(cancelSt.steps === 0, '拖出再拖回则取消', 'steps=' + cancelSt.steps);

  /* ── 5. 障碍：非法折被拒绝 ── */
  console.log('\n[5] 规则边界');
  const tooDeep = await page.evaluate(() => {
    window.__FP.level(0);                       // 3x3
    const st = window.__FP.state();
    window.__FP.fold('L', 2);                   // 2k=4 > 3，应被拒
    return { w: st.w, after: window.__FP.state() };
  });
  ok(tooDeep.after.w === tooDeep.w && tooDeep.after.steps === 0, '折过界被拒绝', '宽=' + tooDeep.after.w);

  /* ── 6. 逐关通关（对照 Python 标准答案） ── */
  console.log('\n[6] 18 关全通对照');
  let allGood = true;
  for (const f of FIX) {
    const r = await page.evaluate((f) => {
      window.__FP.level(f.i);
      let st = window.__FP.state();
      const startOK = st.holes.length === f.holesN && st.w === f.w && st.h === f.h;
      for (const [side, k] of f.path) st = window.__FP.foldNow(side, k);
      return {
        startOK, steps: st.steps, n: st.holes.length, hole: st.holes[0],
        w: st.w, h: st.h, won: st.won
      };
    }, f);
    const good = r.startOK && r.steps === f.par && r.n === 1 &&
      r.hole[0] === f.final[0] && r.hole[1] === f.final[1] &&
      r.w === f.endW && r.h === f.endH;
    if (!good) {
      allGood = false;
      console.log('    ✗ L' + (f.i + 1) + ' ' + JSON.stringify(r) + ' 期望 par=' + f.par +
        ' final=' + JSON.stringify(f.final) + ' ' + f.endW + 'x' + f.endH);
    }
  }
  ok(allGood, '18 关全部按最优步数通关且落孔一致');

  /* ── 7. 存档 ── */
  const save = await page.evaluate(() => JSON.parse(localStorage.getItem('foldpaper.v1') || '{}'));
  ok(save.unlocked === 18, '进度已存档', 'unlocked=' + save.unlocked);
  ok(Object.keys(save.stars || {}).length === 18, '18 关均有星级记录');

  /* ── 8. 选关面板 ── */
  console.log('\n[7] 选关');
  await page.evaluate(() => window.__FP.level(0));
  await page.evaluate(() => document.getElementById('btnList').click());
  await page.waitForTimeout(250);
  const list = await page.evaluate(() => ({
    cells: document.querySelectorAll('#list .grid .cell').length,
    lock: document.querySelectorAll('#list .grid .cell.lock').length,
    cur: document.querySelectorAll('#list .grid .cell.cur').length
  }));
  ok(list.cells === 18, '选关网格 18 格', '格=' + list.cells);
  ok(list.lock === 0, '全通关后无锁关卡', '锁=' + list.lock);
  ok(list.cur === 1, '当前关高亮', '高亮=' + list.cur);
  await page.click('#bClose');
  await page.waitForTimeout(200);

  /* ── 9. 多视口布局 ── */
  console.log('\n[8] 多视口布局');
  const views = [[749, 827], [827, 749], [420, 900], [360, 640]];
  for (const [w, h] of views) {
    await page.setViewportSize({ width: w, height: h });
    await page.waitForTimeout(300);
    await page.evaluate(() => window.__FP.level(11));
    await page.waitForTimeout(160);
    const lay = await page.evaluate(() => {
      const cv = document.getElementById('cv'), sr = cv.getBoundingClientRect();
      const deck = document.getElementById('deck').getBoundingClientRect();
      const top = document.getElementById('top').getBoundingClientRect();
      const hinge = document.getElementById('hinge').getBoundingClientRect();
      return {
        ow: document.documentElement.scrollWidth - window.innerWidth,
        oh: document.documentElement.scrollHeight - window.innerHeight,
        cw: Math.round(sr.width), ch: Math.round(sr.height),
        deckBottom: Math.round(deck.bottom), vh: window.innerHeight,
        topH: Math.round(top.height), hingeH: Math.round(hinge.height),
        stageBottom: Math.round(sr.bottom)
      };
    });
    const okLay = lay.ow <= 1 && lay.oh <= 1 && lay.cw > 200 && lay.ch > 200 &&
      lay.deckBottom <= lay.vh + 1 && lay.stageBottom <= lay.deckBottom + 1;
    ok(okLay, w + 'x' + h + ' 无溢出',
      '溢出=' + lay.ow + ',' + lay.oh + ' 画布=' + lay.cw + 'x' + lay.ch +
      ' 控制台底=' + lay.deckBottom + '/' + lay.vh);
    // 纸张是否落在画布内（不压边）
    const fit = await page.evaluate(() => {
      const s = window.__FP.toScreen(0, 0);
      const r = document.getElementById('cv').getBoundingClientRect();
      const st = window.__FP.state();
      const w0 = s.cs * st.w, h0 = s.cs * st.h;
      return {
        left: s.x - s.cs / 2, top: s.y - s.cs / 2,
        right: s.x - s.cs / 2 + w0, bottom: s.y - s.cs / 2 + h0,
        cw: r.width, ch: r.height
      };
    });
    ok(fit.left > 26 && fit.top > 26 && fit.right < fit.cw - 26 && fit.bottom < fit.ch - 20,
      '纸张四周留出手柄空间',
      'L' + Math.round(fit.left) + ' T' + Math.round(fit.top) +
      ' R' + Math.round(fit.cw - fit.right) + ' B' + Math.round(fit.ch - fit.bottom));
  }

  /* ── 10. 控制台 ── */
  console.log('\n[9] 运行时错误');
  ok(errors.length === 0, '无 console/page 错误', errors.slice(0, 3).join(' | '));

  console.log('\n────────────────────────────');
  console.log('通过 ' + pass + ' 项，失败 ' + fail + ' 项');
  await browser.close();
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('测试脚本异常:', e); process.exit(2); });
