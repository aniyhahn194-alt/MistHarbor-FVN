# Web 版（手机浏览器）构建、测试与部署说明

适用版本：V0.1.0，Ren'Py **8.3.7**。目标：让项目所有者只用手机浏览器就能试玩。

> **先说结论（如实）**
> - 官方 Web 构建**已成功**，得到真正的 HTML5 / WebAssembly 版本（不是另写的网页）。
> - 已在**桌面 Google Chrome 154（Playwright 驱动）**里做了真实浏览器测试：加载、三条分支、存读档、手机视口 + 触控模拟。
> - **没有**在真实手机、**没有**在 iOS Safari / Android Chrome 上测过。下文所有“手机”结论中，凡标“模拟”的只是桌面 Chromium 的视口/触控/UA 模拟。
> - **目前没有公开的在线试玩链接**。GitHub Pages 未启用，也没有触发任何公开部署；需要所有者批准（见第 5 节）。

---

## 1. 官方 Web 构建支持检查

| 检查项 | 结果 |
| --- | --- |
| SDK | 从 renpy.org 下载 `renpy-8.3.7-sdk.tar.bz2`，MD5 与官方 `checksums.txt` 一致 |
| Web 组件 | 官方 `renpy-8.3.7-web.zip`（12.8 MB），MD5 `d4ceaacf857e3a6b086ad7c97709635e` 与官方 `checksums.txt` 一致；解压到 `<SDK>/web/` 即安装（Launcher 里点 “Build Web Application” 时也会这样提示并下载） |
| 构建命令 | `renpy.sh <SDK>/launcher web_build <项目> --destination <目录>`（`launcher/game/web.rpy` 中注册的命令行入口，与 Launcher 按钮同一实现） |
| 项目需改动？ | **不需要改动游戏代码**。首次构建自动在项目根生成 `progressive_download.txt`（已提交）；`tests.rpy` 已在 `options.rpy` 中被 `build.classify` 排除 |

构建脚本：[`tools/build_web.sh`](../tools/build_web.sh)

```bash
# 已有 SDK 且已安装 web 组件：
tools/build_web.sh ~/renpy-8.3.7-sdk dists/web
# 缺 web 组件时让脚本从官方地址下载：
RENPY_WEB_AUTO_INSTALL=1 tools/build_web.sh ~/renpy-8.3.7-sdk dists/web
```

实际构建输出（节选）：

```
Scanning Ren'Py files...
Writing the web zip package. - 631 of 631
All packages have been built.
Preparing progressive download
Creating package... - 37 of 37
f0a7ddaab142c5b8761bfd3f364d642f483213dffe6366efbcb146f1dd937096  MistHarbor-FVN-web.zip
46M  .../MistHarbor-FVN-web      46M  .../MistHarbor-FVN-web.zip      （构建耗时约 4 秒）
```

产物结构：

| 文件 | 大小（字节） | 说明 |
| --- | --- | --- |
| `renpy.wasm` | 19,503,634 | Ren'Py 引擎（官方 Web 组件，固定） |
| `renpy.data` | 16,370,126 | 引擎 Python 标准库等（官方 Web 组件，固定） |
| `game.zip` | 约 7.4 MB | 游戏脚本、GUI 图片、字体（思源黑体 Lite 约 2.9 MB）等 |
| `game/images/*.png` | 7 个文件共约 0.94 MB | 背景与立绘，**按需下载**（progressive download） |
| `renpy.js`、`index.html`、`service-worker.js`、`manifest.json`、`icons/` 等 | 小文件 | 页面与 PWA 外壳 |

引擎部分（约 36 MB 原始、gzip 后约 11 MB）与游戏内容无关，是首次加载体积的主要来源。

**构建产物位置（未提交 git）：** Project store `docs/releases/web/MistHarbor-0.1.0-web.zip`
（`/cursor/stores/bc-01a14f91-ad3e-709c-8bda-f85e68c2fd63/docs/releases/web/`），
SHA256 `f0a7ddaab142c5b8761bfd3f364d642f483213dffe6366efbcb146f1dd937096`（同目录 `SHA256SUMS.txt`）。
这是 `tools/build_web.sh` 的原样输出（文件名改为 `MistHarbor-0.1.0-web.zip`）。该 zip 解压后即可交给任何静态托管。

---

## 2. 浏览器测试（真实输出）

