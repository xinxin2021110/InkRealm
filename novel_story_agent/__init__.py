"""novel_story_agent —— 仿 MetaGPT 风格的"小说故事续写"功能包。

基于 inkrealm 的 Role / Action / ActionNode / Environment / Team 抽象，提供：
- `roles.WorldAnalyst`         作品分析（世界观 / 风格 / 角色画像）
- `roles.PersonaDesigner`      4 维度选项 + 完整 UserPersona
- `roles.OutlinePlanner`       3-20 章故事大纲
- `roles.ChapterWriterRole`    SOP(BY_ORDER) 写章节正文 + 摘要 + 关键事件
- `roles.PlotDirector`         章末 4 个互动选项
- `environment.WritingEnvironment`  把 5 个 Role 组合成"故事工坊"
- `team.NovelTeam`             创业公司隐喻的产品级入口

为方便 webapp 与历史脚本，仍暴露：
- `data.NovelAnalyzer / CharacterLoader`
- `persona.UserPersonaBuilder`
- `generation.OutlineGenerator / ChapterWriter / ChoiceGenerator`
- `schema.NovelAnalysis / UserPersona / StoryOutline / ChapterContent / …`
"""
from __future__ import annotations

from .actions import (
    AnalyzeWorldSettingAction,
    AnalyzeWritingStyleAction,
    BuildUserPersonaAction,
    DraftChapterAction,
    EnrichCharacterAction,
    ExtractKeyEventsAction,
    GenerateChapterChoicesAction,
    GeneratePersonaDimensionsAction,
    ProposeStoryOutlineAction,
    SummarizeChapterAction,
)
from .config import init_config
from .data import CharacterLoader, NovelAnalyzer
from .environment.writing_environment import WritingEnvironment
from .generation import ChapterWriter, ChoiceGenerator, OutlineGenerator
from .persona import UserPersonaBuilder
from .roles import (
    ChapterWriterRole,
    OutlinePlanner,
    PersonaDesigner,
    PlotDirector,
    WorldAnalyst,
)
from .schema import (
    ChapterChoices,
    ChapterContent,
    ChapterOutline,
    CharacterInfo,
    ChoiceOption,
    NovelAnalysis,
    StoryOutline,
    StoryState,
    UserPersona,
    WorldSetting,
    WritingStyle,
)
from .team import NovelTeam

__version__ = "3.0.0"
__all__ = [
    # schema
    "NovelAnalysis", "WorldSetting", "WritingStyle", "CharacterInfo",
    "UserPersona", "StoryOutline", "ChapterOutline", "ChapterContent",
    "ChoiceOption", "ChapterChoices", "StoryState",
    # roles
    "WorldAnalyst", "PersonaDesigner", "OutlinePlanner",
    "ChapterWriterRole", "PlotDirector",
    # actions
    "AnalyzeWorldSettingAction", "AnalyzeWritingStyleAction", "EnrichCharacterAction",
    "GeneratePersonaDimensionsAction", "BuildUserPersonaAction",
    "ProposeStoryOutlineAction",
    "DraftChapterAction", "SummarizeChapterAction", "ExtractKeyEventsAction",
    "GenerateChapterChoicesAction",
    # env / team
    "WritingEnvironment", "NovelTeam",
    # webapp 在用的高阶门面
    "NovelAnalyzer", "CharacterLoader",
    "UserPersonaBuilder", "OutlineGenerator", "ChapterWriter", "ChoiceGenerator",
    # config
    "init_config",
]
