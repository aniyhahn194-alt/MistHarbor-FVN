## options.rpy —— 《雾港来信》基础配置
## 以 Ren'Py 8.x 标准项目模板（the_question 示例）为基础精简而来。
## 以两个 '#' 开头的行是说明性注释。

## 基本信息 ####################################################################

## 游戏名称（窗口标题、主菜单、错误报告中使用）
define config.name = _("雾港来信")

## 是否在主菜单显示游戏名称
define gui.show_name = True

## 版本号
define config.version = "0.1.0"

## “关于”界面的文字，段落之间用 \n\n 分隔
define gui.about = _("""《雾港来信》（Letters from Mist Harbor）V0.1 原型。\n
原创拟人化（Furry）视觉小说。剧情、角色立绘与背景占位图均为原创，
由脚本绘制（见 tools/generate_assets.py）。\n
引擎：Ren'Py。界面模板来自 Ren'Py 官方示例项目；字体：思源黑体（SIL OFL 1.1）。""")

## 打包时使用的短名称：只能是 ASCII，不含空格、冒号、分号
define build.name = "MistHarbor"

## 音频 ########################################################################
## V0.1 暂无音频资源，后续版本可在此加入 config.main_menu_music 等设置。

define config.has_sound = True
define config.has_music = True
define config.has_voice = False

## 语言 ########################################################################
## 默认使用简体中文界面（翻译文件位于 game/tl/schinese/）。

define config.default_language = "schinese"

## 转场 ########################################################################

## 进入 / 退出游戏菜单
define config.enter_transition = dissolve
define config.exit_transition = dissolve

## 读档之后
define config.after_load_transition = None

## 游戏结束回到主菜单时
define config.end_game_transition = fade

## 对话窗口 ####################################################################

## "auto"：scene 语句前隐藏对话框，下一句对话时重新显示
define config.window = "auto"

define config.window_show_transition = Dissolve(.2)
define config.window_hide_transition = Dissolve(.2)

## 偏好默认值 ##################################################################

## 文字速度（每秒字符数，0 为瞬间显示）。设为 40 方便体验打字效果。
default preferences.text_cps = 40

## 自动前进等待时间（0~30）
default preferences.afm_time = 15

## 存档目录 ####################################################################
## 必须是字面量字符串。
define config.save_directory = "MistHarbor-FVN-0.1"

## 图标 ########################################################################
define config.window_icon = "gui/window_icon.png"

## 打包配置 ####################################################################

init python:

    ## 以下文件不放进发行包
    build.classify('**~', None)
    build.classify('**.bak', None)
    build.classify('**/.**', None)
    build.classify('**/#**', None)
    build.classify('**/thumbs.db', None)

    build.documentation('*.html')
    build.documentation('*.txt')
