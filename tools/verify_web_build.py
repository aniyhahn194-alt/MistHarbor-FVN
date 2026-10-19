#!/usr/bin/env python3
"""Web 构建后处理与校验（V0.5）。

  apply-presplash <项目目录> <产物目录>
      把项目根目录的 web-presplash.(png|jpg|webp) 放进产物，删除 Ren'Py 默认的 web-presplash.jpg，
      改写 index.html / pwa_catalog.json 的引用，给加载状态条注入一小段 CSS 外观覆盖，并按 Launcher 的方式重新生成 <产物目录>.zip。
      （官方 CLI web_build 在这一步有 bug，见 tools/build_web.sh 里的说明；Launcher 图形界面没有。）
  check <项目目录> <产物目录>
      校验：index.html 引用的 presplash 存在且与项目文件逐字节一致；默认 presplash 已被替换；
      game.zip 内不含 tests.rpy / 截图辅助脚本，且每个 game/ 下的 .rpyc 都有对应的 .rpy（引擎自带的 renpy/common 不检查）（没有残留）。
      任何一项不满足都以非 0 退出。
"""
import json
import os
import re
import shutil
import sys
import zipfile

SKIN_MARK = "mistharbor-web-skin"
## 只覆盖 index.html 顶部“加载状态条”的外观（默认是黑底 + 浏览器原生蓝色进度条）与页面底色，使其与夜雾港口风格一致。
## 没有改动任何脚本 / 加载逻辑。
SKIN_CSS = """  <style id="mistharbor-web-skin">
    html, body { background: #05080d; }
    #statusDiv { background: rgba(6, 12, 22, 0.86); border-bottom: 1px solid rgba(95, 184, 196, 0.55); border-radius: 0 0 10px 10px; }
    #statusTextDiv { color: #9fc4cf; letter-spacing: 0.04em; }
    #statusProgress { accent-color: #f3c677; }
    #ContextButton { color: rgba(159, 196, 207, 0.8); }
  </style>"""

NAMES = ["web-presplash.png", "web-presplash.jpg", "web-presplash.webp"]


def find_presplash(project):
    for n in NAMES:
        if os.path.exists(os.path.join(project, n)):
            return n
    return None


def apply_presplash(project, out):
    name = find_presplash(project)
    if not name:
        print("项目没有 web-presplash.*，保持 Ren'Py 默认加载画面")
        return
    default = os.path.join(out, "web-presplash.jpg")
    if name != "web-presplash.jpg" and os.path.exists(default):
        os.unlink(default)
    shutil.copy(os.path.join(project, name), os.path.join(out, name))
    idx = os.path.join(out, "index.html")
    with open(idx, encoding="utf-8") as f:
        html = f.read()
    html = html.replace("web-presplash.jpg", name)
    if SKIN_MARK not in html:
        html = html.replace("</head>", SKIN_CSS + "\n</head>", 1)
    with open(idx, "w", encoding="utf-8") as f:
        f.write(html)
    cat = os.path.join(out, "pwa_catalog.json")
    if os.path.exists(cat):
        with open(cat, encoding="utf-8") as f:
            data = json.load(f)
        data["files"] = [name if x == "web-presplash.jpg" else x for x in data["files"]]
        with open(cat, "w", encoding="utf-8") as f:
            f.write(json.dumps(data))
    targets = []
    for dn, dirs, files in os.walk(out):
        targets += [os.path.join(dn, d) for d in dirs]
        targets += [os.path.join(dn, f) for f in files]
    zpath = out.rstrip("/") + ".zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for t in targets:
            zf.write(t, os.path.relpath(t, out))
    print("已应用自制加载画面 %s，并重新生成 %s" % (name, os.path.basename(zpath)))


def check(project, out):
    errs = []
    name = find_presplash(project)
    with open(os.path.join(out, "index.html"), encoding="utf-8") as f:
        html = f.read()
    m = re.search(r'<img id="presplash" src="([^"]+)"', html)
    ref = m.group(1) if m else None
    if name:
        if ref != name:
            errs.append("index.html 引用的 presplash 是 %r，期望 %r" % (ref, name))
        elif not os.path.exists(os.path.join(out, ref)):
            errs.append("产物里缺少 %s" % ref)
        else:
            with open(os.path.join(project, name), "rb") as a, open(os.path.join(out, ref), "rb") as b:
                if a.read() != b.read():
                    errs.append("产物里的 %s 与项目文件不一致" % ref)
        if name != "web-presplash.jpg" and os.path.exists(os.path.join(out, "web-presplash.jpg")):
            errs.append("产物里仍有 Ren'Py 默认 web-presplash.jpg")
        if SKIN_MARK not in html:
            errs.append("index.html 缺少加载状态条样式（%s）" % SKIN_MARK)
    with zipfile.ZipFile(os.path.join(out, "game.zip")) as zf:
        names = zf.namelist()
    for n in names:
        base = os.path.basename(n)
        if base in ("tests.rpy", "tests.rpyc", "capture_screenshots.rpy", "capture_screenshots.rpyc", "dbg.rpy", "dbg.rpyc"):
            errs.append("game.zip 内含开发用文件 %s" % n)
    nameset = set(names)
    for n in names:
        if n.startswith("game/") and n.endswith(".rpyc") and n[:-1] not in nameset:
            errs.append("game.zip 内有残留 .rpyc（没有对应 .rpy）：%s" % n)
    zpath = out.rstrip("/") + ".zip"
    if os.path.exists(zpath):
        with zipfile.ZipFile(zpath) as zf:
            if "index.html" not in zf.namelist():
                errs.append("外层 zip 缺少 index.html")
            if name and name not in zf.namelist():
                errs.append("外层 zip 缺少 %s" % name)
            if name and name != "web-presplash.jpg" and "web-presplash.jpg" in zf.namelist():
                errs.append("外层 zip 仍含默认 web-presplash.jpg")
    if errs:
        print("Web 产物校验失败：")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print("Web 产物校验通过：index.html 引用 %s（与项目文件一致，默认 presplash 已替换）；"
          "game.zip 共 %d 项，不含 tests.rpy，无残留 .rpyc" % (ref, len(names)))


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("apply-presplash", "check"):
        print(__doc__)
        sys.exit(2)
    {"apply-presplash": apply_presplash, "check": check}[sys.argv[1]](os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3]))
