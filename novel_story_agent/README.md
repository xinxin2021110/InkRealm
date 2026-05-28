# 小说故事续写系统

基于《武动乾坤》等小说数据构建的交互式小说续写系统，让你能够与小说角色（如林动）进行沉浸式互动，共同创作属于你们的故事。

## 核心特性

1. **智能角色分析**: 从原始小说数据中自动提取世界观、角色人设、写作风格
2. **多维人设选择**: 4个维度（出身、性格、关系、能力）构建你的专属角色
3. **动态故事大纲**: AI根据人设生成完整故事框架，主线围绕你与林动的关系发展
4. **风格对齐写作**: 生成章节内容严格模仿原著写作风格（天蚕土豆风格）
5. **互动剧情选择**: 每章提供4个不同方向的互动选项，影响剧情走向
6. **状态追踪系统**: 自动记录关系值、实力等级、剧情标记，保持章节连贯性
7. **故事存档导出**: 支持保存故事进度，导出完整故事文本

## 项目结构

```
novel_story_agent/
├── __init__.py                  # 包入口
├── schema.py                    # 数据模型定义
├── config.py                    # 配置管理
├── main.py                      # 主程序入口
├── data/                        # 数据处理模块
│   ├── __init__.py
│   ├── character_loader.py     # 角色数据加载
│   └── novel_analyzer.py       # 小说数据分析器
├── persona/                     # 人设模块
│   ├── __init__.py
│   └── user_persona_builder.py # 用户人设构建器
├── generation/                  # 内容生成模块
│   ├── __init__.py
│   ├── outline_generator.py    # 大纲生成器
│   ├── chapter_writer.py       # 章节写作器
│   └── choice_generator.py     # 选项生成器
├── story/                       # 故事管理模块
│   ├── __init__.py
│   └── story_state.py          # 故事状态管理器
├── provider/                    # LLM提供商
│   ├── __init__.py
│   └── llm_provider.py         # DeepSeek API封装
└── utils/                       # 工具模块
    └── __init__.py
```

## 安装

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

requirements.txt 内容:
```
openai>=1.0.0
pydantic>=2.0.0
```

### 2. 配置API密钥（可选）

默认使用内置API密钥，如需使用自己的密钥:

```bash
export DEEPSEEK_API_KEY="your-api-key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_MODEL="deepseek-v4-flash"
```

或在代码中配置:

```python
from novel_story_agent.config import init_config

init_config(
    api_key="your-api-key",
    base_url="https://api.deepseek.com",
    model="deepseek-v4-flash",
)
```

## 使用方法

### 快速开始

```bash
# 使用默认数据文件启动
python -m novel_story_agent.main

# 指定参数启动
python -m novel_story_agent.main \
    --data-file "《武动乾坤》天蚕土豆.jsonl" \
    --character "林动" \
    --chapters 5
```

### 交互流程

系统会引导你完成以下步骤:

1. **初始化分析**: 系统自动分析小说数据，提取世界观、角色人设、风格样本
2. **创建人设**: 选择4个维度的选项构建你的角色
   - 维度1: 出身背景 (林家旁系/散修之子/流浪儿/敌对势力)
   - 维度2: 性格倾向 (热血坚毅/机智谋略/温和治愈/神秘冷酷)
   - 维度3: 与主角关系 (童年玩伴/不打不相识/救命恩人/神秘指引者)
   - 维度4: 初始能力 (武学天赋/灵药亲和/妖兽沟通/机关巧手)
3. **确认大纲**: 查看AI生成的故事大纲，确认后开始创作
4. **章节互动**: 每章阅读完后选择互动选项，影响剧情走向
5. **故事完结**: 导出完整故事文本

### 命令行参数

```bash
python -m novel_story_agent.main --help
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--data-file` | 小说数据文件路径 | `《武动乾坤》天蚕土豆.jsonl` |
| `--character` | 目标角色名称 | 数据文件中第一个角色 |
| `--chapters` | 故事章节数 (3-20) | `5` |
| `--api-key` | DeepSeek API Key | 内置密钥 |
| `--base-url` | API Base URL | `https://api.deepseek.com` |
| `--load` | 加载已保存的故事ID | None |

### 代码中使用

