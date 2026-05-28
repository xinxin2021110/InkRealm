# 墨韵书境 InkRealm

> 与古今笔下角色,共谱传奇 — 基于 `novel_character_agent` 与 `novel_story_agent` 两套核心算法的全栈 Web 应用。

## 总览

```
webapp/
├── backend/                FastAPI + SQLite + SQLAlchemy
│   ├── app/
│   │   ├── main.py         FastAPI 入口
│   │   ├── config.py       密钥/路径配置 (DeepSeek API key 已写死)
│   │   ├── database.py     SQLite + ORM
│   │   ├── models/         Novel / Character / ChatSession / Story / Chapter
│   │   ├── schemas/        Pydantic 输入输出
│   │   ├── api/            novels.py · chat.py · stories.py
│   │   └── services/       直接调用 novel_character_agent / novel_story_agent
│   ├── run.py              开发模式启动
│   └── requirements.txt
├── frontend/               React 18 + Vite + TS + Tailwind + Zustand + Framer
│   ├── src/
│   │   ├── pages/          11 个页面 (首页/书架/详情/上传/会话/聊天/创建/大纲/章节/我的故事)
│   │   ├── components/     Layout / LoadingScroll / InkLogo / ...
│   │   ├── api/            axios 封装的接口客户端
│   │   ├── hooks/          useTypewriter (打字机效果)
│   │   └── store/          Zustand 状态
│   └── package.json
└── data/                   运行时数据 (自动创建)
    ├── inkrealm.db         SQLite
    ├── novels/             上传的 jsonl 文件副本
    ├── cache/              小说分析缓存 (世界观/风格/人设)
    ├── stories/            (保留)
    ├── exports/            导出的故事 txt
    └── uploads/            (临时)
```

## 一键启动

需要 Python ≥ 3.10 与 Node ≥ 18。

### 1. 安装

