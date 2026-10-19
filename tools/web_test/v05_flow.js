// V0.5 前后对比截图 + 流程冒烟（Playwright + 系统 Chrome）。由 v02_flow.js 改写，界面坐标与 V0.2 相同。
//   --ui before|after：before = main 上的 V0.2-P1 构建；after = V0.5 构建（多一个 splashscreen）。两者按钮坐标相同。
//   额外：捕捉“加载画面”（页面 presplash 阶段、游戏内 splash 阶段）并校验 presplash 图确实是自制的那一张。
//
// 重要：这是【桌面 Chromium】（含视口 / 触控 / iPhone UA 模拟），不是真实手机，更不是 iOS Safari。
//
// 用法：
//   node v05_flow.js compare  --ui before|after --viewport desktop|mobile|mobile932|mobile667 --url http://127.0.0.1:8002/index.html --out <目录> [--only A,B,C]
//   node v05_flow.js saveload --ui after --viewport desktop|mobile ... --url ... --out <目录>
//   视口：desktop = 1280x720；mobile = 844x390；mobile932 = 932x430；mobile667 = 667x375（均为 DPR 2、触控、iPhone UA 的桌面 Chromium 模拟）
// compare：从主菜单开始，真实点击/按键走完 3 条分支（选项 1/1/1、2/2/2、3/3/3），沿途保存
//          加载画面 / 主菜单 / 三段对话 / 三次选项 / 三个结局对白与结局卡片 的截图，并核对到达的结局。
// saveload：第一个选项后在第二次选择处存档 -> 刷新页面 -> 读档 -> 按 +0/+0 通关，应到达结局二（信任度 2 被恢复）。

const { chromium } = require('playwright-core');
const { PNG } = require('pngjs');
const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2);
const cmd = argv[0] || 'compare';
const opt = (n, d) => { const i = argv.indexOf('--' + n); return i >= 0 ? argv[i + 1] : d; };
const UI_TAG = opt('ui', 'after');
const UI = 'v02';  // 界面坐标 / 判读逻辑沿用 V0.2
const VP = opt('viewport', 'desktop');
const URL = opt('url', 'http://127.0.0.1:8002/index.html');
const OUT = path.resolve(opt('out', 'shots'));
fs.mkdirSync(OUT, { recursive: true });

const MOBILE = VP.startsWith('mobile');
const MOBILE_SIZES = { mobile: [844, 390], mobile932: [932, 430], mobile667: [667, 375] };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const IPHONE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';
const ctxOpts = MOBILE
  ? { viewport: { width: MOBILE_SIZES[VP][0], height: MOBILE_SIZES[VP][1] }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, userAgent: IPHONE_UA }
  : { viewport: { width: 1280, height: 720 } };

// 各版本界面里的点击坐标（游戏逻辑坐标 1280x720）
const UIS = {
  v01: { start: [96, 277], load: [96, 319], choiceX: 640, choiceY: [366, 422, 480], quickSave: [662, 710], slot1: [503, 280], advance: [640, 120] },
  v02: { start: [140, 282], load: [140, 350], choiceX: 640, choiceY: [125, 237, 345], quickSave: [864, 528], quickSaveTouch: [1083, 530], slot1: [549, 294], advance: [640, 20] },
};
const U = UIS[UI];