```python
import asyncio
from novel_story_agent import (
    NovelAnalyzer,
    UserPersonaBuilder,
    OutlineGenerator,
    ChapterWriter,
    StoryStateManager,
)

async def main():
    # 1. 分析小说数据
    analyzer = NovelAnalyzer("《武动乾坤》天蚕土豆.jsonl")
    analysis = await analyzer.analyze()
    
    print(f"小说: {analysis.character_info.book_title}")
    print(f"主角: {analysis.character_info.name}")
    
    # 2. 生成人设选项
    builder = UserPersonaBuilder()
    dimensions = await builder.generate_persona_dimensions(
        analysis.world_setting,
        analysis.character_info,
    )
    
    # 显示选项并获取用户选择...
    # selections = {...}
    
    # 3. 构建完整人设
    persona = await builder.build_persona(
        user_name="林云",
        selections=selections,
        world_setting=analysis.world_setting,
        character_info=analysis.character_info,
    )
    
    # 4. 生成故事大纲
    outline_gen = OutlineGenerator()
    outline = await outline_gen.generate_outline(
        user_persona=persona,
        world_setting=analysis.world_setting,
        character_info=analysis.character_info,
        total_chapters=5,
    )
    
    # 5. 初始化故事状态
    story_manager = StoryStateManager()
    story_manager.create_new_story(
        novel_title=analysis.character_info.book_title,
        target_character=analysis.character_info.name,
        user_persona=persona,
        total_chapters=5,
    )
    
    # 6. 逐章生成
    writer = ChapterWriter()
    for chapter_outline in outline.chapters:
        context = story_manager.get_generation_context()
        
        chapter = await writer.write_chapter(
            chapter_outline=chapter_outline,
            user_persona=persona,
            character_info=analysis.character_info,
            world_setting=analysis.world_setting,
            writing_style=analysis.writing_style,
            previous_chapters=context["previous_chapters"],
            relationship_state=context["relationship_state"],
            user_power_level=context["user_power_level"],
            flags=context["flags"],
        )
        
        # 保存章节
        story_manager.add_chapter(chapter)
        
        # 生成互动选项...
        
    # 7. 导出故事
    story_text = story_manager.export_story_text()
    with open("my_story.txt", "w", encoding="utf-8") as f:
        f.write(story_text)

asyncio.run(main())
```

## 数据文件格式

系统使用JSONL格式的数据文件，每行包含一章的信息:

```json
{
    "book_title": "武动乾坤",
    "target_character": "林动",
    "aliases": [""],
    "chapter_order": 1,
    "chapter_title": "第1章 林动",
    "mention_count": 38,
    "is_relevant": true,
    "summary": "章节摘要...",
    "memory_points": ["记忆点1", "记忆点2"],
    "personality_traits": ["性格特点1", "性格特点2"],
    "emotional_state": ["情绪1", "情绪2"],
    "speech_style": ["说话风格1", "说话风格2"],
    "dialogue_examples": ["对话示例1", "对话示例2"],
    "relationships": [
        {
            "name": "林啸",
            "relation": "父子",
            "interaction": "互动描述",
            "attitude": "态度"
        }
    ],
    "key_motivations": ["动机1", "动机2"],
    "evidence_quotes": ["原著引用1", "原著引用2"]
}
```

## 写作风格对齐策略

系统通过以下方式确保生成内容符合原著风格:

1. **风格样本提取**: 从JSONL的evidence_quotes和dialogue_examples中提取典型段落
2. **Prompt植入**: 在生成章节时明确插入风格样本作为参考
3. **特征约束**: 在Prompt中明确列出原著的写作特征要求
4. **叙事特点**: 开篇直接切入冲突、大量使用短句和感叹号、对话简洁有力
5. **修炼描写**: 详细描写身体感受、元力运转、突破瞬间
6. **战斗节奏**: 快节奏战斗、突出招式名称和威力

## 章节连贯性保持

系统通过以下机制保持章节间连贯性:

1. **前置摘要注入**: 每章生成时自动注入前一章的关键事件摘要
2. **状态追踪**: 实时维护角色关系值、实力等级、剧情标记
3. **人设一致性检查**: 确保用户角色的言行符合所选人设
4. **对话历史**: 保留关键对话，确保角色语气一致

## 互动选项设计

每章提供4个方向的互动选项:

- **A - 友善合作向**: 帮助林动、并肩作战、分享资源
- **B - 竞争挑战向**: 与林动切磋、提出赌约、展示实力
- **C - 独立探索向**: 独自行动、寻找机缘、调查秘密
- **D - 情感互动向**: 关心林动、分享心事、建立私交

每个选项包含:
- 剧情影响说明
- 风险提示
- 关系值变化
- 可能设置的剧情标记

## 配置选项

在 `novel_story_agent/config.py` 中可以修改:

```python
@dataclass
class LLMConfig:
    api_key: str = "your-api-key"
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-flash"
    temperature: float = 0.8  # 创意程度
    max_tokens: int = 4096    # 最大token数

@dataclass
class GenerationConfig:
    chapter_min_length: int = 2000  # 章节最小字数
    chapter_max_length: int = 5000  # 章节最大字数
    max_outline_chapters: int = 20  # 最大章节数
    choices_per_chapter: int = 4    # 每章选项数
```

## 特殊命令

在章节互动时可以使用以下命令:

- `save`: 保存当前故事进度
- `status`: 查看当前故事状态（关系值、实力等级等）
- `skip`: 跳过选择，使用默认选项
- `quit`: 退出程序（会自动保存）

## 存档文件

故事会自动保存在 `./story_data/` 目录下，文件名为 `story_{id}.json`。

同时会导出纯文本版本，文件名为 `story_{id}.txt`。

## 支持的LLM

目前默认使用DeepSeek API，但可通过修改 `provider/llm_provider.py` 支持其他LLM:

- OpenAI GPT-4/GPT-3.5
- Claude
- 其他OpenAI兼容API

## 注意事项

1. API调用需要网络连接
2. 生成长章节可能需要等待几秒钟
3. 建议使用温度参数0.7-0.9以获得更好的创意效果
4. 如果生成内容风格不符，可以重新生成或调整参数

## 许可证

MIT License