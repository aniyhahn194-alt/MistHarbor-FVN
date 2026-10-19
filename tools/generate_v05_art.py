#!/usr/bin/env python3
"""《雾港来信》V0.5 美术统一脚本（夜雾港口风格）。

仅为开发期工具，游戏运行时不依赖本脚本；生成结果已提交到 game/ 与项目根目录。
依赖：Pillow（pip install pillow）。**全部由代码绘制，不使用任何外部图片，没有使用图像生成模型。**

做三件事：
  1. 背景：重绘三张场景背景（栈桥 / 后巷 / 灯塔），统一为“夜雾港口”——深蓝、冷青为主，灯光暖金点亮。
  2. 立绘：对 generate_assets.py 绘制的原始立绘做一轮后期（柔化边缘、冷青边缘光 + 暖金灯光边缘光、
     统一配色、雾气色环境光、脚下投影、背光雾晕），降低“贴片感”。这仍然是程序化占位美术，不是专业手绘。
  3. 加载画面：`web-presplash.png`（Web 构建的加载画面）、`game/presplash.png`（桌面启动画面）、
     `game/gui/splash.png`（游戏内 splashscreen 标题画面）。

用法（顺序重要，后一步读取前一步的输出）：
    python3 tools/generate_assets.py     # V0.1 原始立绘 / 背景（本脚本会覆盖背景，立绘就地后期）
    python3 tools/generate_v05_art.py
    python3 tools/generate_ui.py         # 主菜单 / 游戏菜单底图读取 game/images/bg_*.png

注意：立绘后期是在“原始立绘”上做的，所以本脚本总是先在内存中调用 generate_assets.draw_wolf / draw_fox
重新绘制原始立绘，再后期，因此重复运行结果一致（不会叠加处理）。
"""
import math
import os
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import generate_assets as ga  # noqa: E402

IMG = os.path.join(ROOT, "game", "images")
GUI = os.path.join(ROOT, "game", "gui")
FONT = os.path.join(ROOT, "game", "fonts", "SourceHanSansLite.ttf")

# 夜雾港口色板（与 docs/V0.5-ART-UI-BRIEF.md 一致）
INK = (6, 12, 22)
NAVY0 = (8, 16, 26)
NAVY1 = (11, 22, 34)
NAVY2 = (17, 34, 51)
NAVY3 = (26, 52, 74)
TEAL_D = (24, 62, 78)
CYAN = (95, 184, 196)
FOG = (92, 128, 146)
GOLD = (243, 198, 119)
GOLD_L = (255, 232, 176)
EMBER = (232, 150, 70)


# ================================================================ 通用工具
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def vgrad(size, stops):
    """stops: [(t, color), ...]，t 从 0 到 1。"""
    w, h = size
    col = Image.new("RGB", (1, h))
    px = col.load()
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                px[0, y] = lerp(c0, c1, (t - t0) / max(1e-6, t1 - t0))
                break
    return col.resize(size)


def add_glow(img, center, radius, color, intensity=1.0, squash=1.0):
    """柔和的灯光晕（screen 叠加，不会把暗部洗灰）。"""
    w, h = img.size
    if radius >= 150:
        intensity *= 0.55
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    cx, cy = center
    d.ellipse([cx - radius, cy - radius * squash, cx + radius, cy + radius * squash], fill=255)
    layer = layer.filter(ImageFilter.GaussianBlur(radius / 2.0))
    layer = layer.point(lambda v: int(v * intensity))
    lit = Image.new("RGB", (w, h), color)
    lit = ImageChops.multiply(lit, Image.merge("RGB", (layer, layer, layer)))
    return ImageChops.screen(img, lit)