```bash
# 算法包依赖
cd /Users/xinxin/Desktop/杂事/简心/小说复刻项目/Test3/Test3/MetaGPT复刻_副本
pip install -r requirements.txt           # 旧依赖

# 后端依赖
cd webapp/backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

### 2. 启动 (开发模式 — 前后端各一个端口,带热更新)

**Terminal 1 — 后端 (8000)**
```bash
cd webapp/backend
python run.py
```

**Terminal 2 — 前端 (5173)**
```bash
cd webapp/frontend
npm run dev
```

打开 http://localhost:5173

> Vite 已配置代理,前端 `/api/*` 自动转发到后端 8000。
> 启动时后端自动把仓库根的《武动乾坤》天蚕土豆.jsonl 注册为示例小说,
> 第一次进入「共谱华章」时会调 LLM 做小说分析(20-40 秒),后续读缓存。

### 3. 生产模式 (单端口部署)

```bash
cd webapp/frontend && npm run build
cd ../backend && python run.py
# 浏览器打开 http://localhost:8000
```

后端 main.py 在 `frontend/dist/` 存在时会自动托管前端 SPA 与 fallback 路由,
此时所有访问 (前端 + API) 共用 8000 端口,无需 nginx。

## 核心功能

### 📚 小说中心
- 卡片式书架,展示所有可用小说
- 点击进入详情页,展示该书所有可玩角色 (含主角金冠标记)
- 支持上传 .jsonl 角色信息库 (拖拽 / 点击, ≤ 50MB)
- 删除小说会级联清除其角色/会话/故事

### 💬 墨笺对谈 (角色聊天)
- 每个角色一个会话,左卷轴右简牍的拟物消息样式
- 用户消息 (楷体 · 藕粉简牍) / 角色消息 (宋体 · 卷轴附朱砂边)
- **角色回复带打字机逐字效果** (`useTypewriter`)
- **每次响应**: 检索 100+ 真实语录 + 相关记忆 (右上角显示统计)
- 抽屉式角色资料: 性格 / 说话风格 / 关系 / 经典语录
- 支持导出 txt / 删除会话

### ✍️ 共谱华章 (故事共创)
6 步向导构建你的角色:
1. **出身** - LLM 按选定主角实时生成 4 个出身选项
2. **性格** - 4 种性格倾向
3. **羁绊** - 与主角的初始关系
4. **能力** - 在修炼体系中的特长
5. **取名** - 给自己一个响亮名字
6. **篇幅** - 3-20 章的可选区间

确认后:
- 自动调用 `OutlineGenerator` 生成完整故事大纲
- 进入大纲页可逐章展开查看
- 进入阅读器读章节,**风格强对齐原著** (天蚕土豆体)
- 章节末弹层显示 4 个互动选项 (友善 / 竞争 / 独立 / 情感)
- 选项触发关系值变化、剧情标记、实力等级提升
- 任意章节可【重写】重新生成
- 导出整部故事为 txt

### 🗂️ 我的故事
- 横向卡片列出所有进行中 / 已完结的故事
- 显示进度、实力、关系值、最近更新
- 一键继续 / 阅读 / 导出 / 删除

## 主要 API (FastAPI 自动文档: /docs)

```
GET    /api/v1/health
# 小说
GET    /api/v1/novels
POST   /api/v1/novels                          (multipart 上传)
GET    /api/v1/novels/{id}
DELETE /api/v1/novels/{id}
GET    /api/v1/characters/{id}
# 聊天
GET    /api/v1/chat/sessions
POST   /api/v1/chat/sessions
GET    /api/v1/chat/sessions/{id}
DELETE /api/v1/chat/sessions/{id}
POST   /api/v1/chat/sessions/{id}/messages     (核心:发消息)
GET    /api/v1/chat/sessions/{id}/export
# 故事
GET    /api/v1/stories
POST   /api/v1/stories                         (创建并生成第 1 章)
GET    /api/v1/stories/{id}
DELETE /api/v1/stories/{id}
GET    /api/v1/stories/persona-options/{novel_id}/{character_id}
POST   /api/v1/stories/{id}/chapters/{n}/choose
POST   /api/v1/stories/{id}/chapters/{n}/regenerate
GET    /api/v1/stories/{id}/export
```

## 设计风格 (墨韵古风)

| 主色 | 色值 |
|---|---|
| 宣纸白 | `#F5F0E6` |
| 米白 | `#FAF6F0` |
| 墨色 | `#3D2914` |
| 浅墨 | `#8B4513` |
| 朱砂 | `#CD5C5C` |
| 金箔 | `#D4AF37` |
| 竹青 | `#2F4F4F` |
| 藕粉 | `#E8D4C4` |

字体:Noto Serif SC (正文) · Ma Shan Zheng (楷体对话) · 通过 Google Fonts CDN 自动加载。

视觉元素:
- **卷轴消息框**: `.scroll-bubble` 带朱砂左缘和木轴两端
- **简牍消息框**: `.bamboo-bubble` 带横纹理
- **印章按钮**: `.seal` 朱砂底白字
- **古籍页**: `.ancient-page` 暖黄底+噪点
- **金线分隔**: `.gold-divider` 顶导航底
- **打字机光标**: 角色回复时的闪烁竖线

## 与现有算法包的关系

后端 `webapp/backend/app/services/__init__.py` 启动时:
1. 把仓库根 (含 `novel_character_agent/` 与 `novel_story_agent/`) 注入 `sys.path`
2. 调用两个算法包的 `init_config(api_key, base_url, model)` 同步密钥

各 service 直接 import 算法包对象:
- `chat_service` 用 `NovelCharacter.from_data_file` 实例化角色,缓存在内存,
  发送消息时回灌历史 -> 调 `engine.respond(text)`
- `story_service` 用 `NovelAnalyzer / UserPersonaBuilder / OutlineGenerator
   / ChapterWriter / ChoiceGenerator`,小说分析结果磁盘缓存 (`data/cache/`)

## 备注

- DeepSeek API key 已按用户要求**写死**在 `app/config.py`
- SQLite 默认在 `webapp/data/inkrealm.db`,首次运行自动建表并注册示例
- 章节生成耗时 20-40 秒/章 (LLM 调用),前端会显示 LoadingScroll 全屏遮罩
- 仅支持中文,默认浏览器宽度 ≥ 1024px (PC 优先,平板可读,移动暂未优化)
