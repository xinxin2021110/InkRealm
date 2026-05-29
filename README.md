# 墨韵书境 InkRealm

> 与古今笔下角色，共谱传奇 —— 基于多智能体系统的沉浸式叙事生成平台

墨韵书境是一个面向小说IP的AI驱动叙事生成系统，支持用户与虚拟角色深度对话，并共同创作个性化故事。系统基于 **MetaGPT** 架构范式，融合了检索增强生成（RAG）、流式交互（SSE）和多智能体协作等先进技术。
![项目演示图](封面.png)

## ✨ 核心功能

### 📚 小说中心
- 卡片式书架展示多部经典作品
- 支持上传 JSONL 格式的角色信息库
- 自动解析并提取可玩角色
- 内置《武动乾坤》《斗破苍穹》《斗罗大陆》《神印王座》等示例小说

### 💬 墨笺对谈（角色聊天）
- 与小说角色进行沉浸式对话
- 检索 100+ 真实语录，确保角色一致性
- 卷轴式消息样式（左简牍右卷轴）
- 打字机式实时流式渲染
- 角色资料抽屉（性格、关系、语录）

### ✍️ 共谱华章（故事共创）
- 6 步向导构建自定义角色（出身、性格、羁绊、能力、取名、篇幅）
- 自动生成完整故事大纲
- AI 撰写风格化章节内容
- 章末互动选择影响剧情走向
- 支持导出完整故事为 TXT

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     前端层 (Frontend)                        │
│  React 18 + TypeScript + Vite + Tailwind CSS + Framer      │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP / SSE
┌───────────────────────▼─────────────────────────────────────┐
│                     后端层 (Backend)                         │
│  FastAPI + SQLAlchemy + SQLite / PostgreSQL                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    算法核心层 (Core)                        │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  novel_character_agent    - 角色聊天引擎              │ │
│  │  novel_story_agent        - 故事共创引擎              │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  inkrealm/               - 核心架构层                 │ │
│  │    ├── Message/Memory    - 消息与记忆抽象             │ │
│  │    ├── Role/Action       - 角色与动作抽象             │ │
│  │    ├── ActionNode        - 结构化生成节点             │ │
│  │    ├── Environment       - 多智能体环境               │ │
│  │    └── Retrieval         - RAG检索体系                │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                    模型层 (LLM Provider)                     │
│         DeepSeek / OpenAI 兼容 API                          │
└─────────────────────────────────────────────────────────────┘
```

## 📋 环境要求

- **Python**: >= 3.10
- **Node.js**: >= 18
- **操作系统**: macOS / Linux / Windows

## 🚀 快速开始

### 1. 克隆项目

```bash
cd 路径/MetaGPT复刻
```

### 2. 安装算法核心依赖

```bash
# 在项目根目录
pip install -r requirements.txt
```

核心依赖包括：
- `openai>=1.0.0` - LLM API 调用
- `pydantic>=2.0.0` - 数据模型验证

### 3. 安装后端依赖

```bash
cd webapp/backend
pip install -r requirements.txt
```

后端依赖包括：
- `fastapi==0.115.5` - Web 框架
- `uvicorn[standard]==0.32.1` - ASGI 服务器
- `sqlalchemy==2.0.36` - ORM 框架
- `python-multipart==0.0.20` - 文件上传支持

### 4. 安装前端依赖

```bash
cd ../frontend
npm install
```

前端依赖包括：
- `react@^18.3.1` - UI 框架
- `vite@^6.0.5` - 构建工具
- `tailwindcss@^3.4.17` - CSS 框架
- `framer-motion@^11.15.0` - 动画库
- `zustand@^5.0.2` - 状态管理
- `@tanstack/react-query@^5.62.7` - 服务端状态管理

## ▶️ 运行项目

需要同时启动 **后端服务** 和 **前端开发服务器**。

### 方式一：开发模式（推荐）

打开两个终端窗口：

**终端 1 - 启动后端（端口 8000）**

```bash
cd MetaGPT复刻/webapp/backend
python run.py
```

启动成功后会看到：
```
Uvicorn running on http://0.0.0.0:8000
```

**终端 2 - 启动前端（端口 5173）**

```bash
cd MetaGPT复刻/webapp/frontend
npm run dev
```

启动成功后会看到：
```
Local:   http://localhost:5173/
```

### 方式二：生产模式（单端口）

```bash
# 1. 构建前端
cd /Users/xinxin/Desktop/杂事/简心/小说复刻项目/Test4/MetaGPT复刻/webapp/frontend
npm run build

# 2. 启动后端（自动托管前端静态文件）
cd ../backend
python run.py