const results = [];
const record = (name, ok, detail) => { results.push({ name, ok, detail }); console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? ' — ' + detail : ''}`); };

function launch() {
  return chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/local/bin/google-chrome', args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader'] });
}

async function open(browser, ctx = null) {
  ctx = ctx || await browser.newContext(ctxOpts);
  const page = await ctx.newPage();
  const logs = [];
  page.on('console', m => { const t = m.text(); if (!/GL Driver Message/.test(t)) logs.push(`${m.type()}: ${t.slice(0, 300)}`); });
  page.on('pageerror', e => logs.push('pageerror: ' + e.message.slice(0, 300)));
  page.on('requestfailed', r => logs.push('requestfailed: ' + r.url()));
  page.on('response', r => { if (r.status() >= 400) logs.push(`http ${r.status()}: ${r.url()}`); });
  return { ctx, page, logs };
}
const errorCount = logs => logs.filter(l => /pageerror|requestfailed|^http [45]|^error/i.test(l)).length;

const grab = async page => PNG.sync.read(await page.screenshot());
const savePng = (img, name) => fs.writeFileSync(path.join(OUT, `${UI_TAG}-${VP}-${name}.png`), PNG.sync.write(img));

function geo(page, img) {
  const vp = page.viewportSize();
  const scale = Math.min(vp.width / 1280, vp.height / 720);
  const ox = (vp.width - 1280 * scale) / 2, oy = (vp.height - 720 * scale) / 2;
  const k = img ? img.width / vp.width : 1;
  return { scale, ox, oy, k, px: gx => Math.round((ox + gx * scale) * k), py: gy => Math.round((oy + gy * scale) * k) };
}
async function tap(page, gx, gy) {
  const g = geo(page);
  const x = g.ox + gx * g.scale, y = g.oy + gy * g.scale;
  if (MOBILE) await page.touchscreen.tap(x, y); else await page.mouse.click(x, y);
}
async function advance(page) {
  if (MOBILE) await tap(page, ...U.advance); else await page.keyboard.press('Enter');
}

// 游戏坐标区域内的像素差异数（容差为 RGB 差值之和）
function regionDiff(a, b, page, [x0, y0, x1, y1], tol = 24) {
  if (a.width !== b.width || a.height !== b.height) return Infinity;
  const g = geo(page, a);
  let n = 0;
  for (let y = g.py(y0); y < g.py(y1); y++) for (let x = g.px(x0); x < g.px(x1); x++) {
    const i = (y * a.width + x) * 4;
    if (Math.abs(a.data[i] - b.data[i]) + Math.abs(a.data[i + 1] - b.data[i + 1]) + Math.abs(a.data[i + 2] - b.data[i + 2]) > tol) n++;
  }
  return n;
}
const FULL = [0, 0, 1280, 720];
// V0.5：立绘呼吸、灯光呼吸会让两侧与灯下像素持续微动，所以停住判读只看对话框中间一段（避开立绘）
const TEXT_REGION = [420, 560, 860, 700];
function countNear(img, page, rect, rgb, dist = 36) {
  const g = geo(page, img);
  let n = 0;
  for (let y = g.py(rect[1]); y < g.py(rect[3]); y++) for (let x = g.px(rect[0]); x < g.px(rect[2]); x++) {
    const i = (y * img.width + x) * 4;
    if (Math.abs(img.data[i] - rgb[0]) + Math.abs(img.data[i + 1] - rgb[1]) + Math.abs(img.data[i + 2] - rgb[2]) < dist) n++;
  }
  return n;
}
// V0.2 结局卡片：用标题字色识别（结局一金 / 结局二冷白 / 结局三冷青灰）
const TINTS = { 1: [246, 213, 142], 2: [216, 236, 238], 3: [143, 182, 196] };
function cardNumber(img, page) {
  const rect = [330, 150, 950, 300];
  let best = null, bestN = 0;
  for (const [n, rgb] of Object.entries(TINTS)) {
    const c = countNear(img, page, rect, rgb, 20);
    if (c > bestN) { bestN = c; best = Number(n); }
  }
  const minPx = 600 * geo(page, img).scale * geo(page, img).k * geo(page, img).scale * geo(page, img).k;
  return bestN > minPx ? best : null;
}
function isMainMenu(img, page) {
  if (UI === 'v01') {
    const g = geo(page, img);
    const px = (gx, gy) => { const i = (g.py(gy) * img.width + g.px(gx)) * 4; return [img.data[i], img.data[i + 1], img.data[i + 2]]; };
    return px(100, 100).every(v => v < 40) && px(100, 600).every(v => v < 40);
  }
  return countNear(img, page, [40, 60, 520, 160], [246, 213, 142], 30) > 400 * Math.pow(geo(page, img).scale * geo(page, img).k, 2);
}

// 加载阶段取帧：页面 presplash 阶段 / 游戏内 splash 阶段（V0.5 才有）。返回 {presplash, splash, info}
// 主菜单有持续的光束 / 雾漂移动画，相邻 1 秒的帧约有 3%（≈3 万像素 @1280x720）不同；超过 ~9% 才算“还在转场”
const STABLE_PX = 80000;
const SPLASH_RECT = [380, 150, 900, 330];   // 游戏坐标：splash 标题“雾港来信”所在区域（金色字）
async function waitMainMenu(page, timeoutMs = 300000, loadingCapture = false) {
  const t0 = Date.now();
  let prev = await grab(page), stable = 0;
  const cap = { presplash: null, splash: null, info: null };
  while (Date.now() - t0 < timeoutMs) {
    await sleep(loadingCapture ? 400 : 1000);
    const cur = await grab(page);
    if (loadingCapture) {
      const dom = await page.evaluate(() => {
        const el = document.getElementById('presplash');
        if (!el) return null;
        const cs = getComputedStyle(el);
        return { src: el.getAttribute('src'), display: cs.display, naturalWidth: el.naturalWidth, naturalHeight: el.naturalHeight, complete: el.complete };
      });
      if (dom && dom.display !== 'none' && dom.complete && !cap.presplash) { cap.presplash = cur; cap.info = dom; }
      const gold = countNear(cur, page, SPLASH_RECT, [246, 214, 144], 40);
      const preVisible = dom && dom.display !== 'none';
      if (!preVisible && gold > 3000 * Math.pow(geo(page, cur).scale * geo(page, cur).k, 2) && !cap.splash) cap.splash = cur;
    }
    stable = regionDiff(prev, cur, page, FULL) < STABLE_PX * Math.pow(geo(page, cur).k, 2) ? stable + 1 : 0;
    prev = cur;
    if (isMainMenu(cur, page) && stable >= 2) { cap.sec = (Date.now() - t0) / 1000; return loadingCapture ? cap : cap.sec; }
  }
  throw new Error('等待主菜单超时');
}

// 推进剧情，直到画面停住（选项菜单 / V0.2 结局卡片 / 回到主菜单）。返回所有帧。
async function advanceUntilStuck(page, { maxSteps = 90, stopOnCard = false, stepMs = 1300 } = {}) {
  const region = UI === 'v01' ? FULL : TEXT_REGION;
  const thresh = UI === 'v01' ? 200 : 60;
  const frames = [await grab(page)];
  let same = 0;
  for (let i = 0; i < maxSteps; i++) {
    await advance(page);
    await sleep(stepMs);
    const cur = await grab(page);
    frames.push(cur);
    if (stopOnCard && UI === 'v02' && cardNumber(cur, page)) { frames.card = true; return frames; }
    same = regionDiff(frames[frames.length - 2], cur, page, region) < thresh ? same + 1 : 0;
    if (same >= 2) return frames;
  }
  throw new Error('推进剧情超过最大步数仍未停下');
}

async function pickChoice(page, idx) {
  await tap(page, U.choiceX, U.choiceY[idx]);
  await sleep(1600);
}

async function playBranch(browser, tag, picks, expected, extra) {
  const { page, logs } = await open(browser);
  await page.goto(URL);
  let loadSec;
  if (extra) {
    const cap = await waitMainMenu(page, 300000, true);
    loadSec = cap.sec;
    if (cap.presplash) savePng(cap.presplash, '00-loading-presplash');
    if (cap.splash) savePng(cap.splash, '00b-loading-splash');
    record(`${UI_TAG}/${VP} 加载画面`, !!cap.presplash,
      `页面 presplash：${JSON.stringify(cap.info)}；捕捉到页面 presplash 帧=${!!cap.presplash}；捕捉到游戏内 splash 帧=${!!cap.splash}（before 构建没有 splash，期望 false）`);
  } else {
    loadSec = await waitMainMenu(page);
  }
  const main = await grab(page);
  if (extra) savePng(main, '01-main-menu');
  await tap(page, ...U.start);
  await sleep(4500);
  for (let m = 0; m < 3; m++) {
    const frames = await advanceUntilStuck(page, { stepMs: extra && m === 0 ? 2300 : 1300 });
    let idxFirst = frames.length - 1;
    while (idxFirst > 0 && regionDiff(frames[idxFirst - 1], frames[idxFirst], page, TEXT_REGION) < 60) idxFirst--;
    if (extra) {
      savePng(frames[Math.max(0, idxFirst - 2)], `02-dialogue-${m + 1}`);
      savePng(frames[frames.length - 1], `03-choice-${m + 1}`);
    }
    await pickChoice(page, picks[m]);
  }
  const frames = await advanceUntilStuck(page, { stopOnCard: true, maxSteps: 120 });
  await sleep(2500);
  const card = await grab(page);
  const ending = cardNumber(card, page);
  savePng(frames[Math.max(0, frames.length - 3)], `04-ending-${expected}-dialogue`);
  savePng(card, `05-ending-${expected}-card`);
  await tap(page, 640, 648);
  await sleep(3500);
  const backAtMenu = isMainMenu(await grab(page), page);
  const ok = ending === expected && backAtMenu && errorCount(logs) === 0;
  record(`${UI_TAG}/${VP} 分支 ${tag}（选项 ${picks.map(p => p + 1).join('/')}）`, ok,
    `到达结局卡片=${ending}（期望 ${expected}）；回到主菜单=${backAtMenu}；页面错误/失败请求=${errorCount(logs)}；首次到主菜单 ${loadSec.toFixed(1)}s`);
  await page.close();
}

async function compare(browser) {
  const only = opt('only', 'A,B,C').split(',');
  if (only.includes('A')) await playBranch(browser, 'A_true', [0, 0, 0], 1, true);
  if (only.includes('B')) await playBranch(browser, 'B_half', [1, 1, 1], 2, false);
  if (only.includes('C')) await playBranch(browser, 'C_miss', [2, 2, 2], 3, false);
}

async function saveload(browser) {
  const ctx = await browser.newContext(ctxOpts);
  let { page, logs } = await open(browser, ctx);
  await page.goto(URL);
  await waitMainMenu(page);
  await tap(page, ...U.start); await sleep(4500);
  await advanceUntilStuck(page); await pickChoice(page, 0);
  await advanceUntilStuck(page);
  await tap(page, ...(MOBILE && U.quickSaveTouch ? U.quickSaveTouch : U.quickSave)); await sleep(2200);
  savePng(await grab(page), 'save-1-screen');
  await tap(page, ...U.slot1); await sleep(2200);
  savePng(await grab(page), 'save-2-slot1-saved');
  await page.close();

  ({ page, logs } = await open(browser, ctx));
  await page.goto(URL);
  await waitMainMenu(page);
  await tap(page, ...U.load); await sleep(2500);
  savePng(await grab(page), 'save-3-load-screen-after-reload');
  await tap(page, ...U.slot1); await sleep(3500);
  savePng(await grab(page), 'save-4-after-load');
  await pickChoice(page, 1);
  await advanceUntilStuck(page); await pickChoice(page, 1);
  const frames = await advanceUntilStuck(page, { stopOnCard: true, maxSteps: 120 });
  await sleep(2500);
  const card = await grab(page);
  const ending = UI === 'v02' ? cardNumber(card, page) : null;
  savePng(card, 'save-5-ending-after-load');
  record(`${UI_TAG}/${VP} 存档 -> 刷新页面 -> 读档 -> 按 +0/+0 通关`, ending === 2 && errorCount(logs) === 0,
    `读档后到达结局=${ending}（期望 2；信任度未恢复则会是 3）；页面错误/失败请求=${errorCount(logs)}`);
  await page.close();
}

(async () => {
  const browser = await launch();
  try {
    if (cmd === 'compare') await compare(browser);
    else if (cmd === 'saveload') await saveload(browser);
    else throw new Error('未知子命令 ' + cmd);
  } catch (e) {
    record('脚本异常', false, e.message);
  } finally {
    await browser.close();
  }
  fs.writeFileSync(path.join(OUT, `${cmd}-${UI_TAG}-${VP}.json`), JSON.stringify({ ui: UI_TAG, viewport: VP, url: URL, results }, null, 2));
  process.exit(results.every(r => r.ok) ? 0 : 1);
})();