环境：Linux 云端 VM；Google Chrome 154.0.8037.92（headless，软件 WebGL / SwiftShader）；Playwright（`playwright-core`）；
本地静态服务器 `tools/web_test/serve.js`。脚本：[`tools/web_test/web_playtest.js`](../tools/web_test/web_playtest.js)。

> **再次强调：这是桌面 Chromium。** 手机视口 / 触控 / iPhone UA 都是模拟，浏览器引擎仍是 Chromium（Blink），
> **不是 iOS Safari（WebKit）**，也不是 Android 真机。**不得据此声称通过了 iOS Safari 测试。**

运行方法：

```bash
cd tools/web_test && npm install
node serve.js <构建产物目录> 8000 &          # 或用任意静态服务器
node web_playtest.js all --url http://127.0.0.1:8000/index.html --out ../../docs/web/screenshots
node web_playtest.js probe --url http://127.0.0.1:8000/index.html
```

### 2.1 实际结果（对 `MistHarbor-0.1.0-web.zip` 同一份构建输出）

控制台汇总（原样，见 [`docs/web/test-results/console-summary.txt`](web/test-results/console-summary.txt)）：

```
PASS  分支 A_true（选项 1/1/1） — 到达结局卡片=1（期望 1，参考图完整=true）；回到主菜单=true；页面错误/失败请求=0；首次到主菜单 8.4s
PASS  分支 B_half（选项 2/2/2） — 到达结局卡片=2（期望 2，参考图完整=true）；回到主菜单=true；页面错误/失败请求=0；首次到主菜单 8.0s
PASS  分支 C_miss（选项 3/3/3） — 到达结局卡片=3（期望 3，参考图完整=true）；回到主菜单=true；页面错误/失败请求=0；首次到主菜单 8.2s
PASS  存档 → 刷新页面 → 读档（存档跨页面重载保留，且变量恢复） — 读档后按 +0/+0 通关到达结局卡片=2 ...
PASS  全新浏览器上下文看不到已有存档（存档按浏览器/站点隔离） ...
PASS  手机视口模拟（landscape 844x390，触控，iPhone UA；桌面 Chromium） — 主菜单 7.4s；触控点按开始游戏/推进/选项=true；页面错误=0
PASS  手机视口模拟（portrait 390x844，触控，iPhone UA；桌面 Chromium） — 主菜单 7.9s；触控点按开始游戏/推进/选项=true；页面错误=0
PASS  网络请求清单与内存占用 — 按需图片请求 7 个；总请求 15 个；内存(主菜单) {"jsHeapUsedMiB":4.9,"wasmMemoryMiB":192}；内存(灯塔选项) {"jsHeapUsedMiB":5.6,"wasmMemoryMiB":192}
```

| 测试项 | 方法 | 结果 | 证据 |
| --- | --- | --- | --- |
| 启动与主菜单 | 打开 `index.html`，等待画面稳定 | 通过：本地约 7–8 秒到主菜单；控制台依次出现 `Downloading engine…` → `Running…` → `Unpacking…` → `Loading script…` | `01_main_menu.png` |
| 背景 | 三条路径经过栈桥 / 后巷 / 灯塔 | 通过，3 张背景均显示 | `03/04/05_choice*.png` |
| 角色立绘 | 灰舟（平静/忧虑）、林岚（平静/微笑） | 通过，4 张立绘均显示，滑入动画正常 | `03_choice1_dock.png` 等 |
| 中文字体 | 主菜单、对话、选项、结局卡片、存档页 | 通过：无方块字；字体来自游戏包内的思源黑体 Lite（`game/fonts`），**不依赖设备系统字体** | 全部截图 |
| 图片按需下载 | `probe` 记录网络请求 | 通过：7 张图片均以独立请求下载（`game/images/*.png`，合计约 0.94 MB），其余在 `game.zip` | `test-results/probe.json` |
| 分支一 / 二 / 三 | 键盘回车推进、鼠标点选项；与结局卡片参考图（`docs/web/screenshots/ref/`）逐像素比对 | 全部通过：分别到达“结局一：灯塔回信 / 结局二：半盏灯火 / 结局三：雾中错过”并回到主菜单；页面错误与失败请求均为 0 | `06/07/08_ending*_card.png`、`09_back_to_main_menu_after_ending.png` |
| 存档 | 后巷选项处点底部“保存” → 点槽位 1 | 通过：槽位出现缩略图与时间戳 | `20_save_03_slot1_saved.png` |
| 重新加载页面后读档 | 同一浏览器上下文重新打开页面 → “读取游戏” → 槽位 1 | 通过：存档仍在（IndexedDB 持久化），读档回到后巷选项；之后按 +0/+0 通关到结局二 = 信任度 2 被恢复（变量丢失会是结局三） | `20_save_04…`、`20_save_05…`、`20_save_08…` |
| 存档隔离 | 全新浏览器上下文打开读档页 | 通过：全为“空存档位”（存档按浏览器/站点保存，不会跨设备同步） | `20_save_06…` |
| 页面内置菜单 | 点左上 ≡ | 出现 Import Saves / Export Saves / Download Log（Ren'Py 官方 Web 页面自带，**仅看到菜单，未实际导入/导出**） | `20_save_07…` |
| 手机横屏模拟 | 844×390、DPR 2、触控、iPhone UA、`isMobile` | 通过：触控点按“开始游戏”、推进、点选项均有效；Ren'Py 识别为移动端（主菜单不再显示“帮助”） | `30_mobile_landscape_*.png` |
| 手机竖屏模拟 | 390×844 同上 | 功能可用，但**画面仅占屏幕宽度一小条（约 390×219），文字几乎无法阅读**；必须横屏游玩 | `30_mobile_portrait_*.png` |

