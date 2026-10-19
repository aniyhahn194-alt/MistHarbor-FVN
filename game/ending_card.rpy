## ending_card.rpy —— 三个结局共用的结局卡片界面（由 script.rpy 里的 label show_ending 调用）。
## 数据表 ending_info 在 script.rpy 中。

screen ending_card(title, key):
    modal True
    zorder 150
    default ready = False

    $ num, label_cn, name_cn, epilogue, tint, veil, beam = ending_info[key]

    add Solid(veil) at ending_veil

    if beam > 0:
        add "gui/fx/fx_glow.png" at ending_lamp_glow(beam)
        add "gui/fx/fx_beam.png" at ending_beam(beam)

    ## 整屏透明按钮：轻触任意处返回（出现 1 秒后才生效，避免连点误触）
    button:
        xysize (1280, 720)
        background None
        action If(ready, true=Return())

    key "dismiss" action If(ready, true=Return())
    timer 1.0 action SetScreenVariable("ready", True)

    fixed at ending_card_in:

        text "ENDING [num] / 03" xalign 0.5 ypos 70 size 24 color "#5fb8c4" kerning 4

        text "[label_cn]" xalign 0.5 ypos 112 size 36 color "#aebfcd" kerning 6
        text "[name_cn]" xalign 0.5 ypos 158 size 112 color tint kerning 10 outlines [(3, "#0b1622", 0, 2)]

        add "gui/divider.png" xalign 0.5 ypos 318
        text "[epilogue]" xalign 0.5 ypos 352 size 32 color "#d6e2ea"

        hbox:
            xalign 0.5
            ypos 440
            spacing 90
            for k in ("true", "half", "miss"):
                $ got = k in persistent.endings_seen
                vbox:
                    spacing 4
                    xsize 190
                    add ("gui/lamp_on.png" if got else "gui/lamp_off.png") xalign 0.5
                    text (ending_info[k][2] if got else "？？？？") xalign 0.5 size 26 color ("#f3c677" if k == key else ("#aebfcd" if got else "#5d7080"))

        text "已解锁结局 [len(persistent.endings_seen)] / 3" xalign 0.5 ypos 560 size 26 color "#8fa6b6"

        textbutton "返回标题":
            style "ending_button"
            xalign 0.5
            ypos 606
            action Return()


style ending_button:
    background Frame("gui/button/quick_[prefix_]background.png", 22, 22, tile=False)
    xsize 320
    ysize 84

style ending_button_text:
    size 34
    xalign 0.5
    yalign 0.5
    idle_color "#eef3f6"
    hover_color "#f3c677"
    insensitive_color "#5a6c7a"


transform ending_veil:
    alpha 0.0
    linear 0.8 alpha 1.0

transform ending_card_in:
    alpha 0.0
    yoffset 24
    pause 0.35
    ease 0.9 alpha 1.0 yoffset 0

transform ending_lamp_glow(power):
    anchor (0.5, 0.5)
    pos (800, 169)
    zoom 2.2
    alpha 0.0
    linear 1.0 alpha (0.45 * power)
    block:
        ease 2.6 alpha (0.62 * power)
        ease 2.6 alpha (0.4 * power)
        repeat

transform ending_beam(power):
    anchor (0.5, 0.5)
    pos (800, 169)
    transform_anchor True
    rotate -3.0
    alpha 0.0
    linear 1.2 alpha power
    block:
        ease 7.0 rotate 4.0
        ease 7.0 rotate -3.0
        repeat
