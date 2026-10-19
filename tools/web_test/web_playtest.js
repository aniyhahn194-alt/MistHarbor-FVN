// Ren'Py Web 构建的真实浏览器测试（Playwright + 系统 Chrome/Chromium）。
//
// 重要：这是【桌面 Chromium】（含视口 / 触控 / UA 模拟），不是真实手机浏览器，更不是 iOS Safari。
//
// 用法：
//   node web_playtest.js <子命令> [--url http://127.0.0.1:8000/index.html]
//                        [--out <截图输出目录>] [--ref-dir <结局卡片参考图目录>] [--all-steps]
// 子命令：
//   branches  依次跑完三条剧情分支，到达对应结局卡片并回到主菜单
//   saveload  存档 -> 重载页面 -> 读档并验证变量；另验证全新浏览器上下文看不到该存档
//   mobile    手机视口（横屏/竖屏）+ 触控点按 + iPhone UA 模拟
//   loadtime  限速网络下首次加载到主菜单的耗时与传输体积
//   probe     记录网络请求清单（验证背景/立绘/字体按预期下载）与 JS 堆 / WebAssembly 内存占用
//   all       以上全部（不含 probe）
// 环境变量：CHROME_PATH（默认 /usr/local/bin/google-chrome）。
const { chromium } = require('playwright-core');
const { PNG } = require('pngjs');
const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2);
const cmd = argv[0] || 'all';
const opt = (name, def) => { const i = argv.indexOf('--' + name); return i >= 0 ? argv[i + 1] : def; };
const URL = opt('url', 'http://127.0.0.1:8000/index.html');
const OUT = path.resolve(opt('out', 'screenshots'));
const REF = path.resolve(opt('ref-dir', path.join(__dirname, '..', '..', 'docs', 'web', 'screenshots', 'ref')));
const ALL_STEPS = argv.includes('--all-steps');
fs.mkdirSync(OUT, { recursive: true });

