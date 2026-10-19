#!/usr/bin/env python3
"""把 before-*.png 与 after-*.png 拼成左（前）右（后）的对比图。

用法：python3 tools/make_side_by_side.py <before 目录> <after 目录> <输出目录>
文件名约定：before-<viewport>-<名称>.png 与 after-<viewport>-<名称>.png（由 tools/web_test/v05_flow.js 生成）。
只在两边都有同名截图时才拼。输出 JPEG（体积小），底部带“前 / 后”标签（用游戏自带的思源黑体 Lite，OFL）。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "game", "fonts", "SourceHanSansLite.ttf")


def main(before, after, out):
    os.makedirs(out, exist_ok=True)
    font = ImageFont.truetype(FONT, 26)
    n = 0
    for fn in sorted(os.listdir(before)):
        if not fn.startswith("before-") or not fn.endswith(".png"):
            continue
        other = os.path.join(after, "after-" + fn[len("before-"):])
        if not os.path.exists(other):
            continue
        a = Image.open(os.path.join(before, fn)).convert("RGB")
        b = Image.open(other).convert("RGB")
        if b.size != a.size:
            b = b.resize(a.size, Image.LANCZOS)
        bar = 44
        canvas = Image.new("RGB", (a.width * 2 + 8, a.height + bar), (8, 12, 18))
        canvas.paste(a, (0, 0))
        canvas.paste(b, (a.width + 8, 0))
        d = ImageDraw.Draw(canvas)
        d.text((12, a.height + 8), "前：main（V0.2-P1）", font=font, fill=(200, 215, 225))
        d.text((a.width + 20, a.height + 8), "后：V0.5", font=font, fill=(243, 198, 119))
        name = fn[len("before-"):-4] + ".jpg"
        canvas.save(os.path.join(out, name), quality=88)
        n += 1
    print("wrote %d side-by-side images to %s" % (n, out))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
