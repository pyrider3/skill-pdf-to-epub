# 📖 skill-pdf-to-epub

> **Publishing-grade, responsive PDF to EPUB 3 / EPUB 2 conversion skill & toolkit for AI coding agents and human creators.**
> 专为 AI 编程 Agent（Antigravity、Claude Code、Cursor 等）及数字化出版者打造的出版级 PDF 转 EPUB 技能套件。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![EPUB 3 & 2 Compatible](https://img.shields.io/badge/EPUB-3%20%26%202%20Compatible-orange.svg)](http://idpf.org/epub/30)
[![Dark Mode Supported](https://img.shields.io/badge/Style-Dark%20Mode-9cf.svg)](#)

---

## 🎯 痛点与解决方案 (Why This Skill?)

传统的 PDF 转 EPUB 工具（如 Calibre `ebook-convert`、Pandoc 或未经几何引导的 `pdftotext`）在处理复杂中文排版或学术/图书 PDF 时，往往会产生极其恶劣的排版灾难：

1. **断句粉碎**：PDF 中的每一行物理折行都被转换成硬回车 `<p>`，整本书被撕成断头断尾的短句。
2. **孤立标点（Orphan Punctuation）**：段落或行首频繁出现逗号、句号、引号、叹号（如 `，进行放大化`、`。`、`”`）。
3. **顶底眉脚串文**：每页顶部的页眉、底部的页码和版权声明直接混入正文段落中。
4. **跨页脚注绞杀**：段落跨页时，上一页底部的脚注直接插在下一页句子的正中央。
5. **中文字符间散落空格**：PDF 两端对齐算法在汉字之间注入了大量无意义空格（如 `建 模 之 后`）。
6. **图像与图表丢失**：公式、雷达图、思维导图、全彩封面被压烂或直接丢失。

**`skill-pdf-to-epub`** 通过**几何空间坐标分类（Geometric Classification）**与**语义重组管道**，彻底解决以上所有顽疾，输出达到真正数字出版标准的精美 EPUB 电子书。

---

## ✨ 核心特性 (Key Features)

* **🛡️ 零孤立标点保证（Zero-Orphan Punctuation）**：
  内置严格的标点回卷与跨页断句熔接算法，在构建产物中自动断言：`^[，。、；：？！’”’）》』]` 开头的自然段数量必须为 **0**。
* **⚡ 毫秒级坐标解析（Coordinate Space Extraction）**：
  采用 `pdftotext -bbox-layout`，百页 PDF 仅需 0.1 秒即可获取每个字块的精确物理边界（`xMin`, `yMin`, `xMax`, `yMax` 与字号高度），精准剔除页眉页脚与提取双向脚注。
* **🖼️ 300 DPI 超清重采样封面与无损插图**：
  * `pdftoppm -r 300` 渲染 Page 1 获得锐利超清封面。
  * `pdfimages -png` 无损倾倒所有内置矢量/栅格插图、战术图表、雷达图、公式图，杜绝二次压缩失真。
* **🈳 智能 CJK 空格清洗与连字优化**：
  清洗对齐注入的汉字间无意义空格，智能保留英文字词、数字、Markdown 代码间的合法空格。
* **🌓 完美适配暗黑模式（Dark Mode Ready）**：
  配套专业 EPUB 主样式表，兼容 Apple Books、Kindle、微信读书、多看、Kobo、Thorium 等主流阅读器的浅色、护眼及夜间模式切换。
* **🧭 双标准导航体系（Dual Navigation）**：
  同时配备 EPUB 3 `nav.xhtml`（含 `landmarks`）与 EPUB 2 `toc.ncx`，兼顾最新现代阅读器与老旧墨水屏设备。
* **🔍 6 关卡严苛自动化质量验收（6-Gate Verification Suite）**：
  * 压缩格式校验（`mimetype` 必须为未压缩 `ZIP_STORED` 第一项）
  * XML 解析（所有 XHTML/XML/OPF/NCX 100% 格式合法）
  * Manifest 清单完整性（绝无悬空或漏标资产）
  * 图像链接解析（所有 `<img>` 标签精准指向有效图片）
  * 孤立首标点扫描（全文所有 `<p>` 标签 0 孤立标点）
  * 双向交互式脚注锚点链接验证

---

## 🏗️ 转换流程图 (Pipeline Architecture)

```
[ Input PDF Document ]
       │
       ├─► pdftoppm -r 300 (Cover rendering) ───────────► OEBPS/Images/cover.png
       ├─► pdfimages -png (Lossless image dump) ────────► OEBPS/Images/fig_*.png
       └─► pdftotext -bbox-layout (0.1s XML stream) ────► Word Bounding Boxes
                                                                │
                                    ┌───────────────────────────┘
                                    ▼
              [ 几何空间分类与降噪 (Geometric Heuristics) ]
              • yMin < Y_HEADER_ZONE ──────► 自动过滤页眉
              • yMin > Y_FOOTER_ZONE ──────► 自动过滤页脚 / 页码
              • yMin > Y_FN & font_h 小 ───► 提取为交互式双向脚注
              • 跨页句首无缩进 ─────────────► 跨页句子无缝连接
                                    │
                                    ▼
                [ CJK 标点断句熔接器 (CJK Unwrapper) ]
              • 剔除汉字间两端对齐空隙
              • 融合跨页硬换行断句（保证单句完整性）
              • 强校验：零首标点孤行
                                    │
                                    ▼
               [ 语义 XHTML 与响应式排版 (Semantic Assembly) ]
              • 引入 master style.css（亮暗主题自适应）
              • 结构化章节头部、诗歌区块 (.verse)、公式框 (.formula-box)、图注
              • 双导航生成：EPUB 3 nav.xhtml + EPUB 2 toc.ncx + 目录页 toc.xhtml
                                    │
                                    ▼
                      [ 打包与自动化验收 (Verify & Pack) ]
              • 未压缩 mimetype 首项写入 (package_epub.py)
              • 6 重关卡自动化质检验收 (verify_epub.py)
```

---

## 🚀 安装与使用 (Installation & Usage)

### 1. 系统依赖项 (System Prerequisites)

本工具依赖系统级 Poppler PDF 工具集：

```bash
# Ubuntu / Debian
sudo apt-get install -y poppler-utils python3

# Arch Linux
sudo pacman -S poppler python

# macOS (Homebrew)
brew install poppler python
```

---

### 2. 作为 AI Coding Agent 技能安装 (Install as Agent Skill)

#### A. 在 Google Antigravity (AGY) 中使用
将本仓库克隆至全局 Skills 目录或项目工作区：

```bash
# 全局安装 (对该机器上所有 Antigravity 会话生效)
git clone https://github.com/pyrider3/skill-pdf-to-epub.git ~/.gemini/config/skills/pdf-to-epub

# 或作为单个项目工作区技能安装
mkdir -p .agent/skills/
git clone https://github.com/pyrider3/skill-pdf-to-epub.git .agent/skills/pdf-to-epub
```

安装后，只需在对话中直接发送 PDF 并对 Agent 说：
> **“帮我把这个 PDF 转成出版级 EPUB”**
Agent 即会自动激活 `pdf-to-epub` 技能，执行全套专业处理流水线。

#### B. 在 Claude Code / Cursor / Windsurf 中使用
将本目录放入项目仓库，并在提示词或 `.cursorrules` / `CLAUDE.md` 中引用 `SKILL.md` 即可。

---

### 3. 作为独立脚本使用 (Standalone CLI Usage)

你也可以直接使用本项目提供的内置脚本完成资产提取、打包与校验：

```bash
# 1. 提取 PDF 封面（300 DPI）、内置插图与坐标数据
python3 scripts/extract_assets.py input.pdf output_assets/

# 2. 将排版好的 build 目录严格打包为标准 EPUB
python3 scripts/package_epub.py epub_build output.epub

# 3. 运行自动化 6 重质量验收
python3 scripts/verify_epub.py output.epub
```

验收通过时将显示：
```
=== Verifying output.epub ===
PASS: Mimetype is valid, uncompressed, and first entry.
PASS: All 20 XML/XHTML files parsed successfully without errors.
PASS: All manifest items exist in archive.
PASS: All image references in XHTML files resolve cleanly.
Inspected 546 paragraphs across all XHTML files.
PASS: 0 paragraphs start with invalid punctuation. Smooth reading flow.
PASS: All footnote references resolve to valid anchors.
=== [✓] output.epub IS PERFECT AND VALID! ===
```

---

## 📂 项目文件结构 (Repository Structure)

```
skill-pdf-to-epub/
├── SKILL.md                          # Agent 核心技能指令与完整工作流定义
├── README.md                         # 详细技术说明与使用指南
├── LICENSE                           # MIT 开源许可证
├── references/
│   └── cjk_geometry_guide.md         # CJK 几何坐标切分与断句算法深度指南
├── resources/
│   └── style.css                     # 出版级通用 EPUB 主样式表（支持 Dark Mode）
└── scripts/
    ├── extract_assets.py             # 封面渲染（300 DPI）、图片与坐标抽取脚本
    ├── package_epub.py               # 符合 IDPF 规范的标准 EPUB 打包脚本
    └── verify_epub.py                # 6 重关卡自动化质检与断句校验脚本
```

---

## 📜 核心算法参考 (Algorithms Overview)

### CJK 空格清除器 (CJK Space Stripper)
```python
import re

cjk = r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]'

def clean_cjk_spaces(text):
    prev = None
    while prev != text:
        prev = text
        text = re.sub(f'({cjk}) +({cjk})', r'\1\2', text)
    text = re.sub(r'([“‘（《【]) +', r'\1', text)
    text = re.sub(r' +([”’）》】])', r'\1', text)
    return text.strip()
```

### 语义行拼接器 (Semantic Line Joiner)
```python
def join_cjk(s1, s2):
    if not s1: return s2
    if not s2: return s1
    # 修复半角逗号
    if s2.startswith(','):
        return s1 + '，' + s2[1:].lstrip()
    # 英文与数字边界保留必要空格
    if re.search(r'[A-Za-z0-9]$', s1) and re.match(r'^[A-Za-z0-9]', s2):
        return s1 + ' ' + s2
    # 中文字符无缝熔接
    return s1 + s2
```

---

## 📄 开源许可证 (License)

本项目基于 [MIT License](LICENSE) 开源。欢迎自由使用、集成于各大 Agent 平台以及贡献改进！
