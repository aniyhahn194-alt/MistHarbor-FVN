## script.rpy —— 《雾港来信》V0.1 主剧本
##
## 剧情结构（共 3 个分支选择 + 3 个结局）：
##   start
##    └─ ch1_dock        栈桥：遇见林岚，选择 1（是否让她带路）
##        └─ ch2_alley   后巷：选择 2（是否让她看火漆印）
##            └─ ch3_lighthouse  灯塔：选择 3（是否交出信件）
##                ├─ trust >= 4  → ending_true   结局一·灯塔回信
##                ├─ trust >= 1  → ending_half   结局二·半盏灯火
##                └─ 其他        → ending_miss   结局三·雾中错过
## 所有结局最后都以 return 结束，回到主菜单。


################################################################################
## 角色定义
################################################################################

## image= 参数让 "hz worried" 这样的写法可以在说话的同时切换表情。
define hz = Character("灰舟", color="#8fb4e8", image="huizhou")
define ll = Character("林岚", color="#f0a060", image="linlan")


################################################################################
## 图像定义
################################################################################
## 背景（1280x720）
image bg dock = "images/bg_dock.png"
image bg alley = "images/bg_alley.png"
image bg lighthouse = "images/bg_lighthouse.png"

## 立绘：原图 640x1040，缩放到适合 720p 画面的大小。
## 图像名第一个词是 tag，同一个 tag 的新图像会替换旧图像（即切换表情）。
image huizhou normal = Transform("images/huizhou_normal.png", zoom=0.64)
image huizhou worried = Transform("images/huizhou_worried.png", zoom=0.64)
image linlan normal = Transform("images/linlan_normal.png", zoom=0.64)
image linlan smile = Transform("images/linlan_smile.png", zoom=0.64)


################################################################################
## 变换与转场
################################################################################

## 站位
transform pos_left:
    xalign 0.18
    yalign 1.0

transform pos_right:
    xalign 0.82
    yalign 1.0

## 滑入动画：角色从屏幕外缓动进场
transform enter_left:
    xalign -0.3
    yalign 1.0
    ease 0.6 xalign 0.18

transform enter_right:
    xalign 1.3
    yalign 1.0
    ease 0.6 xalign 0.82

## 灯塔点亮时的暖色闪光
define flash_lamp = Fade(0.2, 0.0, 1.0, color="#fff1c0")
## 场景切换使用较慢的淡入淡出
define slow_fade = Fade(0.8, 0.3, 0.8)


################################################################################
## 游戏变量（必须用 default 初始化，才能正确存档/回滚）
################################################################################

## 林岚对灰舟的信任度：选择会增减它，最终决定结局。
default trust = 0
## 第一次选择：是否拒绝了林岚带路
default refused_guide = False
## 第二次选择：是否让林岚看过火漆印
default seal_shown = False

## 持久化数据（跨存档保存）：已达成的结局，供后续版本做结局回顾界面。
default persistent.endings_seen = set()


################################################################################
## 辅助代码
################################################################################

init python:

    def change_trust(delta):
        """修改信任度并给出轻量提示（不暴露具体数值）。"""
        store.trust += delta
        if delta > 0:
            renpy.notify("林岚对你的信任提高了")
        elif delta < 0:
            renpy.notify("林岚对你的信任降低了")


## 信封预览界面：用 show screen / hide screen 控制，方便以后扩展成物品栏。
screen letter_card(title, body):
    zorder 50
    frame:
        align (0.5, 0.36)
        padding (44, 30)
        background Solid("#eadcb8")
        xsize 620
        vbox:
            spacing 12
            text title size 30 color "#3a2c1c" xalign 0.5
            text body size 24 color "#4d3b28" xalign 0.5 text_align 0.5


################################################################################
## 序章：栈桥
################################################################################

label start:

    ## 每次开始新游戏时重置（读档不会进入这里）
    $ trust = 0
    $ refused_guide = False
    $ seal_shown = False

    scene black
    with fade

    "雾港的黄昏来得很早。"

    scene bg dock
    with slow_fade

    "傍晚六点，雾从海面漫上栈桥，把一盏盏路灯吞成模糊的光斑。"

    "我叫灰舟，是雾港邮局最年轻的信使。今天下午，老渡把一封信塞进我的邮包，只交代了三句话。"

    "“午夜钟响之前，把它送到灯塔看守人手里。”"

    "“只交给他本人，不要给任何人看。”"

    "“……还有，别在雾里轻易相信陌生人。”"

    show screen letter_card("收信人：灯塔看守人", "寄信人：（空白）\n信封一角，印着一枚褪色的锚形火漆。")
    with dissolve

    "我翻遍了邮局的旧名册。灯塔看守人那一栏，早在十年前就被划掉了。"

    hide screen letter_card
    with dissolve

    "没有收信人的信，真的送得到吗？我按紧邮包的搭扣，沿着栈桥向货仓区走去。"

    jump ch1_dock


