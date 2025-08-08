# AIDD Paper Tracker

**AIDD Paper Tracker**: 一个用于跟踪和管理AI药物发现相关学术论文的全栈应用系统。

## 项目概述

AIDD Paper Tracker 是一个专门用于自动化收集、管理和分析AI药物发现相关学术论文的系统。它集成了多个预印本服务器（arXiv、bioRxiv、ChemRxiv），提供了现代化的Web界面来浏览、过滤和标记论文的相关性。

### 主要功能

- **自动化论文获取**: 从 arXiv、bioRxiv、ChemRxiv 自动抓取相关论文
- **智能分类筛选**: 支持按来源、分类、日期范围和关键词进行多维度筛选
- **相关性标记**: 可以标记论文为相关/不相关，便于后续分析
- **现代化界面**: 基于 React + TypeScript 的响应式Web界面
- **全文搜索**: 支持在标题、摘要、作者中搜索关键词
- **统计分析**: 提供论文数量、相关性等统计信息
- **数据持久化**: SQLite数据库存储，支持JSON备份

## 技术架构

- **FastAPI**
- **React**
- **TypeScript**
- **Vite**
- **Tailwind CSS**
- **shadcn/ui**
- **SQLite**

## 数据来源
- **arXiv**: cs.LG, cs.AI, q-bio, physics.chem-ph
- **bioRxiv**: biochemistry, bioinformatics, biophysics, synthetic biology
- **ChemRxiv**: Theoretical and Computational Chemistry, Biological and Medicinal Chemistry

## 安装和设置

### 前置要求

- **Conda** (Miniconda 或 Anaconda) - [下载链接](https://docs.conda.io/en/latest/miniconda.html)
- **Node.js 18+** - [下载链接](https://nodejs.org/)
- **npm** (随Node.js一起安装)

### 快速开始

1. **克隆项目**
   ```bash
   git clone https://github.com/xli7654321/AIDD-Paper-Tracker.git
   cd AIDD-Paper-Tracker
   ```

2. **一键启动与conda环境管理** (推荐)
   ```bash
   python run.py
   ```
   
   这个增强版脚本会自动：
   - **检查conda安装**
   - **创建conda环境** `aidd-tracker`，使用Python 3.10 (如果不存在)
   - **在conda环境中安装Python依赖**
   - **检查Node.js和npm可用性**
   - **安装前端依赖**
   - **创建必要的目录** (data, logs)
   - **启动后端和前端服务器**

3. **访问应用**
   - 前端界面: http://localhost:5173
   - 后端API: http://localhost:8000
   - API文档: http://localhost:8000/docs

### 手动安装 (可选)

如果您想要分别安装和启动服务：

1. **创建并激活conda环境**
   ```bash
   conda create -n aidd-tracker python=3.10
   conda activate aidd-tracker
   ```

2. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装前端依赖**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **启动后端服务**
   ```bash
   cd backend
   python run_server.py
   ```

5. **启动前端服务** (另开一个终端)
   ```bash
   cd frontend
   npm run dev
   ```

## 使用指南

### 更新论文数据

1. **通过Web界面**
   - 在主界面点击"Update Papers"按钮
   - 选择要更新的数据源（arXiv、bioRxiv、ChemRxiv）
   - 设置日期范围和分类筛选
   - 点击更新开始数据抓取

2. **通过API**
   ```bash
   curl -X POST "http://localhost:8000/papers/update" \
        -H "Content-Type: application/json" \
        -d '{
          "sources": ["arxiv"],
          "categories": ["cs.LG", "q-bio"],
          "start_date": "2025-06-01",
          "end_date": "2024-06-08"
        }'
   ```

## 项目结构

```
AIDD-Paper-Tracker/
├── backend/                    # 后端FastAPI应用
│   ├── main.py                # FastAPI主应用
│   └── run_server.py          # 后端服务器启动脚本
├── frontend/                   # React前端应用
│   ├── src/
│   │   ├── components/        # React组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API服务
│   │   └── types/            # TypeScript类型定义
│   ├── package.json          # 前端依赖配置
│   └── vite.config.ts        # Vite构建配置
├── data/                      # 数据存储目录
│   ├── papers.db             # SQLite数据库
│   └── papers.json           # JSON备份文件
├── logs/                      # 日志文件目录
├── arxiv_fetcher.py          # arXiv数据抓取器
├── biorxiv_fetcher.py        # bioRxiv数据抓取器
├── chemrxiv_fetcher.py       # ChemRxiv数据抓取器
├── database.py               # 数据库管理模块
├── data_processor.py         # 数据处理模块
├── config.py                 # 配置文件
├── requirements.txt          # Python依赖
├── run.py                    # 一键启动脚本
└── README.md                 # 项目说明文档
```

## 常见问题

1. **端口占用**: 确保8000和5173端口未被占用
2. **依赖问题**: 运行 `pip install -r requirements.txt` 重新安装依赖
3. **数据库错误**: 删除 `data/papers.db` 让系统重新创建
4. **网络问题**: 确保网络连接正常，某些地区可能需要代理访问

## 许可证

本项目采用MIT许可证。

## 致谢

本项目的代码几乎都是由Claude Code和Lovable开发，感谢他们的贡献。

---

*如果您觉得这个项目对您有帮助，请考虑给它一个⭐！*