def fog_band(size, seed, color, strength=110, blobs=20, y0=0.35, y1=1.0, blur=0.035):
    rnd = random.Random(seed)
    w, h = size
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    for _ in range(blobs):
        cx, cy = rnd.randint(-w // 8, w + w // 8), rnd.randint(int(h * y0), int(h * y1))
        rx, ry = rnd.randint(w // 7, w // 3), rnd.randint(h // 24, h // 8)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=rnd.randint(30, strength))
    mask = mask.filter(ImageFilter.GaussianBlur(h * blur))
    return Image.composite(Image.new("RGB", size, color), Image.new("RGB", size, (0, 0, 0)), mask), mask


def add_fog(img, seed, color=FOG, **kw):
    solid, mask = fog_band(img.size, seed, color, **kw)
    return Image.composite(solid, img, mask)


def vignette(img, strength=0.6, color=INK):
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([-w * 0.22, -h * 0.30, w * 1.22, h * 1.30], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(min(w, h) // 5))
    inv = ImageChops.invert(mask).point(lambda v: int(v * strength))
    return Image.composite(Image.new("RGB", (w, h), color), img, inv)


def grain(img, amount=5, seed=1):
    """极轻的颗粒，掩盖 8 位暗部渐变的色带。"""
    rnd = random.Random(seed)
    w, h = img.size
    n = Image.effect_noise((w // 2, h // 2), amount * 4).resize((w, h))
    n = n.point(lambda v: int(128 + (v - 128) * 0.35))
    n = Image.merge("RGB", (n, n, n))
    return ImageChops.add(img, ImageChops.subtract(n, Image.new("RGB", (w, h), (128, 128, 128))), 1.0, 0)


def stars(img, seed, count, ymax, size_choices=(1, 1, 2)):
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(count):
        x, y = rnd.randint(0, img.width), rnd.randint(0, ymax)
        r = rnd.choice(size_choices)
        b = rnd.randint(150, 235)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(b - 14, b, min(255, b + 14)))
    return img


def light_streaks(img, x, y0, y1, color, seed, spread=60, count=26, alpha=150):
    """水面 / 湿地面上灯光的竖向倒影碎片。"""
    rnd = random.Random(seed)
    layer = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(count):
        t = i / count
        y = y0 + (y1 - y0) * t
        half = int(spread * (0.35 + 0.65 * t)) + rnd.randint(-6, 6)
        xo = int(math.sin(i * 1.7 + seed) * (6 + 14 * t))
        c = tuple(int(v * alpha / 255 * (1.0 - 0.55 * t)) for v in color)
        d.line([(x - half + xo, y), (x + half + xo, y)], fill=c, width=2 + int(3 * t))
    layer = layer.filter(ImageFilter.GaussianBlur(2.6))
    return ImageChops.screen(img, layer)


# ================================================================ 背景（1920x1080 绘制，保存时缩到 1280x720）
def bg_dock():
    """栈桥：深蓝夜空、冷青雾、远处灯塔与灯塔光束，两盏暖金路灯，湿木栈桥反光。"""
    W, H = 1920, 1080
    horizon = 610
    img = vgrad((W, H), [(0, (5, 10, 22)), (0.45, (16, 38, 58)), (0.568, (46, 86, 104)), (0.5681, (16, 40, 56)), (1.0, (6, 14, 24))])
    img = stars(img, 4, 70, 330)
    # 雾后的月亮
    img = add_glow(img, (900, 150), 260, (110, 170, 190), 0.55)
    d = ImageDraw.Draw(img)
    d.ellipse([872, 122, 928, 178], fill=(214, 232, 232))
    img = add_glow(img, (900, 150), 90, (160, 210, 220), 0.45)
    # 远山
    d = ImageDraw.Draw(img)
    d.polygon([(0, horizon), (0, 548), (240, 520), (520, 566), (760, horizon)], fill=(14, 34, 48))
    d.polygon([(1300, horizon), (1500, 560), (1760, 528), (1920, 548), (1920, horizon)], fill=(15, 35, 49))
    # 海面：渐变 + 月光倒影
    sea = vgrad((W, H - horizon), [(0, (28, 62, 80)), (0.5, (12, 32, 48)), (1, (6, 14, 24))])
    img.paste(sea, (0, horizon))
    img = light_streaks(img, 900, horizon + 20, horizon + 150, (120, 170, 180), 3, spread=40, count=14, alpha=120)
    # 灯塔（居中偏右，远景）与它的光束
    lx, ly = 1130, horizon
    d = ImageDraw.Draw(img)
    d.polygon([(lx - 22, ly), (lx - 10, ly - 190), (lx + 10, ly - 190), (lx + 22, ly)], fill=(40, 62, 78))
    d.rectangle([lx - 16, ly - 222, lx + 16, ly - 190], fill=(30, 48, 62))
    d.polygon([(lx - 20, ly - 222), (lx, ly - 246), (lx + 20, ly - 222)], fill=(24, 40, 54))
    beam = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(beam)
    bd.polygon([(lx, ly - 206), (lx - 1500, ly - 480), (lx - 1500, ly + 60)], fill=110)
    bd.polygon([(lx, ly - 206), (lx + 1100, ly - 380), (lx + 1100, ly - 40)], fill=60)
    beam = beam.filter(ImageFilter.GaussianBlur(26))
    img = ImageChops.screen(img, ImageChops.multiply(Image.new("RGB", (W, H), (110, 90, 48)), Image.merge("RGB", (beam, beam, beam))))
    img = add_glow(img, (lx, ly - 206), 170, GOLD, 0.95)
    d = ImageDraw.Draw(img)
    d.rectangle([lx - 11, ly - 216, lx + 11, ly - 198], fill=GOLD_L)
    img = light_streaks(img, lx, horizon + 14, horizon + 190, GOLD, 8, spread=26, count=18, alpha=150)
    # 货船剪影（带两扇暖窗）
    d = ImageDraw.Draw(img)
    d.polygon([(1420, horizon + 6), (1760, horizon + 6), (1722, horizon + 52), (1452, horizon + 52)], fill=(12, 26, 38))
    d.rectangle([1520, horizon - 44, 1610, horizon + 6], fill=(15, 32, 46))
    d.rectangle([1650, horizon - 80, 1662, horizon + 6], fill=(14, 30, 42))
    for wx in (1536, 1572):
        d.rectangle([wx, horizon - 28, wx + 14, horizon - 14], fill=(236, 180, 98))
    img = add_glow(img, (1556, horizon - 20), 70, EMBER, 0.45)
    # 海平线雾
    img = add_fog(img, 3, color=(70, 112, 130), strength=105, blobs=16, y0=0.50, y1=0.62, blur=0.03)

    # 木栈桥（近景）：深蓝黑木板，缝隙 + 湿润反光
    d = ImageDraw.Draw(img)
    deck_top = 742
    deck = vgrad((W, H - deck_top), [(0, (24, 28, 38)), (1, (8, 12, 20))])
    img.paste(deck, (0, deck_top))
    d = ImageDraw.Draw(img)
    for k in range(7):
        y0 = deck_top + 6 + int(k * k * 6.5 + k * 22)
        d.line([(0, y0), (W, y0 - 22 + k * 3)], fill=(6, 10, 16), width=2 + k // 2)
    for i in range(-6, 24):
        d.line([(i * 120 + 40, deck_top + 8), (i * 200 - 160, H)], fill=(7, 11, 17), width=2)
    # 栏杆
    d.rectangle([0, 700, W, 716], fill=(14, 24, 34))
    d.rectangle([0, 716, W, 722], fill=(6, 12, 20))
    for x in range(30, W, 230):
        d.rectangle([x, 648, x + 16, 722], fill=(14, 24, 34))
    # 缆桩与缆绳圈（中景，位于两侧角色之间的空地外侧）
    for bx, by in ((850, 880), (1480, 904)):
        d.rectangle([bx, by - 62, bx + 34, by], fill=(10, 16, 24))
        d.ellipse([bx - 8, by - 82, bx + 42, by - 54], fill=(18, 28, 38))
    # 路灯：两盏，立在两个角色之间的空地两侧，给角色的内侧打暖光
    lamps = [(660, 420, 1.0), (1290, 452, 0.9)]
    for px, py, s in lamps:
        d = ImageDraw.Draw(img)
        d.rectangle([px, py, px + 13, 716], fill=(8, 14, 22))
        d.rectangle([px - 24, py - 26, px + 37, py + 4], fill=(8, 14, 22))
        d.polygon([(px - 26, py - 26), (px + 6, py - 50), (px + 39, py - 26)], fill=(8, 14, 22))
        img = add_glow(img, (px + 6, py + 20), 300 * s, (240, 176, 92), 0.95)
        img = add_glow(img, (px + 6, py + 20), 90 * s, GOLD_L, 0.8)
        d = ImageDraw.Draw(img)
        d.rectangle([px - 2, py - 2, px + 15, py + 22], fill=GOLD_L)
        # 灯光落在木板上
        img = add_glow(img, (px + 6, 860), 260 * s, (214, 150, 76), 0.40, squash=0.30)
        img = add_glow(img, (px + 6, 930), 110 * s, (214, 150, 76), 0.45, squash=2.2)
    # 近景雾
    img = add_fog(img, 11, color=(58, 96, 114), strength=90, blobs=16, y0=0.55, y1=0.95)
    # 前景剪影：右下 / 左下的缆绳桶与箱（半透明深色，压住画面下沿，增加层次）
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1000, W, H], fill=(4, 8, 14))
    img = vignette(img, 0.7)
    return img


def bg_alley():
    """后巷：冷青蓝砖墙、中央木门漏出暖光、一盏暖金吊灯、湿石板反光。"""
    W, H = 1920, 1080
    img = vgrad((W, H), [(0, (6, 12, 24)), (0.6, (14, 28, 42)), (1, (8, 14, 24))])
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    # 左右砖墙：深蓝灰砖，带轻微随机明暗
    for (x0, x1) in ((0, 560), (1360, W)):
        d.rectangle([x0, 0, x1, 820], fill=(30, 36, 48))
        for row in range(0, 820, 36):
            off = 0 if (row // 36) % 2 == 0 else 40
            for x in range(x0 - 80 + off, x1, 80):
                s = rnd.randint(-7, 7)
                d.rectangle([x + 2, row + 2, x + 76, row + 33], fill=(38 + s, 46 + s, 60 + s))
    # 墙顶外檐与细管道
    d.rectangle([0, 0, 560, 26], fill=(10, 16, 26))
    d.rectangle([1360, 0, W, 26], fill=(10, 16, 26))
    d.rectangle([488, 0, 506, 820], fill=(16, 26, 36))
    d.rectangle([1420, 0, 1436, 820], fill=(16, 26, 36))
    for y in (200, 520):
        d.rectangle([482, y, 512, y + 12], fill=(24, 38, 50))
        d.rectangle([1414, y, 1442, y + 12], fill=(24, 38, 50))
    # 中央远墙、台阶、木门
    d.rectangle([560, 150, 1360, 820], fill=(18, 30, 44))
    d.rectangle([560, 150, 1360, 190], fill=(12, 22, 34))
    d.rectangle([840, 360, 1080, 820], fill=(22, 18, 20))
    d.rectangle([860, 380, 1060, 820], fill=(40, 30, 28))
    for x in range(860, 1060, 33):
        d.line([(x, 380), (x, 820)], fill=(24, 18, 18), width=3)
    d.ellipse([1020, 600, 1036, 616], fill=(212, 170, 92))
    # 招牌：带锚的信封
    d.rectangle([870, 290, 1050, 346], fill=(10, 18, 28))
    d.rectangle([890, 304, 1030, 332], outline=(206, 178, 120), width=3)
    d.line([(890, 304), (960, 324), (1030, 304)], fill=(206, 178, 120), width=3)
    # 门缝暖光
    door = Image.new("L", (W, H), 0)
    dd = ImageDraw.Draw(door)
    dd.rectangle([858, 770, 1062, 822], fill=190)
    dd.rectangle([940, 380, 980, 822], fill=0)
    door = door.filter(ImageFilter.GaussianBlur(22))
    img = ImageChops.screen(img, ImageChops.multiply(Image.new("RGB", (W, H), (190, 120, 50)), Image.merge("RGB", (door, door, door))))
    # 两侧小窗：暖光透出
    for wx, wy in ((250, 100), (700, 270), (1700, 100)):
        d = ImageDraw.Draw(img)
        d.rectangle([wx - 44, wy - 60, wx + 44, wy + 60], fill=(10, 16, 24))
        d.rectangle([wx - 36, wy - 52, wx + 36, wy + 52], fill=(196, 134, 66))
        d.line([(wx, wy - 52), (wx, wy + 52)], fill=(10, 16, 24), width=4)
        d.line([(wx - 36, wy), (wx + 36, wy)], fill=(10, 16, 24), width=4)
        img = add_glow(img, (wx, wy), 170, (220, 140, 60), 0.45)
    # 石板路
    d = ImageDraw.Draw(img)
    d.polygon([(0, 820), (W, 820), (W, H), (0, H)], fill=(12, 20, 30))
    for i in range(10):
        y = 820 + i * i * 3 + i * 10
        d.line([(0, y), (W, y)], fill=(8, 14, 22), width=3)
    for i in range(-10, 30):
        d.line([(960 + (i - 10) * 30, 820), (960 + (i - 10) * 160, H)], fill=(8, 14, 22), width=3)
    # 吊灯（左中，靠近门；暖金）+ 地面水渍反光
    d.line([(1180, 0), (1180, 236)], fill=(8, 12, 18), width=4)
    d.polygon([(1150, 236), (1210, 236), (1198, 290), (1162, 290)], fill=(10, 16, 24))
    img = add_glow(img, (1180, 270), 360, (238, 160, 76), 0.95)
    img = add_glow(img, (1180, 270), 100, GOLD_L, 0.8)
    d = ImageDraw.Draw(img)
    d.rectangle([1166, 244, 1194, 282], fill=GOLD_L)
    img = add_glow(img, (1180, 930), 380, (190, 126, 60), 0.35, squash=0.22)
    img = add_glow(img, (1180, 960), 120, (214, 150, 76), 0.45, squash=2.0)
    img = add_glow(img, (960, 880), 140, (190, 120, 50), 0.30, squash=0.8)
    # 木桶与木箱（门两侧中景）
    d = ImageDraw.Draw(img)
    for bx in (700, 1160):
        d.rounded_rectangle([bx, 720, bx + 90, 822], radius=12, fill=(22, 24, 30))
        d.line([(bx, 750), (bx + 90, 750)], fill=(12, 14, 20), width=4)
        d.line([(bx, 790), (bx + 90, 790)], fill=(12, 14, 20), width=4)
    img = add_fog(img, 21, color=(52, 88, 106), strength=95, blobs=20, y0=0.4, y1=1.0)
    img = vignette(img, 0.75)
    return img


def bg_lighthouse():
    """灯塔下的守望台：深蓝夜空与星、冷青雾、塔顶暖金灯与光束、海面灯光倒影。"""
    W, H = 1920, 1080
    img = vgrad((W, H), [(0, (4, 8, 20)), (0.5, (14, 34, 56)), (0.59, (38, 78, 98)), (0.5901, (14, 36, 54)), (1, (5, 12, 22))])
    img = stars(img, 5, 150, 440, (1, 1, 2, 2, 3))
    # 月亮（左）与月晕
    img = add_glow(img, (900, 150), 240, (110, 170, 190), 0.5)
    d = ImageDraw.Draw(img)
    d.ellipse([864, 114, 936, 186], fill=(222, 236, 234))
    img = add_glow(img, (900, 150), 80, (170, 214, 220), 0.4)
    horizon = 640
    sea = vgrad((W, H - horizon), [(0, (24, 56, 76)), (0.4, (10, 28, 44)), (1, (5, 12, 22))])
    img.paste(sea, (0, horizon))
    img = light_streaks(img, 900, horizon + 10, horizon + 250, (120, 170, 180), 5, spread=60, count=22, alpha=130)
    # 灯塔（右侧，主视觉）
    tx = 1200
    d = ImageDraw.Draw(img)
    d.polygon([(tx - 140, 900), (tx - 60, 290), (tx + 60, 290), (tx + 140, 900)], fill=(52, 72, 90))
    for k in range(4):
        y0 = 370 + k * 130
        a = (118, 66, 66) if k % 2 == 0 else (60, 84, 102)
        d.polygon([(tx - 78 - k * 6, y0), (tx + 78 + k * 6, y0), (tx + 72 + k * 6, y0 + 56), (tx - 72 - k * 6, y0 + 56)], fill=a)
    d.rectangle([tx - 80, 224, tx + 80, 290], fill=(18, 30, 44))
    d.polygon([(tx - 90, 226), (tx, 150), (tx + 90, 226)], fill=(14, 26, 40))
    # 光束：向左扫过海面
    beam = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(beam)
    bd.polygon([(tx, 254), (0, 130), (0, 430)], fill=120)
    bd.polygon([(tx, 254), (W, 190), (W, 330)], fill=50)
    beam = beam.filter(ImageFilter.GaussianBlur(30))
    img = ImageChops.screen(img, ImageChops.multiply(Image.new("RGB", (W, H), (120, 98, 52)), Image.merge("RGB", (beam, beam, beam))))
    # 塔身受光（右侧偏暖，左侧偏冷）
    glow_tower = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow_tower)
    gd.polygon([(tx - 20, 290), (tx + 60, 290), (tx + 140, 900), (tx + 10, 900)], fill=50)
    glow_tower = glow_tower.filter(ImageFilter.GaussianBlur(24))
    img = ImageChops.screen(img, ImageChops.multiply(Image.new("RGB", (W, H), (170, 120, 60)), Image.merge("RGB", (glow_tower, glow_tower, glow_tower))))
    img = add_glow(img, (tx, 254), 300, GOLD, 0.95)
    img = add_glow(img, (tx, 254), 90, GOLD_L, 0.9)
    d = ImageDraw.Draw(img)
    d.rectangle([tx - 44, 232, tx + 44, 274], fill=GOLD_L)
    img = light_streaks(img, 1180, horizon + 10, horizon + 260, GOLD, 9, spread=80, count=22, alpha=130)
    # 守望台地面与栏杆
    d = ImageDraw.Draw(img)
    d.polygon([(0, 820), (W, 820), (W, H), (0, H)], fill=(12, 20, 32))
    for i in range(0, W, 110):
        d.line([(i, 820), (i - 100, H)], fill=(7, 13, 22), width=3)
    d.rectangle([0, 770, W, 786], fill=(12, 22, 34))
    for x in range(30, W, 200):
        d.rectangle([x, 716, x + 14, 786], fill=(12, 22, 34))
    # 栏杆上一盏小灯（暖金，位于左右角色之间），灯光洒在地面
    for gx in (500,):
        d.line([(gx, 640), (gx, 716)], fill=(8, 14, 22), width=5)
        d.rectangle([gx - 16, 670, gx + 16, 706], fill=(8, 14, 22))
        img = add_glow(img, (gx, 690), 220, (238, 168, 84), 0.9)
        img = add_glow(img, (gx, 690), 60, GOLD_L, 0.8)
        d = ImageDraw.Draw(img)
        d.rectangle([gx - 9, 678, gx + 9, 700], fill=GOLD_L)
        img = add_glow(img, (gx, 900), 240, (200, 140, 70), 0.30, squash=0.28)
    img = add_fog(img, 31, color=(66, 108, 128), strength=88, blobs=18, y0=0.45, y1=1.0)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1000, W, H], fill=(4, 8, 14))
    img = vignette(img, 0.7)
    return img


# ================================================================ 立绘后期
PAD_X, PAD_TOP, PAD_BOTTOM = 40, 30, 70


def feather(alpha, r=1.0):
    return alpha.filter(ImageFilter.GaussianBlur(r))


def stylize_sprite(src, warm_side):
    """src: 640x1040 RGBA 原始立绘。warm_side: 'left' / 'right'，朝向画面中央（灯光方向）的一侧。"""
    src = src.convert("RGBA")
    w, h = src.size
    W, H = w + PAD_X * 2, h + PAD_TOP + PAD_BOTTOM
    canvas_rgb = Image.new("RGB", (W, H), (0, 0, 0))
    rgb = Image.new("RGB", (W, H), (0, 0, 0))
    a = Image.new("L", (W, H), 0)
    rgb.paste(src.convert("RGB"), (PAD_X, PAD_TOP))
    a.paste(src.split()[3], (PAD_X, PAD_TOP))

    # 1. 统一配色：降饱和，叠冷青蓝色罩，整体略压暗
    rgb = ImageEnhance.Color(rgb).enhance(0.92)
    cool = ImageChops.multiply(rgb, Image.new("RGB", (W, H), (150, 184, 214)))
    rgb = Image.blend(rgb, cool, 0.34)
    rgb = ImageEnhance.Brightness(rgb).enhance(1.02)
    # 2. 雾气色环境光：越靠近脚下越被冷青雾吞没
    fogc = vgrad((W, H), [(0, (0, 0, 0)), (0.62, (0, 0, 0)), (1.0, (255, 255, 255))])
    fog_solid = Image.new("RGB", (W, H), (46, 86, 104))
    rgb = Image.composite(Image.blend(rgb, fog_solid, 0.55), rgb, fogc.convert("L"))
    # 3. 暖金灯光：从朝向灯光的一侧打来，叠 screen
    hgrad = Image.new("L", (W, 1))
    for x in range(W):
        t = x / (W - 1)
        t = t if warm_side == "right" else 1 - t
        hgrad.putpixel((x, 0), int(255 * max(0.0, (t - 0.45) / 0.55) ** 1.4))
    warm_mask = hgrad.resize((W, H))
    vfall = vgrad((W, H), [(0, (255, 255, 255)), (0.7, (190, 190, 190)), (1, (70, 70, 70))]).convert("L")
    warm_mask = ImageChops.multiply(warm_mask, vfall).point(lambda v: int(v * 0.30))
    warm = ImageChops.multiply(Image.new("RGB", (W, H), (255, 190, 100)), Image.merge("RGB", (warm_mask,) * 3))
    rgb = ImageChops.screen(rgb, warm)

    # 4. 软化边缘：轻微羽化 alpha，并把硬描边的深色压向深海蓝
    a_soft = feather(a, 1.1)
    a_soft = a_soft.point(lambda v: min(255, int(v * 1.12)))
    rgb = rgb  # 描边色已在配色中被压成深蓝

    # 5. 边缘光：左上冷青、朝灯一侧暖金（只画在轮廓内侧窄带）
    def rim(dx, dy, blur):
        band = ImageChops.subtract(a_soft, ImageChops.offset(a_soft, dx, dy))
        band = band.filter(ImageFilter.GaussianBlur(blur))
        return ImageChops.multiply(band, a_soft)

    cool_dx = 6 if warm_side == "right" else -6
    cool_rim = rim(cool_dx, 5, 1.8).point(lambda v: min(255, int(v * 1.0)))
    warm_rim = rim(-7 if warm_side == "right" else 7, 3, 1.6).point(lambda v: min(255, int(v * 1.1)))
    rgb = ImageChops.screen(rgb, ImageChops.multiply(Image.new("RGB", (W, H), (104, 200, 212)), Image.merge("RGB", (cool_rim.point(lambda v: int(v * 0.50)),) * 3)))
    rgb = ImageChops.screen(rgb, ImageChops.multiply(Image.new("RGB", (W, H), (255, 204, 120)), Image.merge("RGB", (warm_rim.point(lambda v: int(v * 0.75)),) * 3)))

    body = Image.merge("RGBA", (*rgb.split(), a_soft))

    # 6. 背光雾晕（贴着轮廓外侧一圈冷青微光）+ 脚下投影
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    halo_a = a.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.30))
    halo = Image.new("RGBA", (W, H), (70, 140, 156, 0))
    halo.putalpha(halo_a)
    out.alpha_composite(halo)
    sh = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sh)
    foot_y = PAD_TOP + 1004
    cx = W // 2
    sd.ellipse([cx - 210, foot_y - 20, cx + 210, foot_y + 34], fill=190)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    shadow = Image.new("RGBA", (W, H), (2, 6, 12, 0))
    shadow.putalpha(sh)
    out.alpha_composite(shadow)
    out.alpha_composite(body)
    return out


