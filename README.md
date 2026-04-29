# 📚 Chaoxing PDF Downloader

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Playwright-1.40%2B-green" alt="Playwright 1.40+">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License: MIT">
</p>

<p align="center">
  <b>超星学习通 PDF 批量下载器</b> —— 一键下载课程中「不可下载」的 PDF 课件
</p>

---

## ✨ 功能特性

- 🔍 **自动嗅探**：自动扫描当前课程页面中的所有 PDF 资源，无需手动查找链接
- 🛡️ **绕开限制**：针对「无下载按钮」或「下载按钮被禁用」的 PDF，从云盘预览页源码中提取真实下载链接
- 🍪 **持久登录**：基于 Chrome DevTools Protocol (CDP) + 持久化用户目录，登录一次，长期有效
- 📂 **智能命名**：自动从 URL 中提取原始文件名，支持自动重名处理
- 🚀 **简单易用**：仅需两条命令，即可完成从登录到下载的全过程

---

## 📖 原理说明

超星学习通的课程 PDF 通常通过以下两种方式嵌入：

| 类型 | 说明 | 本工具的处理方式 |
|------|------|----------------|
| **云盘预览页** (`pan-yz.chaoxing.com`) | PDF 托管在超星云盘，页面通过 iframe 嵌入预览 | 读取 iframe 的 HTML 源码，正则提取 `*/download/*` 真实直链，并在 iframe 内触发点击，保证 Referer 正确 |
| **PDF Viewer** (`/ananas/modules/pdf/...`) | 基于 PDF.js 的内置阅读器 | 提取 `#downloadUrl` 元素的 `href` 属性，若未被禁用则直接点击下载 |

下载链接包含时效性签名参数（`at_`, `ak_`, `ad_`），直接复制到浏览器外访问会返回 `403`。本工具通过在**对应的 iframe 上下文内**触发下载，确保请求携带正确的 Cookie 和 Referer，从而绕开验证。

---

## 🖼️ 效果预览

<!-- 建议替换为实际截图 -->
```text
[*] 正在扫描页面中的 PDF 资源...
[*] 共 33 个 frames

[Frame 12] 云盘预览页  file_id=9a779462583d289b458edc6073399a62
  └─ 发现下载链接 -> 第1讲软硬件介绍.pdf
[Frame 17] 云盘预览页  file_id=08b15335d3f665287f4b26775afd1d1d
  └─ 发现下载链接 -> 第1讲GPIO.pdf
[Frame 22] 云盘预览页  file_id=d3328256c45f30ed7bc2f6ac7106729d
  └─ 发现下载链接 -> 第2讲定时器.pdf

[*] 共发现 5 个 PDF，开始下载...

[↓] 开始下载: 第1讲软硬件介绍.pdf
    ✓ 成功 (4,988,243 bytes)
...
[*] 全部完成: 5/5 成功
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（仅需一次）
playwright install chromium
```

或使用 `uv`：
```bash
uv pip install -r requirements.txt
python -m playwright install chromium
```

### 2. 首次使用：启动浏览器并登录

```bash
python src/chaoxing_pdf_downloader.py --launch
```

- 系统会弹出一个 Chrome 窗口
- **手动登录**你的超星学习通账号
- 登录完成后，在终端按 `Ctrl+C` 结束进程
- 浏览器会继续在后台运行，登录状态保存在 `/tmp/chaoxing_profile`

### 3. 下载 PDF

在浏览器中打开你想下载的课程章节，然后执行：

```bash
python src/chaoxing_pdf_downloader.py --download
```

下载的文件默认保存在 `~/Downloads` 目录。

---

## ⚙️ 命令行参数

```bash
python src/chaoxing_pdf_downloader.py [选项]
```

| 参数 | 说明 | 示例 |
|------|------|------|
| `--launch` | 启动持久化浏览器（首次使用） | `--launch` |
| `--download` | 连接浏览器并下载当前页面所有 PDF | `--download` |
| `--profile` | Chrome 用户数据目录 | `--profile /tmp/my_profile` |
| `--output` | PDF 保存目录 | `--output ./my_pdfs` |
| `--cdp` | CDP 调试地址 | `--cdp http://localhost:9222` |

### 完整示例

```bash
# 启动浏览器（登录一次）
python src/chaoxing_pdf_downloader.py --launch

# 下载到指定目录
python src/chaoxing_pdf_downloader.py --download --output ./course_pdfs
```

---

## 📁 项目结构

```
chaoxing-pdf-downloader/
├── src/
│   └── chaoxing_pdf_downloader.py   # 主程序
├── requirements.txt                 # Python 依赖
├── .gitignore                       # Git 忽略配置
├── LICENSE                          # MIT 许可证
└── README.md                        # 本文件
```

---

## ❓ 常见问题

### Q1: 提示 "浏览器已启动但 CDP 端口 9222 不可用"
确保之前运行过 `--launch` 且浏览器进程没有被手动关闭。如果关闭了，重新运行 `--launch` 即可。

### Q2: 下载失败，提示签名过期
下载链接的签名（`at_`, `ak_`, `ad_`）有几分钟的有效期。**刷新课程页面**后重新运行 `--download` 即可获取新的签名。

### Q3: 某些章节扫描不到 PDF
本工具目前支持以下两种常见的 PDF 嵌入方式：
- `pan-yz.chaoxing.com` 云盘预览页
- `/ananas/modules/pdf/index.html` 内置阅读器

如果课程使用了其他方式（如纯图片预览、第三方 Office 在线预览等），本工具暂时无法识别。

### Q4: 如何批量下载整门课的所有章节？
目前需要**手动切换章节**后重复运行 `--download`。自动遍历章节列表的功能尚在开发中，欢迎提交 PR！

---

## ⚠️ 免责声明

本项目仅供学习和技术研究使用，请勿用于任何商业或非法用途。

使用本工具下载的内容版权归原作者及超星学习通平台所有。请尊重知识产权，在合理范围内使用下载的课件资料。因使用本工具而产生的任何法律责任，由使用者自行承担。

---

## 📜 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=HitTheStars/chaoxing-pdf-downloader&type=Date)](https://star-history.com/#HitTheStars/chaoxing-pdf-downloader&Date)

> 如果本项目对你有帮助，请点个 ⭐ Star 支持一下！
