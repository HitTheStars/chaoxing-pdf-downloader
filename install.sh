#!/bin/bash
# 超星学习通 PDF 下载器 - macOS / Linux 一键安装脚本
# 使用方法：
#   chmod +x install.sh
#   ./install.sh

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  超星学习通 PDF 下载器 - 安装向导${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 检测 Python
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}[!] 未检测到 Python${NC}"
    echo "请安装 Python 3.8 或更高版本："
    echo "  macOS:   brew install python3"
    echo "  Ubuntu:  sudo apt install python3 python3-venv python3-pip"
    echo "  Arch:    sudo pacman -S python"
    exit 1
fi

echo -e "${GREEN}[*] 检测到 Python: $PYTHON_CMD${NC}"
$PYTHON_CMD --version

# 检测 pip
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo -e "${YELLOW}[!] 未检测到 pip，尝试安装...${NC}"
    $PYTHON_CMD -m ensurepip --upgrade || {
        echo -e "${RED}[!] pip 安装失败，请手动安装 python3-pip${NC}"
        exit 1
    }
fi

# 创建虚拟环境
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}[*] 创建虚拟环境...${NC}"
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

echo -e "${YELLOW}[*] 安装依赖...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -e . -q

echo -e "${YELLOW}[*] 安装 Playwright 浏览器（仅需一次，约 100MB）...${NC}"
"$VENV_DIR/bin/python" -m playwright install chromium

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}使用方法：${NC}"
echo -e "  1. 启动浏览器并登录超星："
echo -e "     ${YELLOW}./.venv/bin/python chaoxing_pdf_downloader.py --launch${NC}"
echo ""
echo -e "  2. 在浏览器中打开课程章节后，下载 PDF："
echo -e "     ${YELLOW}./.venv/bin/python chaoxing_pdf_downloader.py --download${NC}"
echo ""
echo -e "  或直接运行（若已添加到 PATH）："
echo -e "     ${YELLOW}chaoxing-dl --launch${NC}"
echo -e "     ${YELLOW}chaoxing-dl --download${NC}"
echo ""
