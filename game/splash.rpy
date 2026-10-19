## splash.rpy —— V0.5 启动画面（游戏内 splashscreen）
##
## 启动顺序：
##   1. 桌面：Ren'Py 在引擎初始化前显示 game/presplash.png（config.presplash 的自动查找约定）；
##      Web：浏览器页面先显示项目根目录的 web-presplash.png（Ren'Py 官方 Web 构建会把它复制进产物并写进 index.html）。
##   2. 引擎起来后进入本 splashscreen：同一幅标题画面（gui/splash.png）淡入 → 停留 → 淡出到主菜单。
##      所以从加载画面到主菜单是连续的，不会先闪一下 Ren'Py 默认画面或纯黑。
## 点击 / 触屏 / 按键 都可以立刻跳过。读档、重新开始、结局后返回主菜单都不会再次进入这里。

## 桌面端 presplash 至少保留 1.2 秒，避免一闪而过；Web 端由页面自己的加载进度决定，不额外等待。
define config.minimum_presplash_time = 0.0 if renpy.emscripten else 1.2

## splash 画面的淡入 / 淡出：由 ATL 控制标题的轻微上浮，整体用 dissolve 衔接。
transform splash_title_in:
    alpha 0.0
    zoom 1.03
    ease 1.1 alpha 1.0 zoom 1.0

image splash_art = "gui/splash.png"

label splashscreen:

    ## 自动化测试（renpy.sh <项目> test ...）里 testcase 从 Start() 开始，必须在主菜单上执行，
    ## 所以非正常“run”命令（test / lint 等）时直接跳过 splash；浏览器与桌面的正常启动不受影响。
    if renpy.game.args.command != "run":
        return

    scene black
    show splash_art at splash_title_in
    with Dissolve(0.4)

    ## hard=False：任意点击 / 按键 / 触屏都能跳过
    $ renpy.pause(2.2, hard=False)

    scene black
    with Dissolve(0.5)

    return