label ch1_dock:

    show linlan normal at enter_right
    with dissolve

    "栈桥尽头的缆桩旁，有人提着一盏小灯，像是已经等了很久。"

    ll "晚上好，信使先生。这个时辰还在栈桥上赶路的，多半是要去灯塔的人。"

    show huizhou normal at enter_left
    with dissolve

    hz worried "……你怎么知道我要去灯塔？"

    ll smile "别紧张。我叫林岚，在港口替人找路、找东西，也找消息。"

    ll normal "好心提醒你一句：三号码头今晚被海关封了，货仓区的大路走不通。想在午夜前赶到灯塔，只能穿过后巷里的旧信使公会。"

    "她提到了灯塔。我从没对任何人说过。"

    menu:
        "面对这位来历不明的狐狸，我决定——"

        "“那就麻烦你带路。”":
            $ change_trust(2)
            hz normal "既然大路封了，我也没有别的选择。麻烦你带路。"
            ll smile "好。跟紧我，雾里的石板路很滑。"

        "“你为什么要帮我？”":
            $ change_trust(1)
            hz worried "我们素不相识，你为什么要帮我？"
            ll normal "因为你邮包口露出的那一角信封——锚形的火漆，已经十年没有人用过了。"
            ll smile "我不要你的信，只想陪你走一段路。你可以随时觉得我可疑。"
            hz normal "……先走吧。"

        "“不用了，我自己找路。”":
            $ change_trust(-2)
            $ refused_guide = True
            hz normal "谢谢，不必。信使有信使自己的路。"
            ll normal "随你。"
            hide linlan with dissolve
            "我绕开她，径直走向三号码头。铁门果然落了锁，两名海关巡逻员在雾里来回踱步。"
            "她没有骗我。我咬了咬牙，折回栈桥，朝她说的那条后巷走去。"

    jump ch2_alley


################################################################################
## 第二幕：后巷
################################################################################

label ch2_alley:

    scene bg alley
    with slow_fade

    show huizhou normal at pos_left
    show linlan normal at pos_right
    with dissolve

    "后巷窄得只容两人并肩，潮湿的砖墙上挂着一盏昏黄的灯。"

    if refused_guide:
        ll smile "你果然还是来了。放心，我不会再多嘴——除非你想听。"
        hz worried "……我只是想确认路是通的。"
    else:
        ll normal "到了。就是这扇门——信使公会的旧门。"

    "门楣上挂着褪色的招牌：一只衔着锚的信封。"

    ll normal "公会十年前就解散了。传闻是因为一封信，一封没有送到的信。"

    hz worried "没有送到的信？"

    ll normal "雾钟号沉没的那一夜，有人托信使送一份货单去灯塔。信使没能出发，货单从此下落不明。第二天，船沉了，一百多条命，没有人负责。"

    ll normal "我只想知道，那封信是不是还在这世上。"

    "她看向我的邮包。雾里，她的眼睛像两粒熄不灭的灯火。"

    ll normal "你包里那封信……能让我看一眼封口的火漆印吗？只看印，不看内容。"

    menu:
        "邮局的规矩是不让别人看信。可她知道的事，比我多得多。"

        "“好，只看火漆印。”":
            $ change_trust(2)
            $ seal_shown = True
            show screen letter_card("锚形火漆印", "（只露出封口的火漆，其余字迹被手指遮住）")
            with dissolve
            ll smile "……果然。这是公会的“滞留封”，只有没能按时送出的信，才会盖这一枚。"
            hide screen letter_card
            with dissolve
            ll normal "这封信，已经迟到了整整十年。"
            hz worried "十年……老渡一个字都没有提过。"

        "“我只能告诉你，收信人是灯塔看守人。”":
            ll normal "……灯塔看守人。"
            ll normal "这就够了。一个谨慎的信使，总比一个多嘴的信使可靠。"

        "“抱歉，信使不能给任何人看。”":
            $ change_trust(-2)
            hz normal "抱歉，信使不能给任何人看。"
            ll normal "……你很守规矩。"
            ll normal "不过规矩有时候，也会把人困在雾里。"

    "钟楼敲了十一下，离午夜只剩一个钟头。我们穿过后巷，尽头就是灯塔所在的岬角。"

    jump ch3_lighthouse


################################################################################
## 第三幕：灯塔
################################################################################

