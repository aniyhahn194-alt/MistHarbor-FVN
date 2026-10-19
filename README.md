# 雾港来信 / Letters from Mist Harbor

An original Furry visual novel built with Ren'Py and AI-assisted development.

> 当前版本：**V0.1 原型**（可从头玩到三个结局之一并回到主菜单）

## 项目介绍

雾气弥漫的港口城市“雾港”。年轻的狼族信使**灰舟**接到一封没有寄信人、收信人是“灯塔看守人”的神秘信件；
送信途中，他在栈桥遇到熟悉港口秘密的狐狸**林岚**。玩家通过三次选择决定是否信任她，并逐步揭开十年前“雾钟号”沉没事件背后被搁置的那封信。

- 原创剧情、原创角色、原创占位美术（见下文“素材说明”）
- 流程约 2000 字中文文本，预计一次游玩 3–5 分钟（按文字量估算，未做真人计时）
- 本仓库的目标是展示 Ren'Py 开发能力，后续版本将在 V0.1 的结构上继续迭代

## 技术栈

| 项目 | 说明 |
| --- | --- |
| 引擎 | Ren'Py 8.x（开发与验证使用 8.3.7） |
| 脚本 | Ren'Py Script（`.rpy`），少量 Python（信任度辅助函数） |
| 素材生成 | Python 3 + Pillow（仅 `tools/`，**不是**游戏运行依赖） |
| 界面 | Ren'Py 官方示例项目 `the_question` 的 GUI 模板（1280×720），自制主菜单/游戏菜单背景与窗口图标 |
| 字体 | 思源黑体 Lite（`SourceHanSansLite.ttf`，SIL OFL 1.1，取自 Ren'Py SDK 的 `sdk-fonts`） |
| 本地化 | 默认简体中文界面，`game/tl/schinese/` 来自 Ren'Py SDK 自带的官方中文翻译 |

## 游戏功能（V0.1）

1. 两位角色：灰舟（狼）、林岚（狐），均用 `Character` 定义并带颜色名牌
2. 三个不同背景：雾中栈桥、旧信使公会后巷、夜晚灯塔
3. 狼、狐立绘各有两种表情（灰舟：平静/忧虑；林岚：平静/微笑），可由 `hz worried "…"` 方式切换
4. 三次玩家选择（共 3 个 `menu`）
5. `default trust = 0` 初始化信任度；每个选项通过 `change_trust()` 增减，并弹出提示（不暴露具体数值）
6. 用 `if / elif / else` 与 `jump` 按信任度分流；另有 `refused_guide`、`seal_shown` 两个剧情标记影响对白
7. 三个结局（均有结局卡片并正常 `return` 回主菜单）：
   - 信任度 ≥ 4：**结局一 · 灯塔回信**
   - 信任度 1–3：**结局二 · 半盏灯火**
   - 信任度 ≤ 0：**结局三 · 雾中错过**
8. 转场与动画：`fade` / `dissolve` / 自定义 `Fade`；角色滑入用 ATL `transform`；灯塔点亮闪光
9. 信封预览用自定义 `screen letter_card`，可扩展为物品栏
10. 使用 Ren'Py 自带的存档/读档、回退、历史、快进、自动前进、设置、帮助等功能
11. 用 `persistent.endings_seen` 记录已达成结局，为以后的结局回顾界面预留

选项与信任度（初始 0，三次选择各自增减）：

| 选择 | 选项 | 信任度 |
| --- | --- | --- |
| 1 栈桥 | 请她带路 / 追问她为何帮忙 / 拒绝并独自去找路 | +2 / +1 / −2 |
| 2 后巷 | 让她看火漆印 / 只说收信人 / 拒绝给任何人看 | +2 / 0 / −2 |
| 3 灯塔 | 愿意交给收信人 / 先问收信人是谁 / 不交给没证明身份的人 | +2 / 0 / −2 |

## 运行方法