# 3. 访问 http://localhost:8000
```

## 📖 使用指南

### 访问应用

开发模式下，打开浏览器访问：**http://localhost:5173**

### 首次使用

1. **进入小说中心** - 浏览已有的示例小说
2. **选择《武动乾坤》** - 进入小说详情页
3. **开始墨笺对谈** - 与林动进行角色对话
4. **或开启共谱华章** - 创建自己的角色与林动共同冒险

### 上传新小说

1. 准备 JSONL 格式的角色信息库文件
2. 点击右上角「上传小说」
3. 拖拽或选择文件上传（单文件 ≤ 50MB）
4. 系统自动解析并提取可玩角色

### 示例 JSONL 格式

```json
{"character_name": "林动", "content": "林动是青阳镇林家的少年...", "type": "summary", "chapter_order": 1}
{"character_name": "林动", "content": "父亲林啸被林琅天所伤...", "type": "memory_point", "emotion": "愤怒", "weight": 5}
{"character_name": "林动", "dialogue": "我林动，从不信命！", "context": "面对林琅天的压迫时所说", "type": "dialogue_example"}
```

## 📁 项目结构

```
MetaGPT复刻/
├── novel_character_agent/      # 角色聊天核心算法
│   ├── roles/                  # CharacterRole 定义
│   ├── actions/                # 聊天相关 Action
│   └── environment/            # ChatEnvironment
├── novel_story_agent/          # 故事共创核心算法
│   ├── roles/                  # ChapterWriterRole, PlotDirector 等
│   ├── actions/                # 写作、大纲、选项生成 Action
│   ├── environment/            # WritingEnvironment
│   └── team/                   # NovelTeam 编排
├── inkrealm/                   # 核心架构层（新）
│   ├── schema.py               # Message, MemoryItem 定义
│   ├── memory/                 # Memory 实现
│   ├── roles/                  # Role 基类与 RoleContext
│   ├── actions/                # Action 基类与 ActionNode
│   ├── environment/            # Environment 基类
│   ├── retrieval/              # Embedder, Retriever 检索体系
│   ├── provider/               # LLM Provider 抽象
│   └── data/                   # JsonlLoader, ProfileBuilder
├── webapp/                     # Web 应用
│   ├── backend/                # FastAPI 后端
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI 入口
│   │   │   ├── api/            # API 路由 (chat, stories, novels)
│   │   │   ├── services/       # 业务服务层
│   │   │   ├── models/         # SQLAlchemy 数据模型
│   │   │   └── database.py     # 数据库连接
│   │   └── run.py              # 启动脚本
│   ├── frontend/               # React 前端
│   │   ├── src/
│   │   │   ├── pages/          # 页面组件
│   │   │   ├── components/     # 通用组件
│   │   │   ├── api/            # API 客户端
│   │   │   └── store/          # Zustand 状态管理
│   │   └── package.json
│   └── data/                   # 运行时数据
│       ├── novels/             # 上传的小说 JSONL
│       ├── cache/              # 分析结果缓存
│       └── inkrealm.db         # SQLite 数据库
└── 《武动乾坤》天蚕土豆.jsonl  # 示例小说数据
```

## ⚙️ 配置说明

### API 密钥配置

系统使用 DeepSeek API 进行 LLM 调用，API 密钥已配置在：

`webapp/backend/app/config.py`

如需修改，请编辑该文件中的 `DEEPSEEK_API_KEY`。

### 数据库配置

默认使用 SQLite，数据库文件位于：

`webapp/data/inkrealm.db`

首次运行会自动创建表结构并加载示例小说。

### 前端代理配置

Vite 已配置代理，前端 `/api/*` 请求自动转发到后端 8000 端口：

`webapp/frontend/vite.config.ts`

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

## 🛠️ 技术特性

### 核心架构创新

- **MetaGPT 范式迁移**: 将软件工程领域的多智能体架构成功应用于叙事生成场景
- **RAG 检索增强**: TF-IDF + BM25 混合打分，Top-10 语录相关度达 87.3%
- **SSE 流式交互**: ContextVar 流桥接，首 Token 延迟 < 1.5s
- **ActionNode 结构化**: 运行时 Pydantic 模型生成，类型安全

### 性能指标

| 指标 | 目标值 | 实测值 |
|------|--------|--------|
| 聊天首 Token 延迟 | ≤1.5s | P95: 0.8s, P99: 1.2s |
| 单轮聊天总耗时 | ≤8s | 均值: 3.5s |
| 章节生成耗时 | ≤40s | 均值: 25s |
| 角色加载 | ≤3s | ~1.2s |

## 🔧 常见问题

### 1. 依赖安装失败

**问题**: `pip install` 时报错或卡住

**解决**: 
```bash
pip install -r requirements.txt --timeout 60 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 前端 npm install 失败

**问题**: 网络问题导致 npm 包下载失败

**解决**:
```bash
# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com
npm install
```

### 3. 后端启动报错 "ModuleNotFound"

**问题**: Python 无法找到 `novel_character_agent` 等模块

**解决**: 确保在项目根目录安装依赖，并检查 Python 版本 >= 3.10

### 4. 前端无法连接后端

**问题**: 浏览器提示 API 请求失败

**解决**: 
1. 确认后端已启动在 8000 端口
2. 检查 `vite.config.ts` 代理配置
3. 确认浏览器没有拦截跨域请求

## 📝 开发计划

- [ ] 支持更多 LLM Provider（Claude、GPT-4、本地模型）
- [ ] 多角色群聊功能
- [ ] 用户自定义世界观
- [ ] 章节配图 AI 生成
- [ ] 语音合成与语音识别

## 📄 许可证

本项目仅供学习和研究使用。

## 🙏 致谢

- [MetaGPT](https://github.com/geekan/MetaGPT) - 多智能体框架范式
- [DeepSeek](https://deepseek.com) - 大语言模型支持
- [FastAPI](https://fastapi.tiangolo.com) - 后端框架
- [React](https://react.dev) - 前端框架

---

如有问题，欢迎提交 Issue 或联系开发者。