def sprite_set():
    # 灰舟站左侧（暖光来自右侧 / 画面中央），林岚站右侧（暖光来自左侧）
    return [
        ("huizhou_normal.png", ga.draw_wolf("normal"), "right"),
        ("huizhou_worried.png", ga.draw_wolf("worried"), "right"),
        ("linlan_normal.png", ga.draw_fox("normal"), "left"),
        ("linlan_smile.png", ga.draw_fox("smile"), "left"),
    ]


# ================================================================ 加载 / 标题画面
def text_with_glow(img, xy, text, size, fill, glow_color, glow_radius=14, anchor="mm", spacing=0):
    font = ImageFont.truetype(FONT, size)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, text, font=font, fill=glow_color + (255,), anchor=anchor)
    layer = layer.filter(ImageFilter.GaussianBlur(glow_radius))
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img)
    d.text((xy[0], xy[1] + 2), text, font=font, fill=(2, 6, 12, 200), anchor=anchor)
    d.text(xy, text, font=font, fill=fill + (255,), anchor=anchor)


def spaced_text(img, cx, y, text, size, fill, spacing):
    font = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(img)
    widths = [d.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2
    for ch, wd in zip(text, widths):
        d.text((x, y), ch, font=font, fill=fill + (255,), anchor="lm")
        x += wd + spacing


def splash_art(W=1920, H=1080):
    """加载 / 标题画面：夜雾港口远景 + 灯塔光束 + 居中标题。W:H 必须为 16:9。"""
    img = vgrad((W, H), [(0, (4, 8, 18)), (0.5, (12, 30, 48)), (0.66, (30, 62, 80)), (0.661, (10, 26, 40)), (1, (4, 9, 16))])
    img = stars(img, 12, 130, int(H * 0.45), (1, 1, 2, 2))
    horizon = int(H * 0.66)
    cx = W // 2
    # 海面倒影
    img = light_streaks(img, cx, horizon + 8, horizon + int(H * 0.2), GOLD, 3, spread=60, count=24, alpha=150)
    img = add_glow(img, (cx, int(H * 0.60)), int(H * 0.5), (50, 100, 120), 0.35, squash=0.7)
    # 灯塔（居中、远景，位于标题下方）
    ty = horizon
    d = ImageDraw.Draw(img)
    th = int(H * 0.30)
    d.polygon([(cx - 34, ty), (cx - 14, ty - th), (cx + 14, ty - th), (cx + 34, ty)], fill=(34, 56, 72))
    d.rectangle([cx - 24, ty - th - 34, cx + 24, ty - th], fill=(22, 38, 52))
    d.polygon([(cx - 30, ty - th - 34), (cx, ty - th - 64), (cx + 30, ty - th - 34)], fill=(18, 32, 46))
    for k in range(2):
        yy = ty - th + 40 + k * 90
        d.polygon([(cx - 22 - k * 3, yy), (cx + 22 + k * 3, yy), (cx + 20 + k * 3, yy + 22), (cx - 20 - k * 3, yy + 22)], fill=(84, 52, 56))
    lamp = (cx, ty - th - 16)
    beam = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(beam)
    bd.polygon([lamp, (0, lamp[1] - int(H * 0.2)), (0, lamp[1] + int(H * 0.16))], fill=110)
    bd.polygon([lamp, (W, lamp[1] - int(H * 0.12)), (W, lamp[1] + int(H * 0.10))], fill=70)
    beam = beam.filter(ImageFilter.GaussianBlur(32))
    img = ImageChops.screen(img, ImageChops.multiply(Image.new("RGB", (W, H), (120, 98, 52)), Image.merge("RGB", (beam,) * 3)))
    img = add_glow(img, lamp, int(H * 0.26), GOLD, 0.95)
    img = add_glow(img, lamp, int(H * 0.07), GOLD_L, 0.95)
    # 远山与两侧港口剪影
    d = ImageDraw.Draw(img)
    d.polygon([(0, horizon), (0, horizon - 90), (260, horizon - 120), (520, horizon - 50), (700, horizon)], fill=(10, 24, 36))
    d.polygon([(W, horizon), (W, horizon - 100), (W - 300, horizon - 110), (W - 560, horizon - 40), (W - 720, horizon)], fill=(10, 24, 36))
    # 栈桥与两盏路灯（框住构图）
    d.rectangle([0, int(H * 0.86), W, H], fill=(6, 12, 20))
    d.rectangle([0, int(H * 0.835), W, int(H * 0.855)], fill=(12, 22, 32))
    for lx in (int(W * 0.14), int(W * 0.86)):
        d.rectangle([lx, int(H * 0.52), lx + 12, int(H * 0.84)], fill=(8, 14, 22))
        d.rectangle([lx - 20, int(H * 0.50), lx + 32, int(H * 0.52)], fill=(8, 14, 22))
        img = add_glow(img, (lx + 6, int(H * 0.545)), int(H * 0.2), (238, 168, 84), 0.9)
        img = add_glow(img, (lx + 6, int(H * 0.545)), int(H * 0.05), GOLD_L, 0.85)
        d = ImageDraw.Draw(img)
        d.rectangle([lx - 2, int(H * 0.527), lx + 14, int(H * 0.552)], fill=GOLD_L)
    img = add_fog(img, 41, color=(54, 92, 110), strength=100, blobs=16, y0=0.55, y1=0.92)
    img = vignette(img, 0.8)
    img = img.convert("RGBA")
    # 标题
    s = H / 1080.0
    text_with_glow(img, (cx, int(H * 0.30)), "雾港来信", int(190 * s), (246, 214, 144), (240, 170, 70), glow_radius=int(26 * s))
    spaced_text(img, cx, int(H * 0.435), "LETTERS FROM MIST HARBOR", int(34 * s), (140, 206, 214), int(9 * s))
    d = ImageDraw.Draw(img)
    ly = int(H * 0.485)
    d.line([(cx - int(150 * s), ly), (cx + int(150 * s), ly)], fill=(95, 184, 196, 150), width=max(1, int(2 * s)))
    d.ellipse([cx - 5 * s, ly - 5 * s, cx + 5 * s, ly + 5 * s], fill=(255, 226, 160, 255))
    return img.convert("RGB")


def splash_with_loading(W, H, hint):
    img = splash_art(W, H).convert("RGBA")
    s = H / 1080.0
    spaced_text(img, W // 2, int(H * 0.93), hint, int(26 * s), (126, 160, 176), int(6 * s))
    return img.convert("RGB")


# ================================================================ 输出
def save_png(img, path, optimize=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=optimize)
    print("wrote", os.path.relpath(path, ROOT), img.size)


def finish_bg(img, seed):
    img = grain(img, 3, seed)
    return img.resize((1280, 720), Image.LANCZOS)


def main():
    save_png(finish_bg(bg_dock(), 1), os.path.join(IMG, "bg_dock.png"))
    save_png(finish_bg(bg_alley(), 2), os.path.join(IMG, "bg_alley.png"))
    save_png(finish_bg(bg_lighthouse(), 3), os.path.join(IMG, "bg_lighthouse.png"))
    for name, raw, side in sprite_set():
        save_png(stylize_sprite(raw, side), os.path.join(IMG, name))
    # 加载 / 启动画面
    art = splash_with_loading(1920, 1080, "正在启程  LOADING")
    save_png(art.resize((1600, 900), Image.LANCZOS), os.path.join(ROOT, "web-presplash.png"))
    save_png(splash_with_loading(960, 540, "LOADING").convert("RGB"), os.path.join(ROOT, "game", "presplash.png"))
    save_png(splash_art(1920, 1080).resize((1280, 720), Image.LANCZOS), os.path.join(GUI, "splash.png"))


if __name__ == "__main__":
    main()
