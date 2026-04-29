# 超星学习通 PDF 下载器 - Windows 一键安装脚本
# 使用方法：右键点击 -> 使用 PowerShell 运行，或在 PowerShell 中执行：
# powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  超星学习通 PDF 下载器 - 安装向导" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检测 Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "[!] 未检测到 Python" -ForegroundColor Red
    Write-Host "请从 https://www.python.org/downloads/ 下载并安装 Python 3.8 或更高版本"
    Write-Host "安装时请务必勾选 'Add Python to PATH'"
    Write-Host ""
    Start-Process "https://www.python.org/downloads/"
    Read-Host "安装完成后按 Enter 键继续"
    # 重新检测
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }
    if (-not $pythonCmd) {
        Write-Host "[!] 仍未检测到 Python，请手动安装后重试" -ForegroundColor Red
        exit 1
    }
}

$pythonPath = $pythonCmd.Source
Write-Host "[*] 检测到 Python: $pythonPath" -ForegroundColor Green

# 检测版本
$pyVersion = & $pythonPath --version 2>&1
Write-Host "[*] Python 版本: $pyVersion" -ForegroundColor Green

# 创建虚拟环境
$venvDir = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Host "[*] 创建虚拟环境..." -ForegroundColor Yellow
    & $pythonPath -m venv $venvDir
}

# 激活虚拟环境
$venvPython = Join-Path $venvDir "Scripts\python.exe"
$venvPip = Join-Path $venvDir "Scripts\pip.exe"

Write-Host "[*] 安装依赖..." -ForegroundColor Yellow
& $venvPip install --upgrade pip | Out-Null
& $venvPip install -e . | Out-Null

Write-Host "[*] 安装 Playwright 浏览器（仅需一次，约 100MB）..." -ForegroundColor Yellow
& $venvPython -m playwright install chromium | Out-Null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "使用方法：" -ForegroundColor Cyan
Write-Host "  1. 启动浏览器并登录超星：" -ForegroundColor White
Write-Host "     .\.venv\Scripts\python.exe chaoxing_pdf_downloader.py --launch" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. 在浏览器中打开课程章节后，下载 PDF：" -ForegroundColor White
Write-Host "     .\.venv\Scripts\python.exe chaoxing_pdf_downloader.py --download" -ForegroundColor Yellow
Write-Host ""
Write-Host "  或直接运行（若已添加到 PATH）：" -ForegroundColor White
Write-Host "     chaoxing-dl --launch" -ForegroundColor Yellow
Write-Host "     chaoxing-dl --download" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Enter 键退出..." -ForegroundColor Gray
Read-Host | Out-Null
