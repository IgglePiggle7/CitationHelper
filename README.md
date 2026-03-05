---
title: Citation Helper
emoji: 🐨
colorFrom: red
colorTo: blue
sdk: gradio
sdk_version: 6.6.0
app_file: app.py
pinned: false
license: mit
---

# 🎓 多功能学术文献引用助手 (Citation Helper)

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Gradio](https://img.shields.io/badge/Gradio-6.6.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

欢迎来到 **Citation Helper**！这是一个专为科研人员、学者和学生打造的开源学术工具。它旨在解决论文写作过程中繁琐的两个痛点：**标准引用格式的生成** 和 **Word 正文引用标号的乱序重排**。

无论是严格的国标 `GB/T 7714-2015`，还是 `APA`、`IEEE`，只需输入论文标题，大模型便会自动为你精准生成。

---

## 🌟 核心功能

### 🔍 1. 智能文献引用生成器 (基于 SerpApi + LLM)
- **精准联网检索**：底层接入 SerpApi (Google Scholar) 接口，抓取最全面、准确的文献元数据（包含严格的卷期号）。
- **大语言模型格式化**：调用大模型（默认使用免费强大的 Qwen2.5-72B-Instruct）将元数据完美重写为目标格式。
- **支持多种学术规范**：
  - GB/T 7714-2015 (严格遵循等、et al. 及半角标点规则)
  - APA 7th Edition
  - MLA 9th Edition
  - IEEE
  - Chicago (Bibliography)
  - BibTeX
- **自带防刷爆机制 (BYOK)**：支持用户在前端“高级设置”中填入自己的 SerpApi Key 或 大模型 API Key，避免公共额度耗尽。
- **会话历史记录**：在网页会话期间，自动保存并折叠展示你的历史生成记录。

### 📝 2. Word 引用乱序自动重排 (纯本地算法)
- **解决痛点**：在论文反复修改、增删段落后，文中的 `[5, 1-3]` 等引用标号往往会彻底乱序。
- **一键重排**：上传包含乱序标号的 `.docx` 文档，并粘贴原始参考文献列表。工具会通过纯 Python 算法，根据正文出现的先后顺序，自动将标号整理为 `[1],[2], [3]` 格式。
- **自动生成附录**：将重排后的参考文献列表自动追加到 Word 文档末尾，并提供新文档下载。
- **隐私安全**：该功能为纯本地化运算，不调用任何外部 API，彻底保障未发表论文的隐私安全。

---

## 📂 优雅的工程目录结构

本项目采用了彻底解耦的架构设计，UI 层、配置层与业务逻辑层完全分离，极易二次开发与扩展：

```text
CITATIONHELPER/
├── app.py               # Gradio 前端界面主入口
├── config.py            # 全局配置、默认参数与环境变量管理
├── requirements.txt     # 项目 Python 依赖库
├── utils.py             # 通用辅助函数 (如历史记录 Markdown 渲染)
└── services/            # 核心业务逻辑层
    ├── citation.py      # SerpApi 网络检索与 LLM 生成逻辑
    └── document.py      # python-docx 文档解析与引用标号重排算法
```

---

## 🚀 本地运行与部署指南

如果你想在本地计算机上运行该项目，请按照以下步骤操作：

### 1. 克隆代码库
```bash
git clone https://huggingface.co/spaces/IgglePiggle777/CitationHelper
cd CitationHelper
```

### 2. 创建并激活虚拟环境 (推荐)
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
如果你想使用系统的默认调用池，请在系统环境变量或 `.env` 文件中配置以下两项（如果在 Hugging Face Space 上部署，请在 `Settings -> Secrets` 中添加）：
- `SERPAPI_KEY`: 你的 SerpApi 密钥（用于 Google Scholar 检索）。
- `HF_TOKEN`: 你的 Hugging Face Access Token（用于调用免费开源大模型）。

### 5. 启动应用
```bash
python app.py
```
终端会输出一个本地链接（通常为 `http://127.0.0.1:7860`），点击即可在浏览器中访问。

---

## 🤝 贡献与支持
如果你在使用过程中遇到任何 Bug，或者有添加新功能（例如 PDF 解析、更多引用格式）的好点子，欢迎在这个 Space 的 Community 页面提出建议或提交 Pull Request。

如果这个工具对你的学术写作有帮助，别忘了给它点个赞 (❤️ Like) ！