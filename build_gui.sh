#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> 安装依赖…"
pip install -e ".[gui]" --quiet
pip install pyinstaller --quiet

echo "==> 清理旧构建…"
rm -rf build dist

echo "==> 开始打包…"
pyinstaller ffmpeg_gui.spec --noconfirm

# 输出结果
if [[ "$(uname)" == "Darwin" ]]; then
    echo ""
    echo "==> 打包完成: dist/FFmpegTools.app"
    echo "    运行: open dist/FFmpegTools.app"
else
    echo ""
    echo "==> 打包完成: dist/FFmpegTools"
    echo "    运行: ./dist/FFmpegTools"
fi
