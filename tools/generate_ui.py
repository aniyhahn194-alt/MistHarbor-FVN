#!/usr/bin/env python3
"""生成《雾港来信》V0.2 的原创界面素材（对话框、按钮、滑条、面板、特效层等）。

仅为开发期工具，游戏运行时不依赖本脚本；生成结果已提交到 game/gui/ 与 game/images/。
依赖：Pillow（pip install pillow）。用法：python3 tools/generate_ui.py
全部图形由代码绘制（圆角矩形 / 渐变 / 高斯模糊 / 随机噪点），不使用任何外部图片或模板图。
配色：夜雾深蓝 + 冷青 + 灯塔暖金。
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUI = os.path.join(ROOT, "game", "gui")
IMG = os.path.join(ROOT, "game", "images")

NAVY0 = (8, 16, 26)
NAVY1 = (11, 22, 34)
NAVY2 = (17, 34, 51)
NAVY3 = (26, 52, 74)
CYAN = (95, 184, 196)
CYAN_D = (42, 127, 134)
GOLD = (243, 198, 119)
GOLD_D = (200, 150, 70)
TEXT = (238, 243, 246)

SS = 4  # 超采样倍数


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)
    print("wrote", os.path.relpath(path, ROOT), img.size)


def rrect(size, radius, fill, outline=None, width=0, inset=0):
    """超采样圆角矩形，返回 RGBA。"""
    w, h = size
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    box = [inset * SS, inset * SS, (w - inset) * SS - 1, (h - inset) * SS - 1]
    d.rounded_rectangle(box, radius=radius * SS, fill=fill, outline=outline, width=width * SS)
    return img.resize(size, Image.LANCZOS)


def glow_around(size, radius, color, alpha, blur):
    """圆角矩形外发光层（用于悬停态）。"""
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([blur, blur, w - blur - 1, h - blur - 1], radius=radius, fill=alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(blur / 2))
    layer.paste(Image.new("RGBA", size, rgba(color)), (0, 0), mask)
    return layer


def hgrad_alpha(size, a0, a1, color=NAVY0, power=1.0):
    """水平方向 alpha 渐变。"""
    w, h = size
    row = Image.new("L", (w, 1))
    for x in range(w):
        t = (x / max(1, w - 1)) ** power
        row.putpixel((x, 0), int(a0 + (a1 - a0) * t))
    mask = row.resize(size)
    img = Image.new("RGBA", size, rgba(color))
    img.putalpha(mask)
    return img


# ---------------------------------------------------------------- 对话框 / 姓名框
def make_textbox(W=1280, H=260):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    top = 22
    # 顶部渐隐
    fade = Image.new("L", (1, top))
    for y in range(top):
        fade.putpixel((0, y), int(150 * (y / top) ** 1.6))
    img.paste(Image.new("RGBA", (W, top), rgba(NAVY0)), (0, 0), fade.resize((W, top)))
    body = Image.new("RGBA", (W, H - top), rgba(NAVY1, 236))
    # 底部更深
    shade = Image.new("L", (1, H - top))
    for y in range(H - top):
        shade.putpixel((0, y), int(70 * (y / (H - top))))
    body.paste(Image.new("RGBA", body.size, rgba(NAVY0)), (0, 0), shade.resize(body.size))
    img.paste(body, (0, top))
    d = ImageDraw.Draw(img)
    d.rectangle([0, top, W, top + 1], fill=rgba(CYAN, 150))
    # 灯光暖金短线：落在右侧，提示“灯塔”意象
    d.rectangle([W - 330, top, W - 90, top + 1], fill=rgba(GOLD, 200))
    return img


def make_namebox(W=300, H=64):
    base = rrect((W, H), 12, rgba(NAVY2, 245), rgba(CYAN, 210), 2)
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([0, 0, 9, H - 1], radius=4, fill=rgba(GOLD))
    return base


# ---------------------------------------------------------------- 按钮
def make_choice(hover, W=800, H=96):
    if hover:
        img = glow_around((W, H), 18, GOLD, 120, 14)
        face = rrect((W - 24, H - 24), 16, rgba(NAVY3, 245), rgba(GOLD, 255), 3)
    else:
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        face = rrect((W - 24, H - 24), 16, rgba(NAVY2, 232), rgba(CYAN, 200), 2)
    img.alpha_composite(face, (12, 12))
    d = ImageDraw.Draw(img)
    # 左侧小灯点
    cx, cy = 44, H // 2
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=rgba(GOLD if hover else CYAN))
    return img


def make_quick(hover, W=120, H=80):
    if hover:
        img = rrect((W, H), 16, rgba(NAVY3, 245), rgba(GOLD), 3)
    else:
        img = rrect((W, H), 16, rgba(NAVY2, 205), rgba(CYAN, 150), 2)
    return img


def make_nav(hover, selected=False, W=420, H=80):
    """导航按钮：左侧竖灯条 + 渐隐面板。"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if hover or selected:
        panel = hgrad_alpha((W, H - 8), 215 if hover else 150, 0, NAVY3, power=0.8)
        img.alpha_composite(panel, (0, 4))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 6, 6, H - 7], fill=rgba(GOLD if hover else CYAN))
    else:
        panel = hgrad_alpha((W, H - 8), 120, 0, NAVY0, power=0.6)
        img.alpha_composite(panel, (0, 4))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 14, 3, H - 15], fill=rgba(CYAN_D, 190))
    return img


