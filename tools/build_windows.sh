#!/usr/bin/env bash
# 用 Ren'Py 官方 distribute 命令构建 Windows 发行包（zip）。
# 用法：tools/build_windows.sh <Ren'Py SDK 目录> [输出目录，默认 ./dists]
# 在 Linux 上用 SDK 8.3.7 验证过；需要 SDK 自带的 lib/py3-windows-x86_64（官方 SDK 默认包含）。
set -euo pipefail
SDK="${1:?请提供 RenPy SDK 目录，例如 ~/renpy-8.3.7-sdk}"
DEST="${2:-./dists}"
PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$DEST"
"$SDK/renpy.sh" "$SDK/launcher" distribute "$PROJECT" --package win --destination "$DEST"
ls -la "$DEST"
