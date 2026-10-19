## capture_screenshots.rpy —— 真实剧情截图辅助脚本（开发工具，不属于游戏本体）
##
## 用法：把本文件临时复制到 game/ 下，然后（需要图形环境）：
##     MH_SHOT_DIR=/tmp/mh_shots renpy.sh <项目目录> test shots_true
##     MH_SHOT_DIR=/tmp/mh_shots renpy.sh <项目目录> test shots_half
##     MH_SHOT_DIR=/tmp/mh_shots renpy.sh <项目目录> test shots_miss
## 截图完成后请把它从 game/ 删除，不要提交到 game/。
##
## 原理：testcase 驱动真实剧情流程（定时 dismiss 推进对白 + 点击真实选项）；
## periodic 回调检测“当前屏幕上是否出现了指定的界面/台词/选项”，
## 出现并稳定显示 0.8 秒后调用 renpy.screenshot 截图。截图内容就是真实剧情画面。

init python:
    import os, time

    SHOT_DIR = os.environ.get("MH_SHOT_DIR", "/tmp/mh_shots")
    shot_done = set()
    shot_seen = {}

    ## (文件名, 类型, 匹配内容)
    ##   screen：屏幕名；say：对话文本包含；choice：选项文字包含
    SHOT_RULES = [
        ("01_main_menu", "screen", "main_menu"),
        ("02_dialogue_fox_smile", "say", "别紧张"),
        ("03_dialogue_wolf_worried", "say", "你怎么知道我要去灯塔"),
        ("04_choice_1_dock", "choice", "那就麻烦你带路"),
        ("05_letter_card", "screen", "letter_card"),
        ("06_dialogue_alley", "say", "后巷窄得只容两人并肩"),
        ("07_choice_2_alley", "choice", "好，只看火漆印"),
        ("08_dialogue_lighthouse", "say", "灯塔没有亮"),
        ("09_choice_3_lighthouse", "choice", "信使的职责"),
        ("10_ending_true_dialogue", "say", "我就是灯塔看守人"),
        ("11_ending_true_card", "screen_key", ("ending_card", "true")),
        ("12_ending_half_dialogue", "say", "把信放进塔下的信箱吧"),
        ("13_ending_half_card", "screen_key", ("ending_card", "half")),
        ("14_ending_miss_dialogue", "say", "我明白了。信使应该谨慎"),
        ("15_ending_miss_card", "screen_key", ("ending_card", "miss")),
        ("16_menu_save", "screen", "save"),
        ("17_menu_preferences", "screen", "preferences"),
        ("18_menu_history", "screen", "history"),
        ("19_menu_about", "screen", "about"),
    ]

    def _shot_hit(kind, pat):
        if kind == "screen":
            return renpy.get_screen(pat) is not None
        if kind == "screen_key":
            s = renpy.get_screen(pat[0])
            return bool(s) and s.scope.get("key") == pat[1]
        if kind == "say":
            s = renpy.get_screen("say")
            return bool(s) and pat in str(s.scope.get("what", ""))
        if kind == "choice":
            s = renpy.get_screen("choice")
            if not s:
                return False
            return any(pat in str(i.caption) for i in s.scope.get("items", []))
        return False

    shot_run = False
    shot_hold_until = 0
    shot_last = ["", 0]

    def shot_periodic():
        ## 目标画面出现后暂时关闭自动前进，保证它稳定停留到截图完成
        global shot_hold_until
        now = time.time()
        holding = now < shot_hold_until
        for key, kind, pat in SHOT_RULES:
            if key in shot_done:
                continue
            if _shot_hit(kind, pat):
                holding = True
                shot_seen.setdefault(key, now)
                if now - shot_seen[key] > 0.8:
                    if not os.path.isdir(SHOT_DIR):
                        os.makedirs(SHOT_DIR)
                    renpy.screenshot(os.path.join(SHOT_DIR, key + ".png"))
                    shot_done.add(key)
                    shot_hold_until = now + 1.0
            else:
                shot_seen.pop(key, None)
        if shot_run and not holding and renpy.get_screen("say"):
            ## 自己实现自动前进：对话显示满 1 秒后发送 dismiss 事件
            what = str(renpy.get_screen("say").scope.get("what", ""))
            if what != shot_last[0]:
                shot_last[0] = what
                shot_last[1] = now
            elif now - shot_last[1] > 1.0:
                shot_last[1] = now
                renpy.queue_event("dismiss")

    config.periodic_callbacks.append(shot_periodic)

    class ShotWait(Action):
        """testcase 用：截图完成后才视为 sensitive。"""
        def __init__(self, key):
            self.key = key

        def get_sensitive(self):
            return self.key in shot_done

        def __call__(self):
            return None


testcase shots_true:
    $ renpy.set_physical_size((1280, 720))
    $ _preferences.text_cps = 0
    $ shot_run = True
    pause 0.2 until run ShotWait("01_main_menu")
    run Start()
    pause 0.2 until run ShotWait("04_choice_1_dock")
    "那就麻烦你带路"
    pause 0.2 until run ShotWait("07_choice_2_alley")
    "好，只看火漆印"
    pause 0.2 until run ShotWait("09_choice_3_lighthouse")
    "信使的职责"
    pause 0.2 until run ShotWait("11_ending_true_card")
    click until label main_menu_screen
    $ renpy.quit()

testcase shots_half:
    $ _preferences.text_cps = 0
    $ shot_run = True
    run Start()
    "你为什么要帮我"
    "我只能告诉你"
    "我要先知道"
    pause 0.2 until run ShotWait("13_ending_half_card")
    click until label main_menu_screen
    $ renpy.quit()

testcase shots_miss:
    $ _preferences.text_cps = 0
    $ shot_run = True
    run Start()
    "不用了，我自己找路"
    "信使不能给任何人看"
    "我不会把信交给"
    pause 0.2 until run ShotWait("15_ending_miss_card")
    click until label main_menu_screen
    $ renpy.quit()


## 菜单类界面：从真实剧情中途打开（后巷选项出现后），逐个截图再返回
testcase shots_menus:
    $ _preferences.text_cps = 0
    $ shot_run = True
    run Start()
    pause 0.2 until run ShotWait("04_choice_1_dock")
    run ShowMenu("save")
    pause 0.2 until run ShotWait("16_menu_save")
    run ShowMenu("preferences")
    pause 0.2 until run ShotWait("17_menu_preferences")
    run ShowMenu("history")
    pause 0.2 until run ShotWait("18_menu_history")
    run ShowMenu("about")
    pause 0.2 until run ShotWait("19_menu_about")
    $ renpy.quit()