1. 从 [Ren'Py 官网](https://www.renpy.org/latest.html) 下载 Ren'Py 8.x SDK 并解压
2. 打开 Ren'Py Launcher，将本仓库的**上级目录**设为 Launcher 的项目目录（仓库根目录即项目目录，`game/` 位于其下），刷新后即可看到该项目
3. 在 Launcher 中选中“MistHarbor-FVN”，点击“启动项目”

命令行方式：

```bash
./renpy.sh /path/to/MistHarbor-FVN          # 运行游戏
./renpy.sh /path/to/MistHarbor-FVN lint     # 语法 / 引用检查
```

辅助脚本：

```bash
python3 tools/check_project.py              # 静态检查 label/jump/图片/变量（无需 SDK）
pip install pillow && python3 tools/generate_assets.py   # 重新生成占位素材
```

Ren'Py 内置自动化测试（需要图形环境，每条路径对应一个结局）：

```bash
./renpy.sh /path/to/MistHarbor-FVN test path_true
./renpy.sh /path/to/MistHarbor-FVN test path_half
./renpy.sh /path/to/MistHarbor-FVN test path_miss
```

## 目录结构

```
game/
  script.rpy        主剧本：角色、图像、变量、三幕剧情、三个结局
  options.rpy       基础配置（名称、版本、默认语言、转场、存档目录）
  gui.rpy           GUI 配置（字体、颜色、尺寸 1280x720）
  screens.rpy       界面（对话、菜单、存档、设置等，来自官方模板）
  tests.rpy         Ren'Py 自动化测试用例
  images/           游戏使用的背景与立绘（PNG）
  gui/              界面素材（主菜单/游戏菜单背景、图标为自制，按钮等为官方模板）
  fonts/            思源黑体 Lite
  tl/schinese/      Ren'Py 官方简体中文界面翻译
tools/
  generate_assets.py  用 Pillow 绘制占位素材（非运行依赖）
  check_project.py    静态检查脚本
docs/screenshots/     真实运行游戏时截取的截图
```

## 素材说明

- `game/images/` 下的背景与角色立绘、`game/gui/main_menu.png`、`game_menu.png`、`window_icon.png`
  全部由 `tools/generate_assets.py` 用 Pillow 绘制，原创、风格为简易占位图，后续会被正式美术替换。
- 界面按钮/滑条/文本框等基础图片、`screens.rpy`、`gui.rpy`、中文翻译文件来自 Ren'Py SDK 自带的官方项目模板
  （Ren'Py 以 MIT/LGPL 等许可发布），字体为 SIL OFL 1.1 的思源黑体。未使用来源不明的网络图片。
- V0.1 没有音乐与音效。

## 实际测试状态（如实记录）

测试环境：Linux 云端虚拟机，Ren'Py **8.3.7**（官方 SDK `renpy-8.3.7-sdk.tar.bz2`，从 renpy.org 下载），
软件渲染（Mesa llvmpipe），无声卡。

| 项目 | 结果 |
| --- | --- |
| `renpy.sh <项目> lint` | **已运行，通过**：无错误、无警告，仅输出统计与一条通用建议（建议开启 `config.check_conflicting_properties`）。统计：83 个对话块、3 个菜单、24 个界面 |
| `tools/check_project.py` 静态检查 | **已运行，通过**：9 个 label、7 个图像、2 个角色、4 个 default 变量 |
| 实际启动游戏 | **已运行**：游戏可在 Ren'Py 8.3.7 中启动并进入主菜单，截图见 `docs/screenshots/` |
| 自动化通关 | **已运行**：`path_true`、`path_half`、`path_miss` 三个 Ren'Py 测试用例分别走到三个结局（用 `assert` 校验信任度分别为 6 / 1 / −6），并回到主菜单后正常退出 |
| 真人试玩 | **未进行**：没有由人完整游玩并计时；3–5 分钟为按文字量的估算 |
| Ren'Py Launcher 图形界面导入 | **未验证**：只通过命令行 `renpy.sh` 运行；项目为标准结构（`game/`、`options.rpy`、`gui.rpy`、`screens.rpy`），理论上可导入 |
| Windows / macOS / Android 等平台、打包发行 | **未验证** |
| 声音 | **未验证**（V0.1 无音频，测试环境也无声卡） |

截图（均为真实运行游戏时用 `renpy.screenshot` 截取，1280×720）：

| 主菜单 | 后巷 |
| --- | --- |
| ![主菜单](docs/screenshots/01-main-menu.png) | ![后巷](docs/screenshots/02-alley.png) |

| 灯塔 | 结局一对白 |
| --- | --- |
| ![灯塔](docs/screenshots/03-lighthouse.png) | ![结局一](docs/screenshots/04-ending-true.png) |

选择界面截图 `docs/screenshots/05-choice-menu.png` 是在临时测试用的 label 中放置一份相同文字的菜单后截取，仅用于展示选项样式，该临时 label 未提交。

## 已知问题 / 限制

- 美术是代码绘制的简易占位图，立绘为静态、无口型与动作
- 选项菜单会盖住立绘上半部分（默认菜单布局），后续可自定义 `choice` 界面
- 界面（按钮、滑条等）沿用官方模板的默认橙色主题，仅调整了字体与部分颜色，尚未做统一视觉设计
- 无音乐、无音效；无 CG、无角色语音
- 结局回顾界面尚未实现（仅记录了 `persistent.endings_seen`）
- 开始游戏默认文字速度为每秒 40 字，可在“设置”里调整

## 版本计划

- **V0.1（当前）**：可玩原型，两位角色、三个场景、三次选择、三个结局
- **V0.2**：自定义选项/对话框界面，加入背景音乐与基础音效，立绘增加更多表情与站位动画
- **V0.3**：结局回顾与章节选择界面，信件物品栏 / 线索笔记，增加支线与更多分支
- **V0.4+**：替换为正式美术，完善 UI 视觉，打包发布（Windows / macOS / Linux），英文本地化

## AI 辅助开发说明

本项目由 AI Agent（Cursor Cloud Agent）参与生成，包括：剧情文本、`.rpy` 脚本、素材生成脚本、静态检查脚本和本 README。
上文“实际测试状态”中的测试均由该 AI Agent 在云端虚拟机的命令行/软件渲染环境中执行并如实记录；
**没有任何未经验证的运行或测试被声称为已完成**。项目所有者尚未对游戏进行人工完整试玩与评审，
故内容和代码质量需要人工复核后才能作为最终作品使用。
