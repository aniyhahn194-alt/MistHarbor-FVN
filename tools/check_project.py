#!/usr/bin/env python3
"""简易静态检查：label / jump / call / 图片 / 变量引用。

不依赖 Ren'Py SDK，只用正则扫描 game/*.rpy，作为 `renpy.sh <项目> lint` 的补充。
用法：python3 tools/check_project.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "game")
SCRIPTS = ["script.rpy", "tests.rpy"]  # 只检查剧情与测试脚本；screens / gui / ending_card 为界面代码，由 renpy lint 检查
UI_FILES = ["screens.rpy", "gui.rpy", "ending_card.rpy"]  # 仅用来收集 default 变量声明

errors = []


def err(msg):
    errors.append(msg)


def read(name):
    with open(os.path.join(GAME, name), encoding="utf-8") as f:
        return f.read().splitlines()


lines = {n: read(n) for n in SCRIPTS if os.path.exists(os.path.join(GAME, n))}
all_lines = [(n, i + 1, l) for n, ls in lines.items() for i, l in enumerate(ls)]

# 1. 缩进：Ren'Py 要求 4 空格缩进，不允许 Tab
for n, i, l in all_lines:
    if "\t" in l:
        err(f"{n}:{i}: 含有 Tab 字符")
    if l.strip() and (len(l) - len(l.lstrip(" "))) % 4 != 0:
        err(f"{n}:{i}: 缩进不是 4 的倍数")

# 2. label / jump / call
labels = set()
for n, i, l in all_lines:
    m = re.match(r"\s*label\s+([A-Za-z_][\w.]*)", l)
    if m:
        labels.add(m.group(1))
labels |= {"start", "main_menu_screen"}  # 引擎内置
for n, i, l in all_lines:
    for m in re.finditer(r"^\s*(?:jump|call)\s+(?!screen\b|expression\b)([A-Za-z_]\w*)", l):
        if m.group(1) not in labels:
            err(f"{n}:{i}: 跳转到未定义的 label '{m.group(1)}'")
    for m in re.finditer(r'Jump\("(\w+)"\)', l):
        if m.group(1) not in labels:
            err(f"{n}:{i}: Jump 到未定义的 label '{m.group(1)}'")

# 3. 图片：image 定义指向的文件必须存在；scene/show 使用的图像必须已定义
defined = set()
for n, i, l in all_lines:
    m = re.match(r'\s*image\s+([\w ]+?)\s*:\s*$', l)
    if m:
        defined.add(m.group(1).strip())  # ATL 图像（如 fog_drift），其中的图片文件由 renpy lint 检查
    m = re.match(r'\s*image\s+([\w ]+?)\s*=\s*(.*)$', l)
    if m:
        defined.add(m.group(1).strip())
        for f in re.findall(r'"([^"]+\.(?:png|jpg|webp))"', m.group(2)):
            if not os.path.exists(os.path.join(GAME, f)):
                err(f"{n}:{i}: 图片文件不存在 {f}")
tags = {d.split()[0] for d in defined}
for n, i, l in all_lines:
    m = re.match(r"\s*(scene|show)\s+(?!screen\b)([A-Za-z_][\w ]*?)(?:\s+(?:at|with|behind|as|onlayer|zorder)\b.*)?$", l)
    if m and m.group(2).strip() not in defined and m.group(2).strip().split()[0] not in ("black", "text", "expression"):
        err(f"{n}:{i}: 使用了未定义的图像 '{m.group(2).strip()}'")
    m = re.match(r"\s*hide\s+(?!screen\b)([A-Za-z_]\w*)", l)
    if m and m.group(1) not in tags:
        err(f"{n}:{i}: hide 了未定义的图像标签 '{m.group(1)}'")

# 4. 角色：说话者必须已 define
chars = set()
for n, i, l in all_lines:
    m = re.match(r"\s*define\s+(\w+)\s*=\s*Character\(", l)
    if m:
        chars.add(m.group(1))
for n, i, l in all_lines:
    m = re.match(r'\s*([a-z]\w*)(?:\s+\w+)*\s+"', l)
    if m and m.group(1) not in chars and m.group(1) not in (
            "menu", "centered", "text", "type", "click", "pause", "screen", "frame", "vbox", "hbox"):
        pass  # 仅作提示，避免对 UI 语句误报
speakers = set()
for n, i, l in all_lines:
    if n != "script.rpy":
        continue
    m = re.match(r'^    ([a-z]\w*)\s+(?:\w+\s+)?"', l)
    if m and m.group(1) not in ("text", "show", "hide", "scene", "jump", "call", "with", "menu", "if", "elif", "else", "return", "pass", "centered"):
        speakers.add(m.group(1))
for s in speakers:
    if s not in chars:
        err(f"script.rpy: 说话者 '{s}' 未用 Character 定义")

# 5. 变量：default 声明；被 `$ x =` 赋值或 if 判断的变量必须有 default
defaults = set()
for n, i, l in all_lines:
    m = re.match(r"\s*default\s+([\w.]+)\s*=", l)
    if m:
        defaults.add(m.group(1))
for n in UI_FILES:
    if os.path.exists(os.path.join(GAME, n)):
        for l in read(n):
            m = re.match(r"\s*default\s+([\w.]+)\s*=", l)
            if m:
                defaults.add(m.group(1))
in_python = False
for n, i, l in all_lines:
    if l.strip() and not l.startswith(" "):
        in_python = l.startswith("init python")
    if in_python:
        continue
    m = re.match(r"\s*\$\s*([a-z_]\w*)\s*[+\-]?=", l)
    if m and m.group(1) not in defaults:
        err(f"{n}:{i}: 变量 '{m.group(1)}' 被赋值但没有 default")
    m = re.match(r"\s*(?:if|elif)\s+(?:not\s+)?([a-z_]\w*)\b", l)
    if m and m.group(1) not in defaults and m.group(1) not in ("renpy", "persistent"):
        err(f"{n}:{i}: 变量 '{m.group(1)}' 用于判断但没有 default")

# 6. 所有 game/images 下的 png 是否都被引用（避免遗留未使用素材）
used = " ".join(l for _, _, l in all_lines)
for f in sorted(os.listdir(os.path.join(GAME, "images"))):
    if f not in used:
        err(f"images/{f} 未被任何脚本引用")

# 7. 结局：每个 ending label 必须以 return 结束
text = "\n".join(lines["script.rpy"])
for m in re.finditer(r"label (ending_\w+):(.*?)(?=\nlabel |\Z)", text, re.S):
    if not re.search(r"^\s+return\s*$", m.group(2), re.M):
        err(f"label {m.group(1)} 没有 return（无法回到主菜单）")

if errors:
    print("发现问题：")
    for e in errors:
        print(" -", e)
    sys.exit(1)
print(f"静态检查通过：{len(labels)} 个 label，{len(defined)} 个图像，{len(chars)} 个角色，{len(defaults)} 个 default 变量。")
