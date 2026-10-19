## tests.rpy —— Ren'Py 内置自动化测试用例（开发辅助，不影响正常游玩）。
## 运行方法（需要图形环境）：
##     renpy.sh <项目目录> test path_true
##     renpy.sh <项目目录> test path_half
##     renpy.sh <项目目录> test path_miss
## 每个用例从新游戏开始，按固定选项走到结局，直到回到主菜单为止。

testcase path_true:
    run Start()
    click until "那就麻烦你带路"
    click until "好，只看火漆印"
    click until "信使的职责"
    click until label ending_true
    assert trust == 6
    click until label main_menu_screen
    $ print("TESTCASE_OK endings=%s" % sorted(persistent.endings_seen))
    $ renpy.quit()

testcase path_half:
    run Start()
    click until "你为什么要帮我"
    click until "我只能告诉你"
    click until "我要先知道"
    click until label ending_half
    assert trust == 1
    click until label main_menu_screen
    $ print("TESTCASE_OK endings=%s" % sorted(persistent.endings_seen))
    $ renpy.quit()

testcase path_miss:
    run Start()
    click until "不用了，我自己找路"
    click until "信使不能给任何人看"
    click until "我不会把信交给"
    click until label ending_miss
    assert trust == -6
    click until label main_menu_screen
    $ print("TESTCASE_OK endings=%s" % sorted(persistent.endings_seen))
    $ renpy.quit()
