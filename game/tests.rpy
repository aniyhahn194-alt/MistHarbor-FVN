## tests.rpy —— Ren'Py 内置自动化测试用例（开发辅助，不影响正常游玩）。
## 运行方法（需要图形环境）：
##     renpy.sh <项目目录> test path_true
##     renpy.sh <项目目录> test path_half
##     renpy.sh <项目目录> test path_miss
## 每个用例从新游戏开始，按固定选项走到结局，直到回到主菜单为止，
## 并在标准输出打印到达的结局与信任度，便于核对。

testcase path_true:
    run Start()
    click until "那就麻烦你带路"
    click until "好，只看火漆印"
    click until "信使的职责"
    click until label ending_true
    assert trust == 6
    $ print("TEST path_true: REACHED ending_true, trust=%d" % trust)
    click until label main_menu_screen
    $ print("TEST path_true: RETURNED to main menu")
    $ renpy.quit()

testcase path_half:
    run Start()
    click until "你为什么要帮我"
    click until "我只能告诉你"
    click until "我要先知道"
    click until label ending_half
    assert trust == 1
    $ print("TEST path_half: REACHED ending_half, trust=%d" % trust)
    click until label main_menu_screen
    $ print("TEST path_half: RETURNED to main menu")
    $ renpy.quit()

testcase path_miss:
    run Start()
    click until "不用了，我自己找路"
    click until "信使不能给任何人看"
    click until "我不会把信交给"
    click until label ending_miss
    assert trust == -6
    $ print("TEST path_miss: REACHED ending_miss, trust=%d" % trust)
    click until label main_menu_screen
    $ print("TEST path_miss: RETURNED to main menu")
    $ renpy.quit()


## 存档 / 读档：在后巷存档（trust=2），继续做出不同选择（trust 变为 0），
## 再读档，检查 trust 回到 2 且回到存档时的位置。
testcase save_load:
    run Start()
    click until "那就麻烦你带路"
    click until label ch2_alley
    assert trust == 2
    pause 1.0
    run FileSave("zz_test", confirm=False, slot=True)
    click until "抱歉，信使不能给任何人看"
    click until label ch3_lighthouse
    assert trust == 0
    $ print("TEST save_load: before load trust=%d" % trust)
    run FileLoad("zz_test", confirm=False, slot=True)
    pause 2.0
    assert trust == 2
    $ print("TEST save_load: after load trust=%d" % trust)
    click until "好，只看火漆印"
    click until label ch3_lighthouse
    assert trust == 4
    $ print("TEST save_load: replayed choice 2 after load, trust=%d" % trust)
    $ renpy.unlink_save("zz_test")
    $ renpy.quit()

## 重新开始：从中途返回主菜单，再次“开始游戏”，变量必须被重置。
testcase restart:
    run Start()
    click until "不用了，我自己找路"
    click until label ch2_alley
    assert trust == -2
    assert refused_guide
    run MainMenu(confirm=False)
    pause 1.5
    run Start()
    click until label ch1_dock
    assert trust == 0
    assert not refused_guide
    $ print("TEST restart: variables reset on new game, trust=%d" % trust)
    $ renpy.quit()
