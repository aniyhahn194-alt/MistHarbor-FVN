# 第三方内容与许可来源

本项目 V0.1 中**非自制**的内容全部来自 Ren'Py 官方 SDK（8.3.7，https://www.renpy.org/ ），具体如下。
自制内容（背景、立绘、主菜单/游戏菜单背景、窗口图标、剧情文本）由 `tools/generate_assets.py` 与 AI Agent 原创生成，见 README。

| 内容 | 位置 | 来源 | 许可 |
| --- | --- | --- | --- |
| 界面按钮、滑条、滚动条、文本框、对话框背景、半透明遮罩等基础 UI 图片 | `game/gui/`（除 `main_menu.png`、`game_menu.png`、`window_icon.png`） | Ren'Py SDK 官方示例项目 `the_question/game/gui/`（Ren'Py GUI 模板生成的通用纯色/渐变界面图，不含人物或场景插画） | Ren'Py 许可（MIT；见 SDK 的 `LICENSE.txt`） |
| `gui.rpy`、`screens.rpy` | `game/` | Ren'Py SDK 官方示例项目 `the_question`（Ren'Py 默认界面模板），本项目已修改字体、颜色、选项位置等 | 同上（MIT） |
| 简体中文界面翻译 | `game/tl/schinese/common.rpy`、`screens.rpy` | Ren'Py SDK `launcher/game/tl/schinese/` | 同上（MIT） |
| 思源黑体 Lite（Source Han Sans Lite for RenPy） | `game/fonts/SourceHanSansLite.ttf`，许可正文见 `game/fonts/OFL.txt` | Ren'Py SDK `sdk-fonts/`；字体版权 © 2014-2019 Adobe，Reserved Font Name 'Source' | SIL Open Font License 1.1（依据字体文件 name 表记载） |

说明：

- 已从模板中移除 `the_question` 示例自带的背景与人物插画、头像（它们的版权人为第三方），仓库中不包含这些文件。
- 未使用任何来源不明的网络图片或字体。
- Ren'Py 引擎本身不随仓库分发；运行时使用者需自行下载 Ren'Py SDK，其中包含的第三方组件各有许可，见 SDK 的 `LICENSE.txt`。
- 如后续替换为正式美术或添加音乐，需在此文件补充来源与许可。