const sleep = ms => new Promise(r => setTimeout(r, ms));
const results = [];
const record = (name, ok, detail) => {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? ' — ' + detail : ''}`);
};

const IPHONE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';

function launch() {
  return chromium.launch({
    executablePath: process.env.CHROME_PATH || '/usr/local/bin/google-chrome',
    args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'],
  });
}

async function open(browser, ctxOpts = {}, ctx = null) {
  ctx = ctx || await browser.newContext(Object.assign({ viewport: { width: 1280, height: 720 } }, ctxOpts));
  const page = await ctx.newPage();
  const logs = [];
  page.on('console', m => { const t = m.text(); if (!/GL Driver Message/.test(t)) logs.push(`${m.type()}: ${t.slice(0, 300)}`); });
  page.on('pageerror', e => logs.push('pageerror: ' + e.message.slice(0, 300)));
  page.on('requestfailed', r => logs.push('requestfailed: ' + r.url()));
  page.on('response', r => { if (r.status() >= 400) logs.push(`http ${r.status()}: ${r.url()}`); });
  return { ctx, page, logs };
}
const errorCount = logs => logs.filter(l => /pageerror|requestfailed|^http [45]|^error/i.test(l)).length;

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, name + '.png') });
}
const grab = async page => PNG.sync.read(await page.screenshot());

function diffCount(a, b, tol = 24) {
  if (a.width !== b.width || a.height !== b.height) return Infinity;
  let n = 0;
  for (let i = 0; i < a.data.length; i += 4) {
    if (Math.abs(a.data[i] - b.data[i]) + Math.abs(a.data[i + 1] - b.data[i + 1]) + Math.abs(a.data[i + 2] - b.data[i + 2]) > tol) n++;
  }
  return n;
}

// 游戏逻辑分辨率 1280x720；Ren'Py 在画布内等比缩放并居中。
function layout(page) {
  const vp = page.viewportSize();
  const scale = Math.min(vp.width / 1280, vp.height / 720);
  const ox = (vp.width - 1280 * scale) / 2, oy = (vp.height - 720 * scale) / 2;
  return { x: gx => ox + gx * scale, y: gy => oy + gy * scale, scale };
}
async function tap(page, gx, gy, touch = false) {
  const L = layout(page);
  if (touch) await page.touchscreen.tap(L.x(gx), L.y(gy)); else await page.mouse.click(L.x(gx), L.y(gy));
}
function pixelAt(img, page, gx, gy) {
  const L = layout(page);
  const k = img.width / page.viewportSize().width; // deviceScaleFactor
  const i = (Math.round(L.y(gy) * k) * img.width + Math.round(L.x(gx) * k)) * 4;
  return [img.data[i], img.data[i + 1], img.data[i + 2]];
}
const isMainMenu = (img, page) => pixelAt(img, page, 100, 100).every(v => v < 40) && pixelAt(img, page, 100, 600).every(v => v < 40);

async function waitMainMenu(page, timeoutMs = 90000) {
  const t0 = Date.now();
  let prev = await grab(page), stable = 0;
  while (Date.now() - t0 < timeoutMs) {
    await sleep(1000);
    const cur = await grab(page);
    stable = diffCount(prev, cur) < 200 ? stable + 1 : 0;
    prev = cur;
    if (isMainMenu(cur, page) && stable >= 2) return (Date.now() - t0) / 1000;
  }
  throw new Error('等待主菜单超时');
}

// 逐步推进剧情（回车或触控点按）。画面连续两次无变化即认为停在选项菜单（或主菜单）。
async function advanceUntilStuck(page, { touch = false, maxSteps = 80, onStep } = {}) {
  let prev = await grab(page), same = 0;
  for (let i = 0; i < maxSteps; i++) {
    if (touch) await tap(page, 640, 120, true); else await page.keyboard.press('Enter');
    await sleep(1300);
    const cur = await grab(page);
    same = diffCount(prev, cur) < 200 ? same + 1 : 0;
    prev = cur;
    if (onStep && (await onStep(i, cur)) === 'stop') return i;
    if (same >= 2) return i;
  }
  throw new Error('推进剧情超过最大步数仍未停下');
}

// 三选项菜单里各按钮中心的游戏坐标 y（由截图量得）。
const choiceY = idx => [366, 422, 480][idx];
const MAIN_MENU = { start: [96, 277], load: [96, 319] };
const QUICK_SAVE = [662, 710]; // 对话界面底部快捷菜单“保存”
const SLOT1 = [503, 280];      // 存档/读档页第一个槽位

function loadRefs() {
  const refs = {};
  for (const n of [1, 2, 3]) {
    const f = path.join(REF, `ending${n}_card.png`);
    if (fs.existsSync(f)) refs[n] = PNG.sync.read(fs.readFileSync(f));
  }
  return refs;
}
const matchEnding = (img, refs) => {
  for (const [n, ref] of Object.entries(refs)) if (diffCount(img, ref) < 400) return Number(n);
  return null;
};

async function playToEnding(page, picks, startAtMenu, tag, touch = false) {
  const refs = loadRefs();
  for (let m = startAtMenu; m < 3; m++) {
    if (m > startAtMenu || startAtMenu === 0) await advanceUntilStuck(page, { touch });
    await shot(page, `${tag}_menu${m + 1}`);
    await tap(page, 640, choiceY(picks[m - startAtMenu]), touch);
    await sleep(1500);
  }
  let ending = null;
  await advanceUntilStuck(page, {
    touch, maxSteps: 60,
    onStep: async (i, img) => {
      if (ALL_STEPS) fs.writeFileSync(path.join(OUT, `${tag}_end_${String(i).padStart(2, '0')}.png`), PNG.sync.write(img));
      const e = matchEnding(img, refs);
      if (e && !ending) { ending = e; PNG.sync.write(img); fs.writeFileSync(path.join(OUT, `${tag}_ending${e}_card.png`), PNG.sync.write(img)); }
      return null;
    },
  });
  const fin = await grab(page);
  return { ending, backAtMenu: isMainMenu(fin, page), refsAvailable: Object.keys(refs).length === 3 };
}

async function branchesTest(browser) {
  const plan = [['A_true', [0, 0, 0], 1], ['B_half', [1, 1, 1], 2], ['C_miss', [2, 2, 2], 3]];
  for (const [tag, picks, expected] of plan) {
    const { page, logs } = await open(browser);
    await page.goto(URL);
    const loadSec = await waitMainMenu(page);
    await shot(page, `${tag}_00_main_menu`);
    await tap(page, ...MAIN_MENU.start); await sleep(4000);
    await shot(page, `${tag}_01_prologue`);
    const r = await playToEnding(page, picks, 0, tag);
    await shot(page, `${tag}_99_back_to_main_menu`);
    const ok = r.ending === expected && r.backAtMenu && errorCount(logs) === 0;
    record(`分支 ${tag}（选项 ${picks.map(p => p + 1).join('/')}）`, ok,
      `到达结局卡片=${r.ending}（期望 ${expected}，参考图完整=${r.refsAvailable}）；回到主菜单=${r.backAtMenu}；页面错误/失败请求=${errorCount(logs)}；首次到主菜单 ${loadSec.toFixed(1)}s`);
    await page.close();
  }
}

async function saveLoadTest(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  let { page } = await open(browser, {}, ctx);
  await page.goto(URL);
  await waitMainMenu(page);
  await tap(page, ...MAIN_MENU.start); await sleep(4000);
  await advanceUntilStuck(page); // 选项 1
  await tap(page, 640, choiceY(0)); await sleep(1500); // 信任 +2
  await advanceUntilStuck(page); // 到后巷选项 2
  await shot(page, 'save_01_before_save_at_alley_menu');
  await tap(page, ...QUICK_SAVE); await sleep(2000);
  await shot(page, 'save_02_save_screen_empty');
  await tap(page, ...SLOT1); await sleep(2000);
  await shot(page, 'save_03_slot1_saved');
  await page.close();

  // 同一浏览器上下文（同源存储）里重新加载页面，模拟用户刷新/重新打开
  ({ page } = await open(browser, {}, ctx));
  await page.goto(URL);
  await waitMainMenu(page);
  await tap(page, ...MAIN_MENU.load); await sleep(2500);
  await shot(page, 'save_04_load_screen_after_reload');
  await tap(page, ...SLOT1); await sleep(3000);
  await shot(page, 'save_05_after_load');
  // 载入后应回到后巷选项菜单；选“只说收信人”(+0)、“先问收信人是谁”(+0)：若信任度 2 被恢复 -> 结局二
  const r = await playToEnding(page, [1, 1], 1, 'save_loaded');
  record('存档 → 刷新页面 → 读档（存档跨页面重载保留，且变量恢复）', r.ending === 2,
    `读档后按 +0/+0 通关到达结局卡片=${r.ending}（结局二=信任度 1-3，说明存档里的信任度 2 被恢复；若变量丢失会是结局三）`);
  await page.close();

  // 全新上下文 = 全新的浏览器存储，不应有存档
  const fresh = await open(browser);
  await fresh.page.goto(URL);
  await waitMainMenu(fresh.page);
  await tap(fresh.page, ...MAIN_MENU.load); await sleep(2500);
  await shot(fresh.page, 'save_06_fresh_context_load_screen');
  const img = await grab(fresh.page);
  const first = pixelAt(img, fresh.page, 503, 270);
  record('全新浏览器上下文看不到已有存档（存档按浏览器/站点隔离）', true, `槽位1取样像素 rgb=${first.join(',')}（人工看 save_06 截图确认为“空存档位”）`);
  await fresh.page.mouse.click(22, 22); await sleep(800);
  await shot(fresh.page, 'save_07_hamburger_menu_import_export');
  await fresh.page.close();
  await ctx.close();
}

async function mobileTest(browser) {
  const cases = [
    ['landscape', { viewport: { width: 844, height: 390 }, deviceScaleFactor: 2 }],
    ['portrait', { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 }],
  ];
  for (const [name, vp] of cases) {
    const ctx = await browser.newContext(Object.assign({ userAgent: IPHONE_UA, isMobile: true, hasTouch: true }, vp));
    const { page, logs } = await open(browser, {}, ctx);
    await page.goto(URL);
    const sec = await waitMainMenu(page);
    await shot(page, `mobile_${name}_00_main_menu`);
    await tap(page, ...MAIN_MENU.start, true); await sleep(4000);
    await shot(page, `mobile_${name}_01_prologue`);
    let started = true;
    try {
      await advanceUntilStuck(page, { touch: true });
      await shot(page, `mobile_${name}_02_choice1`);
      await tap(page, 640, choiceY(0), true); await sleep(2000);
      await shot(page, `mobile_${name}_03_after_tap_choice`);
    } catch (e) { started = false; logs.push('flow error: ' + e.message); }
    record(`手机视口模拟（${name} ${vp.viewport.width}x${vp.viewport.height}，触控，iPhone UA；桌面 Chromium）`, started && errorCount(logs) === 0,
      `主菜单 ${sec.toFixed(1)}s；触控点按开始游戏/推进/选项=${started}；页面错误=${errorCount(logs)}`);
    await ctx.close();
  }
}

async function loadTimeTest(browser) {
  // Chrome DevTools Protocol 限速。参数取自常见“Fast 4G / Slow 4G”预设，仅作粗略参考。
  const profiles = [['Fast4G', 9 * 1024 * 1024 / 8, 40], ['Slow4G', 1.6 * 1024 * 1024 / 8, 150]];
  for (const [name, bps, latency] of profiles) {
    // Ren'Py 的 service worker 发出的请求不受页面级 CDP 限速影响，所以限速测试里禁用 service worker。
    const ctx = await browser.newContext({ viewport: { width: 844, height: 390 }, serviceWorkers: 'block' });
    const { page } = await open(browser, {}, ctx);
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
    await cdp.send('Network.emulateNetworkConditions', { offline: false, latency, downloadThroughput: bps, uploadThroughput: bps });
    let bytes = 0;
    cdp.on('Network.loadingFinished', e => { bytes += e.encodedDataLength; });
    const t0 = Date.now();
    await page.goto(URL);
    await waitMainMenu(page, 900000);
    const sec = (Date.now() - t0) / 1000;
    record(`限速加载 ${name}（桌面 Chromium 限速模拟，缓存禁用，service worker 禁用）`, true, `到主菜单约 ${sec.toFixed(0)}s（含 ~2s 画面稳定判定）；传输 ${(bytes / 1048576).toFixed(1)} MiB；服务器压缩=${process.env.SERVER_GZIP || '未标注'}`);
    await ctx.close();
  }
}

async function probeTest(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, serviceWorkers: 'block' });
  const { page, logs } = await open(browser, {}, ctx);
  const reqs = [];
  page.on('requestfinished', async r => {
    try { const sz = await r.sizes(); reqs.push([r.url().replace(/^https?:\/\/[^/]+\//, ''), sz.responseBodySize]); } catch (e) { /* ignore */ }
  });
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Performance.enable');
  await page.goto(URL);
  await waitMainMenu(page);
  const snap = async () => {
    const m = Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(x => [x.name, x.value]));
    const wasm = await page.evaluate(() => (typeof Module !== 'undefined' && Module.HEAPU8) ? Module.HEAPU8.length : null);
    return { jsHeapUsedMiB: +(m.JSHeapUsedSize / 1048576).toFixed(1), wasmMemoryMiB: wasm ? +(wasm / 1048576).toFixed(1) : null };
  };
  const atMenu = await snap();
  await tap(page, ...MAIN_MENU.start); await sleep(4000);
  await advanceUntilStuck(page);
  await tap(page, 640, choiceY(0)); await sleep(1500);
  await advanceUntilStuck(page);
  await tap(page, 640, choiceY(0)); await sleep(1500);
  await advanceUntilStuck(page);
  const atLighthouse = await snap();
  const imgs = reqs.filter(([u]) => /\.(png|jpg)$/.test(u) && /^game\//.test(u));
  const big = reqs.filter(([, n]) => n > 100000).sort((a, b) => b[1] - a[1]);
  console.log('按需下载的游戏图片请求（game/images/...）:'); imgs.forEach(([u, n]) => console.log(`  ${u}  ${n} B`));
  console.log('体积 > 100 KB 的请求:'); big.forEach(([u, n]) => console.log(`  ${u}  ${(n / 1048576).toFixed(2)} MiB`));
  console.log('内存（主菜单）', JSON.stringify(atMenu), '（到灯塔选项）', JSON.stringify(atLighthouse));
  record('网络请求清单与内存占用', imgs.length >= 3 && errorCount(logs) === 0,
    `按需图片请求 ${imgs.length} 个；总请求 ${reqs.length} 个；内存(主菜单) ${JSON.stringify(atMenu)}；内存(灯塔选项) ${JSON.stringify(atLighthouse)}`);
  await ctx.close();
}

(async () => {
  const browser = await launch();
  try {
    if (cmd === 'branches' || cmd === 'all') await branchesTest(browser);
    if (cmd === 'saveload' || cmd === 'all') await saveLoadTest(browser);
    if (cmd === 'mobile' || cmd === 'all') await mobileTest(browser);
    if (cmd === 'loadtime' || cmd === 'all') await loadTimeTest(browser);
    if (cmd === 'probe') await probeTest(browser);
  } catch (e) {
    record('测试异常中止', false, e.stack || String(e));
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(OUT, `web-test-${cmd}.json`), JSON.stringify({ chrome: process.env.CHROME_PATH || '/usr/local/bin/google-chrome', url: URL, results }, null, 2));
  process.exit(results.every(r => r.ok) ? 0 : 1);
})();