def make_plain_button(hover, W=300, H=44):
    if hover:
        return rrect((W, H), 10, rgba(NAVY3, 170), rgba(CYAN, 190), 2)
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def make_slot(hover, W=268, H=224):
    if hover:
        img = glow_around((W, H), 14, GOLD, 110, 10)
        img.alpha_composite(rrect((W - 12, H - 12), 12, rgba(NAVY3, 245), rgba(GOLD), 3), (6, 6))
    else:
        img = rrect((W, H), 12, rgba(NAVY2, 235), rgba(CYAN, 150), 2)
    return img


def make_check(selected, W=44, H=44):
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    box = [6 * SS, 8 * SS, 34 * SS, 36 * SS]
    d.rounded_rectangle(box, radius=6 * SS, fill=rgba(GOLD) if selected else rgba(NAVY0, 160), outline=rgba(GOLD if selected else CYAN), width=3 * SS)
    if selected:
        d.line([(12 * SS, 22 * SS), (18 * SS, 29 * SS), (29 * SS, 15 * SS)], fill=rgba(NAVY1), width=4 * SS, joint="curve")
    return img.resize((W, H), Image.LANCZOS)


def make_radio(selected, W=44, H=44):
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([6 * SS, 8 * SS, 34 * SS, 36 * SS], fill=rgba(NAVY0, 160), outline=rgba(GOLD if selected else CYAN), width=3 * SS)
    if selected:
        d.ellipse([13 * SS, 15 * SS, 27 * SS, 29 * SS], fill=rgba(GOLD))
    return img.resize((W, H), Image.LANCZOS)


# ---------------------------------------------------------------- 条 / 滑条 / 滚动条
def make_bar(W, H, left=False, right=False, hover=False):
    track = rrect((W, H), 8, rgba(NAVY0, 190), rgba(CYAN_D, 160), 1, inset=0)
    return track


