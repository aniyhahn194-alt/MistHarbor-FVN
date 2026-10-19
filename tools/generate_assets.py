#!/usr/bin/env python3
"""生成《雾港来信》V0.1 的原创占位素材（角色立绘、背景、主菜单图）。

仅为开发期工具，游戏运行时不依赖本脚本；生成结果已提交到 game/ 目录。
依赖：Pillow（pip install pillow）。用法：python3 tools/generate_assets.py
所有图形均由代码绘制，不使用任何外部图片。
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "game", "images")
GUI_DIR = os.path.join(ROOT, "game", "gui")

SS = 2  # 超采样倍数，缩小后边缘更平滑


# ---------------------------------------------------------------- 工具函数
def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def vgradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=lerp(top, bottom, y / max(1, h - 1)))
    return img


def fog_layer(size, seed, color=(205, 215, 222), strength=110, blobs=26):
    """随机椭圆 + 高斯模糊，叠出雾气。"""
    rnd = random.Random(seed)
    w, h = size
    layer = Image.new("L", size, 0)
    d = ImageDraw.Draw(layer)
    for _ in range(blobs):
        cx, cy = rnd.randint(0, w), rnd.randint(int(h * 0.3), h)
        rx, ry = rnd.randint(w // 8, w // 3), rnd.randint(h // 20, h // 8)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=rnd.randint(40, strength))
    layer = layer.filter(ImageFilter.GaussianBlur(h // 28))
    solid = Image.new("RGB", size, color)
    return solid, layer


def add_fog(img, seed, **kw):
    solid, mask = fog_layer(img.size, seed, **kw)
    return Image.composite(solid, img, mask)


def glow(img, center, radius, color, intensity=1.0):
    """在 center 处叠加暖色光晕（灯笼 / 路灯）。"""
    w, h = img.size
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    d.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], fill=255)
    layer = layer.filter(ImageFilter.GaussianBlur(radius / 2.2))
    layer = layer.point(lambda v: int(v * intensity))
    return Image.composite(Image.new("RGB", (w, h), color), img, layer)


# ---------------------------------------------------------------- 背景
def make_bg_dock():
    """港口栈桥：黄昏、浓雾、远处灯塔与货船。"""
    W, H = 1920, 1080
    img = vgradient((W, H), (88, 108, 128), (176, 188, 190))
    d = ImageDraw.Draw(img)
    horizon = 600
    # 海面
    sea = vgradient((W, H - horizon), (96, 120, 134), (46, 66, 82))
    img.paste(sea, (0, horizon))
    d = ImageDraw.Draw(img)
    # 远处山影与灯塔
    d.polygon([(0, horizon), (260, 520), (520, 570), (760, horizon)], fill=(112, 130, 144))
    d.polygon([(1100, horizon), (1400, 540), (1700, 575), (1920, 530), (1920, horizon)], fill=(108, 126, 140))
    d.polygon([(1480, 540), (1500, 330), (1540, 330), (1560, 540)], fill=(124, 138, 150))
    d.rectangle([1488, 300, 1552, 335], fill=(140, 150, 156))
    d.polygon([(1486, 300), (1520, 270), (1554, 300)], fill=(98, 112, 124))
    img = glow(img, (1520, 318), 150, (255, 226, 160), 0.85)
    # 远处货船剪影
    d = ImageDraw.Draw(img)
    d.polygon([(300, 640), (700, 640), (660, 690), (340, 690)], fill=(70, 86, 100))
    d.rectangle([420, 590, 520, 640], fill=(80, 96, 110))
    d.rectangle([560, 560, 574, 640], fill=(76, 92, 106))
    img = add_fog(img, 3, strength=120, blobs=22)
    d = ImageDraw.Draw(img)
    # 海面高光
    for i in range(40):
        y = horizon + 25 + i * 9
        x = 1380 + int(math.sin(i * 1.3) * 60)
        d.line([(x - 90 + i, y), (x + 90 - i, y)], fill=(210, 205, 170), width=2)
    # 木栈桥（近景）
    d.polygon([(0, 760), (W, 700), (W, H), (0, H)], fill=(72, 56, 46))
    for i in range(0, W + 120, 120):
        d.line([(i, 740 - i * 0.03 + 20), (i - 160, H)], fill=(48, 36, 30), width=4)
    for k in range(5):
        y0 = 770 + k * 62
        d.line([(0, y0 + 6 - k * 3), (W, y0 - 56 + k * 3)], fill=(54, 42, 34), width=3)
    # 栏杆与缆桩
    d.rectangle([0, 690, W, 706], fill=(58, 46, 40))
    for x in range(40, W, 240):
        d.rectangle([x, 640, x + 16, 706], fill=(58, 46, 40))
    for x, y in ((300, 850), (1550, 880)):
        d.rectangle([x, y - 70, x + 34, y], fill=(40, 32, 30))
        d.ellipse([x - 8, y - 88, x + 42, y - 62], fill=(52, 42, 38))
    # 路灯
    for lx in (420, 1180):
        d.rectangle([lx, 420, lx + 12, 700], fill=(36, 40, 46))
        d.rectangle([lx - 22, 396, lx + 34, 424], fill=(36, 40, 46))
        img = glow(img, (lx + 6, 440), 190, (255, 214, 140), 0.8)
        d = ImageDraw.Draw(img)
        d.ellipse([lx - 6, 426, lx + 18, 452], fill=(255, 238, 190))
    img = add_fog(img, 11, strength=95, blobs=18)
    return img


def make_bg_alley():
    """旧仓库后巷：砖墙、木门、一盏昏黄的灯、湿漉漉的石板路。"""
    W, H = 1920, 1080
    img = vgradient((W, H), (34, 40, 54), (62, 66, 74))
    d = ImageDraw.Draw(img)
    rnd = random.Random(7)
    # 左右砖墙
    for (x0, x1) in ((0, 560), (1360, W)):
        d.rectangle([x0, 0, x1, 820], fill=(78, 58, 54))
        for row in range(0, 820, 36):
            off = 0 if (row // 36) % 2 == 0 else 40
            for x in range(x0 - 80 + off, x1, 80):
                shade = rnd.randint(-10, 10)
                d.rectangle([x + 2, row + 2, x + 76, row + 33], fill=(88 + shade, 62 + shade, 56 + shade))
    # 中央远处的墙与门
    d.rectangle([560, 160, 1360, 820], fill=(52, 58, 70))
    d.rectangle([860, 380, 1060, 820], fill=(66, 46, 36))
    d.rectangle([880, 400, 1040, 820], fill=(80, 56, 42))
    for x in range(880, 1040, 32):
        d.line([(x, 400), (x, 820)], fill=(58, 40, 32), width=3)
    d.ellipse([1010, 610, 1026, 626], fill=(200, 170, 90))
    # 门上方旧招牌：一只带锚的信封
    d.rectangle([880, 300, 1040, 360], fill=(40, 46, 54))
    d.rectangle([900, 314, 1020, 346], outline=(190, 176, 140), width=3)
    d.line([(900, 314), (960, 335), (1020, 314)], fill=(190, 176, 140), width=3)
    # 石板路
    d.polygon([(0, 820), (W, 820), (W, H), (0, H)], fill=(58, 60, 66))
    for i in range(10):
        y = 820 + i * i * 3 + i * 10
        d.line([(0, y), (W, y)], fill=(44, 46, 52), width=3)
    for i in range(-10, 30):
        d.line([(960 + (i - 10) * 30, 820), (960 + (i - 10) * 160, H)], fill=(44, 46, 52), width=3)
    # 水渍反光
    d.ellipse([660, 900, 1260, 1000], fill=(74, 80, 92))
    # 挂灯
    d.line([(1500, 0), (1500, 230)], fill=(30, 30, 34), width=4)
    d.rectangle([1478, 230, 1522, 290], fill=(50, 44, 36))
    img = glow(img, (1500, 262), 300, (255, 190, 110), 0.9)
    d = ImageDraw.Draw(img)
    d.rectangle([1486, 240, 1514, 282], fill=(255, 226, 160))
    img = add_fog(img, 21, color=(160, 172, 186), strength=90, blobs=22)
    return img


def make_bg_lighthouse():
    """灯塔下的守望台：夜晚、雾散开一些、海面有微光。"""
    W, H = 1920, 1080
    img = vgradient((W, H), (14, 22, 44), (74, 96, 120))
    d = ImageDraw.Draw(img)
    rnd = random.Random(5)
    for _ in range(130):
        x, y = rnd.randint(0, W), rnd.randint(0, 420)
        r = rnd.choice((1, 1, 2, 2, 3))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 240, 255))
    d.ellipse([260, 110, 340, 190], fill=(244, 244, 230))
    horizon = 640
    sea = vgradient((W, H - horizon), (40, 62, 90), (16, 28, 46))
    img.paste(sea, (0, horizon))
    d = ImageDraw.Draw(img)
    for i in range(36):
        y = horizon + 20 + i * 11
        d.line([(300 - i * 2, y), (300 + 80 + i * 4, y)], fill=(180, 190, 190), width=2)
    # 灯塔
    d.polygon([(1200, 900), (1280, 280), (1400, 280), (1480, 900)], fill=(200, 200, 206))
    for k in range(4):
        y0 = 360 + k * 130
        d.polygon([(1262 - k * 6, y0), (1418 + k * 6, y0), (1412 + k * 6, y0 + 56), (1268 - k * 6, y0 + 56)], fill=(168, 60, 60))
    d.rectangle([1260, 220, 1420, 282], fill=(60, 70, 84))
    d.polygon([(1250, 222), (1340, 150), (1430, 222)], fill=(70, 80, 96))
    img = glow(img, (1340, 252), 230, (255, 236, 170), 0.95)
    d = ImageDraw.Draw(img)
    d.rectangle([1296, 232, 1384, 272], fill=(255, 246, 200))
    # 守望台地面与栏杆
    d.polygon([(0, 820), (W, 820), (W, H), (0, H)], fill=(52, 56, 66))
    for i in range(0, W, 110):
        d.line([(i, 820), (i - 200 + 100, H)], fill=(40, 44, 52), width=3)
    d.rectangle([0, 770, W, 786], fill=(36, 40, 50))
    for x in range(30, W, 200):
        d.rectangle([x, 720, x + 14, 786], fill=(36, 40, 50))
    img = add_fog(img, 31, color=(150, 168, 190), strength=70, blobs=14)
    return img


# ---------------------------------------------------------------- 角色
class Painter:
    """在 SS 倍画布上用 1x 坐标作画的小封装。"""

    def __init__(self, w, h):
        self.size = (w, h)
        self.img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def _s(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def poly(self, pts, fill, outline=None):
        self.d.polygon(self._s(pts), fill=fill, outline=outline)

    def ell(self, box, fill, outline=None, width=1):
        x0, y0, x1, y1 = box
        self.d.ellipse([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill, outline=outline, width=width * SS)

    def rect(self, box, fill, radius=0):
        x0, y0, x1, y1 = box
        b = [x0 * SS, y0 * SS, x1 * SS, y1 * SS]
        if radius:
            self.d.rounded_rectangle(b, radius=radius * SS, fill=fill)
        else:
            self.d.rectangle(b, fill=fill)

    def line(self, pts, fill, width=2):
        self.d.line(self._s(pts), fill=fill, width=width * SS, joint="curve")

    def arc(self, box, start, end, fill, width=3):
        x0, y0, x1, y1 = box
        self.d.arc([x0 * SS, y0 * SS, x1 * SS, y1 * SS], start, end, fill=fill, width=width * SS)

    def result(self):
        out = self.img.resize(self.size, Image.LANCZOS)
        # 加一圈深色描边，让立绘在各种背景上更清晰
        alpha = out.split()[3]
        edge = alpha.filter(ImageFilter.MaxFilter(5))
        outline = Image.new("RGBA", out.size, (24, 28, 36, 0))
        outline.putalpha(edge)
        outline.alpha_composite(out)
        return outline


INK = (28, 30, 38)


def draw_wolf(expression="normal"):
    """灰舟：灰色狼族信使，深蓝信使外套、斜挎邮包、围巾。"""
    p = Painter(640, 1040)
    fur, fur_dk, fur_lt = (128, 136, 150), (92, 98, 112), (206, 212, 220)
    coat, coat_dk, trim = (44, 70, 110), (30, 50, 84), (214, 176, 84)
    cx = 320
    # 尾巴（在身体后面）
    p.poly([(cx + 70, 700), (cx + 230, 720), (cx + 290, 860), (cx + 200, 900), (cx + 150, 800)], fur_dk)
    p.poly([(cx + 200, 900), (cx + 290, 860), (cx + 270, 840)], fur_lt)
    # 腿与靴子
    p.rect([cx - 92, 760, cx - 8, 960], (40, 44, 58), 14)
    p.rect([cx + 8, 760, cx + 92, 960], (40, 44, 58), 14)
    p.rect([cx - 110, 950, cx - 2, 1010], (62, 44, 36), 18)
    p.rect([cx + 2, 950, cx + 110, 1010], (62, 44, 36), 18)
    # 外套下摆与身体
    p.poly([(cx - 120, 420), (cx + 120, 420), (cx + 150, 790), (cx - 150, 790)], coat)
    p.poly([(cx - 20, 420), (cx + 20, 420), (cx + 40, 790), (cx - 40, 790)], coat_dk)
    for i in range(3):
        p.ell([cx + 8, 500 + i * 70, cx + 24, 516 + i * 70], trim)
    # 手臂（袖子 + 爪）
    p.poly([(cx - 120, 430), (cx - 90, 430), (cx - 120, 700), (cx - 176, 690)], coat_dk)
    p.poly([(cx + 90, 430), (cx + 120, 430), (cx + 176, 690), (cx + 120, 700)], coat_dk)
    p.ell([cx - 188, 676, cx - 112, 740], fur)
    p.ell([cx + 112, 676, cx + 188, 740], fur)
    # 斜挎邮包与带子
    p.poly([(cx - 118, 424), (cx - 84, 424), (cx + 134, 700), (cx + 100, 720)], (96, 70, 44))
    p.rect([cx + 70, 640, cx + 190, 760], (120, 88, 54), 12)
    p.rect([cx + 70, 640, cx + 190, 686], (96, 70, 44), 12)
    p.ell([cx + 120, 676, cx + 140, 696], trim)
    # 围巾
    p.rect([cx - 110, 372, cx + 110, 440], (190, 70, 70), 30)
    p.poly([(cx + 40, 420), (cx + 100, 430), (cx + 110, 560), (cx + 56, 548)], (166, 54, 58))
    # 头：耳朵
    p.poly([(cx - 128, 200), (cx - 96, 40), (cx - 30, 150)], fur_dk)
    p.poly([(cx + 128, 200), (cx + 96, 40), (cx + 30, 150)], fur_dk)
    p.poly([(cx - 108, 180), (cx - 94, 80), (cx - 52, 150)], (74, 54, 66))
    p.poly([(cx + 108, 180), (cx + 94, 80), (cx + 52, 150)], (74, 54, 66))
    # 头部与脸颊毛簇
    p.poly([(cx - 150, 270), (cx - 120, 130), (cx + 120, 130), (cx + 150, 270), (cx + 120, 360), (cx, 392), (cx - 120, 360)], fur)
    p.poly([(cx - 150, 270), (cx - 190, 320), (cx - 140, 330), (cx - 164, 372), (cx - 110, 350)], fur)
    p.poly([(cx + 150, 270), (cx + 190, 320), (cx + 140, 330), (cx + 164, 372), (cx + 110, 350)], fur)
    # 额头深色斑与浅色面罩
    p.poly([(cx - 70, 130), (cx + 70, 130), (cx + 40, 230), (cx, 250), (cx - 40, 230)], fur_dk)
    p.poly([(cx - 120, 290), (cx - 40, 250), (cx, 270), (cx + 40, 250), (cx + 120, 290), (cx + 100, 350), (cx, 386), (cx - 100, 350)], fur_lt)
    # 口鼻部（狼的长吻）
    p.poly([(cx - 52, 280), (cx + 52, 280), (cx + 44, 352), (cx, 372), (cx - 44, 352)], (226, 230, 236))
    p.poly([(cx - 30, 270), (cx + 30, 270), (cx + 22, 304), (cx, 316), (cx - 22, 304)], INK)
    p.line([(cx, 316), (cx, 336)], INK, 3)
    if expression == "worried":
        p.arc([cx - 28, 332, cx, 356], 190, 350, INK, 3)
        p.arc([cx, 332, cx + 28, 356], 190, 350, INK, 3)
    else:
        p.arc([cx - 28, 322, cx, 346], 20, 160, INK, 3)
        p.arc([cx, 322, cx + 28, 346], 20, 160, INK, 3)
    # 眼睛（琥珀色，竖向瞳孔）
    for sx in (-1, 1):
        ex = cx + sx * 66
        p.poly([(ex - 30, 238), (ex + 30, 238 + sx * -6), (ex + 24, 268), (ex - 24, 268)], (238, 240, 244))
        p.ell([ex - 17, 232, ex + 17, 268], (222, 170, 60))
        p.ell([ex - 6, 238, ex + 6, 262], INK)
        p.ell([ex - 12, 238, ex - 4, 246], (255, 255, 255))
        if expression == "worried":
            p.line([(ex - 34, 218 - sx * 8), (ex + 30, 224 + sx * 8)], INK, 5)
        else:
            p.line([(ex - 34, 220 + sx * 4), (ex + 30, 220 - sx * 4)], INK, 5)
    # 鼻侧胡须点
    for sx in (-1, 1):
        for k in range(3):
            p.ell([cx + sx * (24 + k * 9) - 2, 330 + k * 6 - 2, cx + sx * (24 + k * 9) + 2, 330 + k * 6 + 2], fur_dk)
    return p.result()


def draw_fox(expression="normal"):
    """林岚：橘红狐狸，白胸、黑袜、青绿斗篷、蓬松大尾巴。"""
    p = Painter(640, 1040)
    fur, fur_dk, fur_lt = (226, 118, 48), (170, 78, 34), (250, 240, 226)
    cloak, cloak_dk, trim = (36, 98, 98), (24, 70, 74), (232, 200, 120)
    cx = 320
    # 大尾巴（身后左侧）
    p.poly([(cx - 70, 740), (cx - 220, 640), (cx - 300, 700), (cx - 300, 840), (cx - 220, 930), (cx - 110, 880)], fur)
    p.poly([(cx - 300, 700), (cx - 300, 840), (cx - 250, 900), (cx - 200, 860), (cx - 250, 760)], fur_lt)
    p.poly([(cx - 150, 720), (cx - 110, 880), (cx - 70, 740)], fur_dk)
    # 腿（黑袜）与鞋
    p.rect([cx - 84, 770, cx - 12, 960], (46, 36, 38), 14)
    p.rect([cx + 12, 770, cx + 84, 960], (46, 36, 38), 14)
    p.rect([cx - 104, 950, cx - 6, 1006], (36, 30, 34), 18)
    p.rect([cx + 6, 950, cx + 104, 1006], (36, 30, 34), 18)
    # 斗篷 / 身体
    p.poly([(cx - 130, 410), (cx + 130, 410), (cx + 176, 800), (cx - 176, 800)], cloak)
    p.poly([(cx - 130, 410), (cx - 70, 410), (cx - 60, 800), (cx - 176, 800)], cloak_dk)
    p.poly([(cx - 46, 410), (cx + 46, 410), (cx + 30, 640), (cx - 30, 640)], fur_lt)
    p.line([(cx - 130, 420), (cx - 100, 800)], trim, 3)
    p.line([(cx + 130, 420), (cx + 150, 800)], trim, 3)
    # 兜帽后缘 / 领口
    p.rect([cx - 130, 380, cx + 130, 440], cloak_dk, 30)
    # 手臂和一盏小提灯
    p.poly([(cx - 130, 430), (cx - 96, 430), (cx - 130, 690), (cx - 190, 676)], cloak_dk)
    p.poly([(cx + 96, 430), (cx + 130, 430), (cx + 196, 640), (cx + 140, 660)], cloak_dk)
    p.ell([cx - 200, 662, cx - 120, 730], fur_dk)
    p.ell([cx + 150, 628, cx + 230, 696], fur_dk)
    p.line([(cx + 190, 640), (cx + 190, 700)], (200, 180, 120), 3)
    p.rect([cx + 164, 700, cx + 218, 770], (60, 54, 50), 6)
    p.rect([cx + 172, 710, cx + 210, 762], (255, 214, 120), 4)
    # 耳朵（尖而长，黑尖）
    p.poly([(cx - 130, 210), (cx - 120, 20), (cx - 20, 140)], fur)
    p.poly([(cx + 130, 210), (cx + 120, 20), (cx + 20, 140)], fur)
    p.poly([(cx - 120, 20), (cx - 112, 90), (cx - 76, 76)], INK)
    p.poly([(cx + 120, 20), (cx + 112, 90), (cx + 76, 76)], INK)
    p.poly([(cx - 108, 190), (cx - 104, 90), (cx - 50, 150)], (250, 200, 170))
    p.poly([(cx + 108, 190), (cx + 104, 90), (cx + 50, 150)], (250, 200, 170))
    # 头：橘色头顶 + 白色脸颊毛领（倒三角脸）
    p.poly([(cx - 140, 260), (cx - 110, 130), (cx + 110, 130), (cx + 140, 260), (cx + 100, 340), (cx, 380), (cx - 100, 340)], fur)
    p.poly([(cx - 150, 270), (cx - 200, 330), (cx - 144, 328), (cx - 160, 376), (cx - 100, 340), (cx - 40, 300)], fur_lt)
    p.poly([(cx + 150, 270), (cx + 200, 330), (cx + 144, 328), (cx + 160, 376), (cx + 100, 340), (cx + 40, 300)], fur_lt)
    # 吻部（更尖、白色下半）
    p.poly([(cx - 46, 250), (cx + 46, 250), (cx + 60, 310), (cx, 392), (cx - 60, 310)], fur_lt)
    p.poly([(cx - 28, 262), (cx + 28, 262), (cx + 18, 300), (cx, 310), (cx - 18, 300)], INK)
    p.line([(cx, 310), (cx, 336)], INK, 3)
    if expression == "smile":
        p.arc([cx - 36, 318, cx, 352], 10, 170, INK, 3)
        p.arc([cx, 318, cx + 36, 352], 10, 170, INK, 3)
        p.poly([(cx - 10, 342), (cx + 10, 342), (cx, 360)], (230, 120, 130))
    else:
        p.line([(cx - 30, 340), (cx, 336), (cx + 30, 340)], INK, 3)
    # 眼睛（绿色，狭长；smile 时为弯月形）
    for sx in (-1, 1):
        ex = cx + sx * 64
        if expression == "smile":
            p.arc([ex - 26, 236, ex + 26, 276], 200, 340, INK, 5)
        else:
            p.poly([(ex - 32, 252), (ex, 234), (ex + 32, 244 - sx * 4), (ex + 26, 270), (ex - 20, 272)], (240, 244, 240))
            p.ell([ex - 16, 238, ex + 16, 270], (70, 168, 130))
            p.ell([ex - 6, 244, ex + 6, 266], INK)
            p.ell([ex - 12, 243, ex - 4, 251], (255, 255, 255))
            p.line([(ex - 34, 232 + sx * 6), (ex + 34, 226 - sx * 6)], INK, 5)
    # 额头标记
    p.poly([(cx - 12, 140), (cx + 12, 140), (cx, 190)], fur_dk)
    return p.result()


# ---------------------------------------------------------------- 主菜单 / 其他
def make_main_menu():
    W, H = 1920, 1080
    img = make_bg_dock()
    img = ImageEnhanceDark(img)
    return img


def ImageEnhanceDark(img):
    """整体压暗并加一层深蓝，作为主菜单背景。"""
    overlay = Image.new("RGB", img.size, (14, 22, 38))
    return Image.blend(img, overlay, 0.45)


def make_game_menu():
    """存档 / 设置等游戏菜单的背景：压暗后的后巷。"""
    return ImageEnhanceDark(make_bg_alley())


def make_window_icon():
    """窗口图标：灰舟的头像裁切（256x256）。"""
    wolf = draw_wolf("normal").crop((120, 20, 520, 420))
    icon = Image.new("RGBA", (400, 400), (30, 44, 66, 255))
    icon.alpha_composite(wolf)
    return icon.resize((256, 256), Image.LANCZOS)


def save(img, name, folder=IMG_DIR):
    # 游戏分辨率为 1280x720：1920x1080 绘制的背景在此缩小，立绘保持原尺寸并在游戏内缩放
    if img.size == (1920, 1080):
        img = img.resize((1280, 720), Image.LANCZOS)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    img.save(path, optimize=True)
    print("wrote", os.path.relpath(path, ROOT), img.size)


def main():
    save(make_bg_dock(), "bg_dock.png")
    save(make_bg_alley(), "bg_alley.png")
    save(make_bg_lighthouse(), "bg_lighthouse.png")
    save(draw_wolf("normal"), "huizhou_normal.png")
    save(draw_wolf("worried"), "huizhou_worried.png")
    save(draw_fox("normal"), "linlan_normal.png")
    save(draw_fox("smile"), "linlan_smile.png")
    save(make_main_menu(), "main_menu.png", GUI_DIR)
    save(make_game_menu(), "game_menu.png", GUI_DIR)
    save(make_window_icon(), "window_icon.png", GUI_DIR)


if __name__ == "__main__":
    main()
