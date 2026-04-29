<div align="center">

# 📚 Chaoxing PDF Downloader

<p>
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-green?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License: MIT">
</p>

<p>
  <b>超星学习通 PDF 批量下载器</b><br>
  一键下载课程中「没有下载按钮」的 PDF 课件
</p>

[//]: # (<img src="assets/demo.png" width="600" alt="演示截图">)

</div>

---

## ✨ 功能特性

- 🔍 **自动嗅探** —— 无需手动找链接，自动扫描当前课程页面中的所有 PDF
- 🛡️ **绕开限制** —— 针对「下载按钮被禁用」的 PDF，从云盘预览页源码中提取真实下载链接
- 🍪 **持久登录** —— 登录一次，长期有效，不用每次重复扫码
- 🖥️ **跨平台** —— 支持 Windows、macOS、Linux
- 📂 **智能命名** —— 自动保留原始文件名，支持防重名

---

## 📖 原理说明

超星学习通的 PDF 通常以两种方式嵌入：

| 类型 | 说明 | 本工具的处理方式 |
|------|------|----------------|
| **云盘预览页** | PDF 托管在 `pan-yz.chaoxing.com`，页面通过 iframe 嵌入 | 读取 iframe HTML 源码，正则提取 `*/download/*` 真实直链，在 iframe 内触发点击，保证 Referer 正确 |
| **PDF Viewer** | 基于 PDF.js 的内置阅读器 | 提取 `#downloadUrl` 元素的 `href`，若未被禁用则直接点击下载 |

下载链接包含时效性签名（`at_`, `ak_`, `ad_`），直接复制到外部访问会返回 `403`。本工具通过在**对应的 iframe 上下文内**触发下载，确保请求携带正确的 Cookie 和 Referer，从而绕开验证。

---

## 🚀 快速开始

### 第一步：下载本项目

点击右上角绿色按钮 **<> Code → Download ZIP**，解压到任意文件夹。

或者使用 Git：
```bash
git clone https://github.com/HitTheStars/chaoxing-pdf-downloader.git
cd chaoxing-pdf-downloader
```

---

### 第二步：一键安装（推荐）

#### 🪟 Windows

1. 确保已安装 [Python 3.8+](https://www.python.org/downloads/)（安装时勾选 **"Add Python to PATH"**）
2. 进入项目文件夹，**右键** `install.ps1` → **使用 PowerShell 运行**

或者打开 PowerShell，执行：
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

#### 🍎 macOS / 🐧 Linux

打开终端，进入项目文件夹，执行：
```bash
chmod +x install.sh
./install.sh
```

> 安装过程会自动创建虚拟环境、安装依赖、下载 Playwright 浏览器（约 100MB，仅需一次）。

---

### 第三步：启动浏览器并登录

#### Windows
```powershell
.\.venv\Scripts\python.exe chaoxing_pdf_downloader.py --launch
```

#### macOS / Linux
```bash
./.venv/bin/python chaoxing_pdf_downloader.py --launch
```

- 系统会弹出一个 Chrome 窗口
- **手动登录**你的超星学习通账号
- 登录完成后，在终端按 `Ctrl+C` 结束进程
- 浏览器会继续在后台运行，登录状态保存在 `.chaoxing_profile` 文件夹中

---

### 第四步：下载 PDF

在浏览器中打开你想下载的课程章节，然后执行：

#### Windows
```powershell
.\.venv\Scripts\python.exe chaoxing_pdf_downloader.py --download
```

#### macOS / Linux
```bash
./.venv/bin/python chaoxing_pdf_downloader.py --download
```

下载的文件默认保存在系统的 **下载文件夹**（`~/Downloads` 或 `C:\Users\用户名\Downloads`）。

---

### 完整演示

```text
[*] 正在扫描页面中的 PDF 资源...
[*] 共 33 个 frames

[Frame 12] 云盘预览页  file_id=9a779462583d289b458edc6073399a62
  └─ 发现下载链接 -> 第1讲软硬件介绍.pdf
[Frame 17] 云盘预览页  file_id=08b15335d3f665287f4b26775afd1d1d
  └─ 发现下载链接 -> 第1讲GPIO.pdf

[*] 共发现 5 个 PDF，开始下载...

[↓] 开始下载: 第1讲软硬件介绍.pdf
    ✓ 成功 (4,988,243 bytes)

[*] 全部完成: 5/5 成功
```

---

## ⚙️ 命令行参数

```bash
python chaoxing_pdf_downloader.py [选项]
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `--launch` | 启动持久化浏览器（首次使用） | `--launch` |
| `--download` | 连接浏览器并下载当前页面所有 PDF | `--download` |
| `--profile` | Chrome 用户数据目录 | `--profile ./my_profile` |
| `--output` | PDF 保存目录 | `--output ./course_pdfs` |
| `--cdp` | CDP 调试地址 | `--cdp http://localhost:9222` |

### 指定下载目录示例

```bash
# Windows
.\.venv\Scripts\python.exe chaoxing_pdf_downloader.py --download --output D:\课程资料

# macOS / Linux
./.venv/bin/python chaoxing_pdf_downloader.py --download --output ~/课程资料
```

---

## 📁 项目结构

```
chaoxing-pdf-downloader/
├── chaoxing_pdf_downloader.py    # 主程序
├── install.ps1                   # Windows 一键安装脚本
├── install.sh                    # macOS / Linux 一键安装脚本
├── pyproject.toml                # pip 安装配置
├── requirements.txt              # Python 依赖
├── .gitignore                    # Git 忽略配置
├── LICENSE                       # MIT 许可证
└── README.md                     # 本文件
```

---

## ❓ 常见问题

### Q1: 安装时提示 "未检测到 Python"

- **Windows**: 从 [python.org](https://www.python.org/downloads/) 下载安装包，**安装时必须勾选 "Add Python to PATH"**
- **macOS**: `brew install python3`
- **Linux**: `sudo apt install python3 python3-venv python3-pip` (Ubuntu/Debian) 或 `sudo pacman -S python` (Arch)

### Q2: 提示 "浏览器已启动但 CDP 端口 9222 不可用"

确保之前运行过 `--launch` 且浏览器进程没有被手动关闭。如果关闭了，重新运行 `--launch` 即可。

### Q3: 下载失败，提示签名过期

下载链接的签名（`at_`, `ak_`, `ad_`）有几分钟的有效期。**刷新课程页面**后重新运行 `--download` 即可获取新的签名。

### Q4: 某些章节扫描不到 PDF

本工具目前支持以下三种常见的资源嵌入方式：
- `pan-yz.chaoxing.com` 云盘预览页
- `/ananas/modules/pdf/index.html` 内置阅读器（下载按钮可用）
- `/ananas/modules/pdf/index.html` 内置阅读器（下载按钮被禁用，但链接藏在 JS 变量 `window.data` 中）

如果课程使用了其他方式（如纯图片预览、第三方 Office 在线预览等），本工具暂时无法识别。欢迎提交 Issue 反馈。

### Q5: 如何批量下载整门课的所有章节？

使用 `--bulk` 参数即可自动遍历所有章节并下载：
```bash
python chaoxing_pdf_downloader.py --bulk
```

### Q6: 我不想用命令行，有更简单的方式吗？

可以考虑使用浏览器扩展方案（零命令行操作），但目前本项目仅提供 Python 版本。有相关需求可以提 Issue 讨论。

---

## ⚠️ 免责声明

> **本工具仅供拥有合法访问权限的用户进行个人学习使用。**

### 使用前提

- 你必须是课程的合法注册学生，且已通过超星学习通官方渠道登录
- 本工具**不具备**绕过登录验证、破解付费内容或突破任何技术保护措施的能力
- 本工具本质上是浏览器自动化脚本，模拟的是人工点击下载操作

### 禁止行为

以下行为**明确禁止**，否则产生的全部法律责任由使用者自行承担：

- ❌ 将下载的课程资料传播、分享到任何公开或私人群组、网盘、社交平台
- ❌ 将下载的内容用于商业目的或牟利
- ❌ 将本工具用于访问或下载你没有权限查看的课程内容
- ❌ 对本工具进行二次修改以用于批量爬取、数据挖掘等超出个人学习范围的行为

### 知识产权声明

课程中的 PDF、PPT、Word 等资料版权归原作者所有（授课教师或出版机构）。本工具仅提供技术便利，不享有任何资料的版权，也不对使用者如何处置下载内容负责。

**因违反上述规定而产生的任何法律纠纷、学校处分、平台封号等后果，由使用者自行承担，与本工具作者无关。**

详见 [DISCLAIMER.md](DISCLAIMER.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

- 发现 Bug？请提交 [Issue](https://github.com/HitTheStars/chaoxing-pdf-downloader/issues)
- 有新想法？欢迎 [Discussions](https://github.com/HitTheStars/chaoxing-pdf-downloader/discussions)
- 想改进代码？直接提交 PR

---

## 📜 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

<div align="center">

如果本项目对你有帮助，请点个 ⭐ **Star** 支持一下！

[![Star History Chart](https://api.star-history.com/svg?repos=HitTheStars/chaoxing-pdf-downloader&type=Date)](https://star-history.com/#HitTheStars/chaoxing-pdf-downloader&Date)

</div>