def make_slider_bar(hover, W=400, H=44):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    track = rrect((W, 14), 7, rgba(NAVY0, 210), rgba(CYAN if hover else CYAN_D, 220), 2)
    img.alpha_composite(track, (0, (H - 14) // 2))
    return img


def make_slider_thumb(hover, W=26, H=44):
    return rrect((W, H), 9, rgba(GOLD if hover else (226, 184, 110)), rgba(NAVY1), 2)


def make_scroll_bar(hover, W=16, H=400, vertical=True):
    return rrect((W, H), 8, rgba(NAVY0, 180), rgba(CYAN_D, 120), 1)


def make_scroll_thumb(hover, W=16, H=400):
    return rrect((W, H), 8, rgba(CYAN if hover else CYAN_D, 235))


# ---------------------------------------------------------------- 框 / 提示 / 遮罩
def make_frame(W=600, H=250):
    return rrect((W, H), 18, rgba(NAVY1, 235), rgba(CYAN, 170), 2)


def make_notify(W=600, H=60):
    img = rrect((W, H), H // 2, rgba(NAVY1, 238), rgba(GOLD, 220), 2)
    d = ImageDraw.Draw(img)
    d.ellipse([26, H // 2 - 7, 40, H // 2 + 7], fill=rgba(GOLD))
    return img


def make_skip(W=300, H=64):
    img = rrect((W, H), H // 2, rgba(NAVY1, 238), rgba(CYAN, 220), 2)
    return img


def make_menu_overlay(W=1280, H=720, width=760):
    """主菜单左侧渐隐面板。"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(hgrad_alpha((width, H), 238, 0, NAVY0, power=0.55), (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 3, H], fill=rgba(CYAN_D, 200))
    return img


def make_game_menu_overlay(W=1280, H=720):
    img = Image.new("RGBA", (W, H), rgba(NAVY0, 150))
    img.alpha_composite(hgrad_alpha((360, H), 235, 0, NAVY0, power=0.5), (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 3, H], fill=rgba(CYAN_D, 200))
    d.rectangle([0, 112, W, 113], fill=rgba(CYAN, 70))
    return img


def make_confirm_overlay(W=1280, H=720):
    return Image.new("RGBA", (W, H), rgba(NAVY0, 170))


# ---------------------------------------------------------------- 背景（主菜单 / 游戏菜单）
def darken_with_navy(img, amount):
    overlay = Image.new("RGB", img.size, NAVY1)
    return Image.blend(img.convert("RGB"), overlay, amount)


def vignette(img, strength=0.55):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([-w * 0.25, -h * 0.35, w * 1.25, h * 1.35], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(min(w, h) // 5))
    dark = Image.new("RGB", (w, h), NAVY0)
    inv = ImageChops.invert(mask).point(lambda v: int(v * strength))
    return Image.composite(dark, img.convert("RGB"), inv)


def make_main_menu_bg():
    base = Image.open(os.path.join(IMG, "bg_lighthouse.png")).convert("RGB")
    img = darken_with_navy(base, 0.38)
    img = vignette(img, 0.7)
    return img


def make_game_menu_bg():
    base = Image.open(os.path.join(IMG, "bg_dock.png")).convert("RGB")
    img = base.filter(ImageFilter.GaussianBlur(7))
    img = darken_with_navy(img, 0.6)
    return vignette(img, 0.6)


# ---------------------------------------------------------------- 特效层（光束 / 雾 / 灯）
def make_beam(W=2400, H=320):
    """灯塔光束：以图像中心为灯点，向左右两侧延伸的楔形光。"""
    S = 2
    layer = Image.new("L", (W // S, H // S), 0)
    px = layer.load()
    cx, cy = (W // S) / 2, (H // S) / 2
    spread = math.radians(4.2)
    for y in range(H // S):
        for x in range(W // S):
            dx = abs(x - cx)
            if dx < 4:
                continue
            ang = math.atan2(abs(y - cy), dx)
            if ang < spread:
                edge = 1 - ang / spread
                fall = max(0.0, 1 - dx / (W // S / 2)) ** 1.4
                px[x, y] = int(255 * (edge ** 0.8) * fall)
    layer = layer.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
    img = Image.new("RGBA", (W, H), rgba((255, 236, 180)))
    img.putalpha(layer.point(lambda v: int(v * 0.5)))
    return img


def make_fog(W=1280, H=360, seed=5, color=(190, 208, 220), strength=120, blobs=22):
    """水平可无缝平铺（周期 W/2）的雾层。"""
    rnd = random.Random(seed)
    period = W // 2
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    for _ in range(blobs):
        cx = rnd.randint(0, period)
        cy = rnd.randint(int(H * 0.25), H)
        rx = rnd.randint(period // 8, period // 3)
        ry = rnd.randint(H // 14, H // 6)
        a = rnd.randint(40, strength)
        for k in (0, 1):
            for off in (-period, 0, period):
                x0 = cx + off + k * period
                d.ellipse([x0 - rx, cy - ry, x0 + rx, cy + ry], fill=a)
    mask = mask.filter(ImageFilter.GaussianBlur(H // 12))
    # 顶部与底部渐隐，避免出现硬边
    fade = Image.new("L", (1, H))
    for y in range(H):
        t = y / (H - 1)
        fade.putpixel((0, y), int(255 * min(1.0, t * 3.0) * min(1.0, (1 - t) * 6.0)))
    mask = ImageChops.multiply(mask, fade.resize((W, H)))
    img = Image.new("RGBA", (W, H), rgba(color))
    img.putalpha(mask)
    return img


def make_lamp(lit, S=72):
    img = Image.new("RGBA", (S * SS, S * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = S * SS // 2, S * SS // 2
    r = int(S * SS * 0.2)
    if lit:
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([cx - r * 2.3, cy - r * 2.3, cx + r * 2.3, cy + r * 2.3], fill=rgba(GOLD, 150))
        glow = glow.filter(ImageFilter.GaussianBlur(S * SS * 0.1))
        img.alpha_composite(glow)
        d = ImageDraw.Draw(img)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgba((255, 236, 180)), outline=rgba(GOLD), width=SS * 2)
    else:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgba(NAVY2), outline=rgba(CYAN_D), width=SS * 2)
    return img.resize((S, S), Image.LANCZOS)


def make_divider(W=640, H=14):
    """标题下的细分隔线：两侧冷青渐隐，中间一枚金色灯点。"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    half = W // 2 - 14
    for side in (0, 1):
        g = hgrad_alpha((half, 2), 0, 220, CYAN) if side == 0 else hgrad_alpha((half, 2), 220, 0, CYAN)
        img.alpha_composite(g, (0 if side == 0 else W - half, H // 2 - 1))
    d = ImageDraw.Draw(img)
    d.ellipse([W // 2 - 5, H // 2 - 5, W // 2 + 5, H // 2 + 5], fill=rgba(GOLD))
    return img


def make_radial(S=512, color=GOLD, peak=200):
    img = Image.new("RGBA", (S, S), rgba(color, 0))
    mask = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([S * 0.3, S * 0.3, S * 0.7, S * 0.7], fill=peak)
    mask = mask.filter(ImageFilter.GaussianBlur(S / 11))
    img.putalpha(mask)
    return img


def make_letter_paper(W=660, H=280):
    """信封预览用的羊皮纸底图：暖色纸面 + 深蓝描边 + 金色内线。"""
    paper = rrect((W, H), 14, rgba((233, 220, 186)), rgba(NAVY2), 4)
    d = ImageDraw.Draw(paper)
    d.rounded_rectangle([14, 14, W - 15, H - 15], radius=8, outline=rgba(GOLD_D, 170), width=2)
    return paper


def main():
    save(make_textbox(), os.path.join(GUI, "textbox.png"))
    save(make_namebox(), os.path.join(GUI, "namebox.png"))
    save(make_choice(False), os.path.join(GUI, "button", "choice_idle_background.png"))
    save(make_choice(True), os.path.join(GUI, "button", "choice_hover_background.png"))
    save(make_quick(False), os.path.join(GUI, "button", "quick_idle_background.png"))
    save(make_quick(True), os.path.join(GUI, "button", "quick_hover_background.png"))
    save(make_plain_button(False), os.path.join(GUI, "button", "idle_background.png"))
    save(make_plain_button(True), os.path.join(GUI, "button", "hover_background.png"))
    save(make_nav(False), os.path.join(GUI, "button", "nav_idle_background.png"))
    save(make_nav(True), os.path.join(GUI, "button", "nav_hover_background.png"))
    save(make_nav(False, True), os.path.join(GUI, "button", "nav_selected_idle_background.png"))
    save(make_nav(True), os.path.join(GUI, "button", "nav_selected_hover_background.png"))
    save(make_slot(False), os.path.join(GUI, "button", "slot_idle_background.png"))
    save(make_slot(True), os.path.join(GUI, "button", "slot_hover_background.png"))
    save(make_check(False), os.path.join(GUI, "button", "check_foreground.png"))
    save(make_check(True), os.path.join(GUI, "button", "check_selected_foreground.png"))
    save(make_radio(False), os.path.join(GUI, "button", "radio_foreground.png"))
    save(make_radio(True), os.path.join(GUI, "button", "radio_selected_foreground.png"))

    for name, hv in (("idle", False), ("hover", True)):
        save(make_slider_bar(hv), os.path.join(GUI, "slider", f"horizontal_{name}_bar.png"))
        save(make_slider_thumb(hv), os.path.join(GUI, "slider", f"horizontal_{name}_thumb.png"))
        v = make_slider_bar(hv).rotate(90, expand=True)
        save(v, os.path.join(GUI, "slider", f"vertical_{name}_bar.png"))
        save(make_slider_thumb(hv).rotate(90, expand=True), os.path.join(GUI, "slider", f"vertical_{name}_thumb.png"))
        save(make_scroll_bar(hv, 700, 16), os.path.join(GUI, "scrollbar", f"horizontal_{name}_bar.png"))
        save(make_scroll_thumb(hv, 700, 16), os.path.join(GUI, "scrollbar", f"horizontal_{name}_thumb.png"))
        save(make_scroll_bar(hv, 16, 700), os.path.join(GUI, "scrollbar", f"vertical_{name}_bar.png"))
        save(make_scroll_thumb(hv, 16, 700), os.path.join(GUI, "scrollbar", f"vertical_{name}_thumb.png"))

    save(make_bar(400, 44), os.path.join(GUI, "bar", "left.png"))
    save(make_bar(400, 44), os.path.join(GUI, "bar", "right.png"))
    save(make_bar(44, 400), os.path.join(GUI, "bar", "top.png"))
    save(make_bar(44, 400), os.path.join(GUI, "bar", "bottom.png"))

    save(make_frame(), os.path.join(GUI, "frame.png"))
    save(make_notify(), os.path.join(GUI, "notify.png"))
    save(make_skip(), os.path.join(GUI, "skip.png"))
    save(Image.new("RGBA", (1280, 720), rgba(NAVY0, 190)), os.path.join(GUI, "nvl.png"))
    save(make_menu_overlay(), os.path.join(GUI, "overlay", "main_menu.png"))
    save(make_game_menu_overlay(), os.path.join(GUI, "overlay", "game_menu.png"))
    save(make_confirm_overlay(), os.path.join(GUI, "overlay", "confirm.png"))

    save(make_main_menu_bg(), os.path.join(GUI, "main_menu.png"))
    save(make_game_menu_bg(), os.path.join(GUI, "game_menu.png"))

    save(make_beam(), os.path.join(GUI, "fx", "fx_beam.png"))
    save(make_fog(seed=5), os.path.join(GUI, "fx", "fx_fog_a.png"))
    save(make_fog(seed=19, strength=90, blobs=16), os.path.join(GUI, "fx", "fx_fog_b.png"))
    save(make_radial(), os.path.join(GUI, "fx", "fx_glow.png"))
    save(make_lamp(True), os.path.join(GUI, "lamp_on.png"))
    save(make_lamp(False), os.path.join(GUI, "lamp_off.png"))
    save(make_divider(), os.path.join(GUI, "divider.png"))
    save(make_letter_paper(), os.path.join(GUI, "letter_paper.png"))


if __name__ == "__main__":
    main()