label ch3_lighthouse:

    scene bg lighthouse
    with slow_fade

    show huizhou normal at pos_left
    show linlan normal at pos_right
    with dissolve

    "雾在岬角上散开了一些。灯塔孤零零地立在夜色里，塔顶的灯室一片漆黑。"

    hz worried "灯塔没有亮……看守人在哪里？"

    ll normal "没有看守人。十年前，最后一位看守人的名字，就被邮局划掉了。"

    if seal_shown:
        ll normal "你看过那枚“滞留封”了，应该明白：这封信等的不是一个名字，而是一盏灯。"

    ll normal "可是每逢起雾的夜晚，总有人把灯点亮。你想知道是谁吗？"

    ll normal "最后一个问题。如果这封信会把你卷进麻烦，你还愿意把它交出来吗？"

    menu:
        "钟声就要响了。我握紧邮包带，终于开口——"

        "“信使的职责，就是把信交到收信人手里。”":
            $ change_trust(2)
            hz normal "信使的职责，就是把信交到收信人手里。麻烦不麻烦，是收信人的事。"

        "“我要先知道，收信人到底是谁。”":
            hz normal "我要先知道，收信人到底是谁。"
            ll smile "很公平。"

        "“我不会把信交给没有证明身份的人。”":
            $ change_trust(-2)
            hz normal "我不会把信交给没有证明身份的人。"
            ll normal "……是啊，这才是信使。"

    ## 根据累计信任度分流到不同结局
    if trust >= 4:
        jump ending_true
    elif trust >= 1:
        jump ending_half
    else:
        jump ending_miss


################################################################################
## 结局
################################################################################

label ending_true:

    show linlan smile
    with dissolve

    ll smile "谢谢你，灰舟。你通过了我所有的试探。"

    hz worried "试探？"

    ll normal "我就是灯塔看守人。上一任看守人是我父亲，雾钟号出事那一夜，他一直在等这封信。"

    ll normal "这十年里，来找这封信的人，有一半是商会派来的。我不敢先开口。"

    hz normal "所以你才一路试探我。"

    ll smile "对不起。也谢谢你，每一次都选择了相信我。"

    "我把信交到她手里。她拆开封口，借着小灯读了很久，尾巴轻轻垂了下来。"

    ll normal "第七号舱，超载三成；雾警，未报。……是这份货单。有了它，当年的真相就能见光了。"

    "她提着灯登上塔梯。几分钟后，塔顶的灯室里亮起一团暖光，光柱劈开浓雾，扫过整座港口。"

    scene bg lighthouse with flash_lamp

    show huizhou normal at pos_left
    show linlan smile at pos_right
    with dissolve

    ll smile "灰舟，信使的工作还没完。我有一封回信，想请你明天送去商会旧址。你愿意吗？"

    hz normal "只要收信人还在，信就该送到。"

    "午夜钟声响起。雾港的雾，第一次被一盏灯照亮了。"

    call show_ending("结局一 · 灯塔回信", "true")
    return


label ending_half:

    show linlan normal
    with dissolve

    ll normal "你把信带到了这里，却还在犹豫。这样也好。"

    ll normal "我现在无法证明什么。你信我一半，我也只能告诉你一半——我是替灯塔守灯的人。"

    ll smile "把信放进塔下的信箱吧，按规矩盖上投递章。明晚，我会取走它。"

    hz normal "……好。规矩就是规矩。"

    "我把信放进灯塔脚下那只锈迹斑斑的信箱，盖下投递章。午夜钟声同时响起。"

    hide linlan
    with dissolve

    ll smile "明天夜里，灯会为你亮。到时候，我把另一半也告诉你。"

    "她的身影消失在雾里。塔顶，一点微弱的光亮了起来。"

    call show_ending("结局二 · 半盏灯火", "half")
    return


label ending_miss:

    show linlan normal
    show huizhou worried
    with dissolve

    ll normal "我明白了。信使应该谨慎，你没有做错。"

    ll normal "只是雾里的路，有时候需要一点点信任才能走完。"

    hide linlan
    with dissolve

    ll "再见，灰舟。"

    "午夜钟声响起，塔顶依旧漆黑。没有看守人，也没有收信人。"

    "我把信带回邮局，在登记簿上写下：无法投递。"

    "一周后的雾夜，我在窗边看见远处的岬角上，灯亮了一瞬——像有人在回答一封没有人读过的信。"

    call show_ending("结局三 · 雾中错过", "miss")
    return


## 结局卡片：显示标题、记录已达成结局，然后返回调用处。
label show_ending(title, key):

    scene black
    with slow_fade

    $ persistent.endings_seen.add(key)

    centered "{size=+10}[title]{/size}"

    centered "已解锁结局 [len(persistent.endings_seen)] / 3"

    centered "—— 《雾港来信》V0.1 完 ——"

    return
