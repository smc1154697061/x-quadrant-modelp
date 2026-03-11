#!/bin/bash
# ===================================
# PyInstaller 打包脚本 (Linux/Mac)
# ===================================

set -e  # 遇到错误立即退出

echo "[1/5] 清理旧的打包文件..."
rm -rf dist build *.spec

echo "[2/5] 检查依赖..."
pip install pyinstaller || {
    echo "错误: 安装 PyInstaller 失败"
    exit 1
}

echo "[3/5] 开始打包..."
pyinstaller build_spec.py --clean --noconfirm || {
    echo "错误: 打包失败"
    exit 1
}

echo "[4/5] 创建运行目录..."
mkdir -p dist/runtime/{data,logs}

# 复制必要的文件
echo "[5/5] 复制配置文件..."
cp -r data/* dist/runtime/data/ 2>/dev/null || true
cp -r logs/* dist/runtime/logs/ 2>/dev/null || true

echo ""
echo "==================================="
echo "打包完成！"
echo "==================================="
echo ""
echo "可执行文件位置: dist/x-quadrant-modelp"
echo "运行目录: dist/runtime/"
echo ""
echo "部署到服务器:"
echo "1. 将 dist/x-quadrant-modelp 上传到服务器"
echo "2. 将 dist/runtime/ 目录上传到服务器"
echo "3. 赋予执行权限: chmod +x x-quadrant-modelp"
echo "4. 在服务器上运行: ./x-quadrant-modelp"
echo ""

