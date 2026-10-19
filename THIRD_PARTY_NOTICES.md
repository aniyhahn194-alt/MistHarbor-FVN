# 第三方内容与许可来源

本项目 **V0.5** 中**非自制**的内容如下。其余（剧本、背景、立绘、加载 / 标题画面、全部界面图片、特效层）均为本项目原创：立绘原图由 `tools/generate_assets.py`、背景 / 立绘后期 / 加载画面由 `tools/generate_v05_art.py`、界面图片由 `tools/generate_ui.py` 用 Pillow 以代码绘制，没有使用任何外部图片素材，**也没有使用任何 AI 图像生成工具**（本环境未提供）。

| 内容 | 位置 | 来源 | 许可 |
| --- | --- | --- | --- |
| 界面代码结构：`gui.rpy`、`screens.rpy`（Screen 定义、style 命名与布局骨架） | `game/` | Ren'Py SDK（8.3.7）官方 GUI 模板 / 示例项目 `the_question`。V0.2 已大幅改写：配色、尺寸、主菜单、对话框、选项、快捷菜单、存档页、设置页、结局卡片等均为本项目重写，但仍保留模板的屏幕与样式骨架 | 按 Ren'Py 总许可归类为 MIT（见 SDK 的 `LICENSE.txt`）。**说明**：`LICENSE.txt` 没有对 GUI 模板单独声明许可，本条沿用 V0.1 的归类，未另行核对 |
| 简体中文界面翻译 | `game/tl/schinese/common.rpy`、`screens.rpy` | Ren'Py SDK `launcher/game/tl/schinese/` | 同上（MIT） |
| 思源黑体 Lite（Source Han Sans Lite for RenPy） | `game/fonts/SourceHanSansLite.ttf`，许可正文见 `game/fonts/OFL.txt` | Ren'Py SDK `sdk-fonts/`；字体版权 © 2014-2019 Adobe，Reserved Font Name 'Source' | SIL Open Font License 1.1（依据字体文件 name 表记载） |

## V0.2-P1 的素材核对记录

- **界面图片已全部替换为原创**：V0.1 中取自官方模板的按钮、滑条、滚动条、框、遮罩等 `game/gui/` 图片（模板生成的纯色 / 渐变图）在 V0.2 中已全部由 `tools/generate_ui.py` 重新绘制并覆盖，不再使用模板图片。仅 `game/gui/window_icon.png`（V0.1 自制的窗口图标）保持不变。
- **字体**：仅使用思源黑体 Lite（OFL 1.1）。V0.2 没有新增字体；标题 / 结局名同样由该字体在游戏内实时渲染，没有把字体栅格化进图片。OFL 允许随游戏分发与内嵌，`OFL.txt` 已随包提供。
- **未使用**任何网络抓取的图片、字体、音频或第三方插画。
- **已移除错误署名**：V0.1 的“关于”页残留了官方示例 `the_question` 的演职员署名（与本项目无关），V0.2 已改为本项目的真实来源说明。
- 开发期工具依赖：Pillow（仅 `tools/`，HPND 许可，不随游戏分发）；Playwright（`tools/web_test/`，Apache-2.0，不随游戏分发）。

## V0.5 的素材核对记录

- **来源**：新增 / 改动的 `game/images/bg_*.png`、`game/images/huizhou_*.png`、`game/images/linlan_*.png`、`web-presplash.png`、`game/presplash.png`、`game/gui/splash.png`、`game/gui/main_menu.png`、`game/gui/game_menu.png`、`game/gui/textbox.png`、`game/gui/namebox.png`、`game/gui/button/{choice,quick}_*_background.png` 全部由本仓库 `tools/` 下的 Python + Pillow 脚本以代码生成。**授权状况**：作者原创的程序化图形，随项目一起发布，无第三方权利人。它们是程序化占位美术，**不是**专业手绘作品。
- **字体**：没有新增字体。加载 / 标题画面（`web-presplash.png`、`game/presplash.png`、`game/gui/splash.png`）里的标题文字用已有的思源黑体 Lite（SIL OFL 1.1）**渲染成了图片**。OFL 1.1 允许在作品（含图像）中使用字体渲染的文字并随作品分发，`OFL.txt` 仍随包提供；没有修改或再分发字体文件本身。
- **未使用**任何网络抓取的图片、字体、音频或第三方插画；没有使用图像生成模型。
- **Web 构建产物**：包含 Ren'Py 官方 Web 运行时（`renpy.wasm` 等，来自官方 `renpy-8.3.7-web.zip`）；`tools/verify_web_build.py` 向 `index.html` 注入的只是一小段自写 CSS（加载状态条外观）。

## 说明

- 已从模板中移除 `the_question` 示例自带的背景与人物插画、头像（它们的版权人为第三方），仓库中不包含这些文件。
- Ren'Py 引擎本身不随仓库分发；运行时使用者需自行下载 Ren'Py SDK，其中包含的第三方组件各有许可，见 SDK 的 `LICENSE.txt`。Web / Windows 构建产物会包含引擎运行时。
- 如后续替换为正式美术或添加音乐，需在此文件补充来源与许可（要求见 `docs/ART_BRIEF.md` 的“授权要求”）。
