#!/usr/bin/env bash
# 用 Ren'Py 官方 Web 构建（launcher 的 web_build 命令，等价于 Launcher 里的 “Build Web Application”）
# 生成真正的 HTML5/WebAssembly 版本。
#
# 用法：tools/build_web.sh <Ren'Py SDK 目录> [输出目录，默认 ./dists/web]
#
# 前置条件：
#   * Ren'Py 8.3.7 SDK（https://www.renpy.org/dl/8.3.7/renpy-8.3.7-sdk.tar.bz2）
#   * 对应版本的官方 Web 组件（https://www.renpy.org/dl/8.3.7/renpy-8.3.7-web.zip），解压到 <SDK>/web/
#     （Launcher 里点 “Build Web Application” 时会提示并自动下载；命令行下可设置 RENPY_WEB_AUTO_INSTALL=1 让本脚本代为下载）
#
# 输出：
#   <输出目录>/MistHarbor-FVN-web/        可直接用任意静态服务器托管的目录
#   <输出目录>/MistHarbor-FVN-web.zip     同内容的 zip（SHA256 会打印并写入 SHA256SUMS.txt）
#
# 注意：首次 Web 构建会在项目根目录生成 progressive_download.txt（Ren'Py 自动创建，决定哪些图片按需下载），
# 该文件已提交到仓库；产物目录/zip 体积较大（约 45 MB），不要提交进 git。
set -euo pipefail

SDK="${1:?请提供 RenPy SDK 目录，例如 ~/renpy-8.3.7-sdk}"
DEST="${2:-./dists/web}"
PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
SDK="$(cd "$SDK" && pwd)"
mkdir -p "$DEST"
DEST="$(cd "$DEST" && pwd)"
OUTDIR="$DEST/MistHarbor-FVN-web"
WEB_VERSION="8.3.7"

if [ ! -f "$SDK/web/index.html" ]; then
  if [ "${RENPY_WEB_AUTO_INSTALL:-0}" = "1" ]; then
    echo "未找到 $SDK/web，下载官方 renpy-$WEB_VERSION-web.zip ..."
    tmp="$(mktemp -d)"
    curl -fSL "https://www.renpy.org/dl/$WEB_VERSION/renpy-$WEB_VERSION-web.zip" -o "$tmp/web.zip"
    unzip -q "$tmp/web.zip" -d "$SDK"
    rm -rf "$tmp"
  else
    echo "错误：SDK 缺少官方 Web 组件 $SDK/web/" >&2
    echo "请在 Launcher 里点 “Build Web Application” 让它下载，或手动下载" >&2
    echo "  https://www.renpy.org/dl/$WEB_VERSION/renpy-$WEB_VERSION-web.zip" >&2
    echo "解压到 $SDK 下（得到 $SDK/web/），或设置 RENPY_WEB_AUTO_INSTALL=1 重新运行本脚本。" >&2
    exit 1
  fi
fi

# 无显示器的服务器上，让 SDL 使用 dummy 驱动即可（构建本身不需要图形输出）。
export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-dummy}"
export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-dummy}"

"$SDK/renpy.sh" "$SDK/launcher" web_build "$PROJECT" --destination "$OUTDIR"

test -f "$OUTDIR/index.html" -a -f "$OUTDIR/renpy.wasm" -a -f "$OUTDIR/game.zip" \
  || { echo "错误：构建产物不完整" >&2; exit 1; }

(cd "$DEST" && sha256sum "MistHarbor-FVN-web.zip" | tee SHA256SUMS.txt)
du -sh "$OUTDIR" "$DEST/MistHarbor-FVN-web.zip"
echo "本地预览：node tools/web_test/serve.js \"$OUTDIR\" 8000   然后访问 http://127.0.0.1:8000/"