### 2.2 首次加载体积与限速（仅为 Chromium DevTools 限速模拟）

禁用缓存、禁用 service worker（它的请求不受页面级限速影响）；`Fast 4G ≈ 9 Mbps / 40 ms`，`Slow 4G ≈ 1.6 Mbps / 150 ms`。
“到主菜单”包含脚本内 ~2 秒画面稳定判定。结果见 `docs/web/test-results/loadtime-*.json`。

| 服务器压缩 | 传输量 | Fast 4G → 主菜单 | Slow 4G → 主菜单 |
| --- | --- | --- | --- |
| 无压缩（原始） | 43.3 / 42.8 MiB | 约 46 s | 约 222 s |
| gzip（`serve.js --gzip`，粗略模拟） | 19.7 / 19.2 MiB | 约 24 s | 约 104 s |

GitHub Pages 是否对 `.wasm` / `renpy.data` 做 gzip **未验证**，所以实际体积可能在两列之间。之后访问是否命中浏览器 / service worker 缓存**未验证**（Ren'Py 文档提示：超过 50 MB 的单文件不会缓存，本构建最大单文件 18.6 MiB，理论上可缓存）。

---

## 3. 兼容性与风险（区分已验证 / 推测）

**已验证（桌面 Chromium 中）**
- 能加载并运行完整 V0.1：背景、立绘、中文字体、三条分支、存读档（含刷新页面后读档）。
- 竖屏下画面只占一小条，无法正常阅读；横屏可用。
- 触控点按（Playwright `touchscreen.tap`）可操作主菜单、推进对话、选择选项。
- 浏览器内存：WebAssembly 内存 192 MiB，JS 堆约 5 MiB。
- 首次加载体积见 2.2。
- 画面按 1280×720 等比缩放；在 844×390 横屏视口下缩放比约 0.54：对话文字（`gui.text_size = 26`）约 14 CSS px，底部快捷菜单文字（`gui.quick_button_text_size = 14`）约 7–8 CSS px，点按目标偏小（由配置值与缩放比推算，手指实际是否好按**未验证**）。

**推测 / 官方文档说法（未在真机验证）**
- iOS Safari：一般要求 HTTPS 才能使用 service worker；WebKit 对单标签内存有较严格上限，192 MiB 的 WASM 内存加上引擎，低内存机型有被系统杀掉标签页的可能——**未测**。
- iOS Safari 存档：存档保存在 IndexedDB；Safari 的智能防跟踪（ITP）可能在站点长时间不交互后清理脚本可写存储，隐私浏览模式下存档也不稳定——**未测**。建议重要进度用 Ren'Py 页面左上 ≡ 里的 “Export Saves” 备份（该功能仅确认存在，未实测）。
- 音频：V0.1 **没有音频**，所以没有测。Ren'Py 官方文档说明浏览器要求用户先在页面里点击一次才会播放声音，且 Safari 的 WebAudio 不支持 OGG，后续加入音频时需用 mp3 或设置 `config.webaudio_required_types`。
- 首次加载：移动网络下 20–45 MB 下载较久（见 2.2）；加载期间是官方默认的预加载页面，没有自定义进度画面。可考虑放一张 `web-presplash.jpg`（目前使用官方默认）。
- 竖屏：`manifest.json` 声明 `orientation: landscape-primary`，但只有“添加到主屏幕”的 PWA 模式才会遵守；普通浏览器标签里需要手动横屏——**PWA 安装未测**。
- 字体：已确认走游戏包内字体，系统字体缺失不会影响；字体文件随 `game.zip` 一起下载（约 2.9 MB 未压缩）。
- 引擎本身：官方文档称 Web 版“尽力”支持 iOS / Android 的 Safari / Chrome，但可能随浏览器升级失效；无法保证。

---

## 4. 让手机能玩：现状与可选方案（评估）

**现状：没有任何公开链接。** 没有启用 GitHub Pages，没有部署到任何第三方站点。Project store 里的 zip 只是文件，手机不能直接“打开 zip 玩”，必须先托管到某个 https 网址。

| 方案 | 说明 | 优点 | 缺点 / 需要用户做的事 |
| --- | --- | --- | --- |
| A. GitHub Pages（仓库已是 **public**） | 用本仓库的 `web-build-pages.yml`，在 Actions 手动运行并选择 `publish=yes` | 免费、HTTPS、与仓库同处 | 站点**完全公开**；需所有者在 Settings → Pages 选 Source = GitHub Actions；`github-pages` 环境默认只允许默认分支（main）部署，所以需要先合并本 PR 与原型 PR，或在 Settings → Environments 放宽分支规则；是否 gzip 未验证。预期网址形如 `https://aniyhahn194-alt.github.io/MistHarbor-FVN/`（**尚不存在**） |
| B. itch.io（HTML5 项目，可设为“仅链接 / 受限”） | 上传 `MistHarbor-0.1.0-web.zip` | Ren'Py 官方文档提到的常见托管方式；可设为不公开列出 | 需要所有者注册 itch.io 账号并手动上传；iframe 内嵌，全屏/存档行为需实测 |
| C. 其他静态托管（Cloudflare Pages / Netlify 等） | 上传解压目录或 zip | 通常默认 gzip/brotli，国内外访问速度各异 | 需所有者账号；同样会产生公开网址（可设密码/访问控制视平台而定） |
| D. 本地网络预览 | 电脑上 `node tools/web_test/serve.js` + 手机同一 Wi-Fi 访问 | 不公开 | 需要一台电脑，**所有者目前只有手机，不可行** |

推荐顺序：先由所有者决定是否接受“公开网址”。若接受 → 方案 A（本仓库已备好配置）；若不想公开 → 方案 B 或 C 的受限访问。

---

## 5. 需要用户批准的部署步骤（本 PR 均**未执行**）

本 PR 只添加了 `.github/workflows/web-build-pages.yml`。该 workflow：
- 只有 `workflow_dispatch`（手动触发），**没有** push / PR 触发；合并后也不会自动运行。
- 默认 `publish=no`：只构建并上传 14 天保留的**私有 Artifact**（`MistHarbor-FVN-web.zip` + SHA256），不发布。
- 构建时校验官方 SDK / web 组件的 MD5（来自官方 `checksums.txt`）。
- 此 workflow 本身**尚未在 GitHub Actions 上运行过**（只验证了 YAML 语法与其中调用的 `tools/build_web.sh` 命令）。

若决定发布到 GitHub Pages，需要所有者依次确认：
1. 同意站点公开（任何人拿到链接都能玩；源码仓库本身已是公开的）。
2. 合并本 PR（及其基础分支 `cursor/v0-1-prototype-1d4f` / PR #1，或把 workflow 文件放进 main）——因为 `workflow_dispatch` 与 `github-pages` 环境默认限制在默认分支。
3. 仓库 Settings → Pages → Build and deployment → Source 选 **GitHub Actions**。
4. Actions → `web-build-pages` → Run workflow，`publish` 选 `yes`。
5. 部署完成后在 Actions 日志里取得真实网址，再用手机横屏打开试玩，并按第 6 节清单反馈。

---

## 6. 手机试玩清单（待真机验证）

请在 **横屏** 下用手机浏览器（Safari / Chrome）打开试玩链接：
- [ ] 首次加载能到主菜单（记录用时、网络类型、手机型号 / 系统 / 浏览器版本）
- [ ] 中文无方块、背景与立绘正常
- [ ] 轻点屏幕推进对话；选项可点中（尤其底部小菜单是否好按）
- [ ] 三条分支都能到结局并回主菜单
- [ ] 保存 → 关闭标签页 → 重新打开 → 读档，进度是否还在
- [ ] 切到后台再回来是否仍正常（iOS 可能杀掉标签页）
- [ ] 竖屏时是否能接受（预期画面很小）
