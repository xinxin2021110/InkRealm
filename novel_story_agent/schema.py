"""adapter: 把旧 schema 直接映射到 inkrealm.schema。

注：
- `CharacterInfo` 现在等价于新的 `CharacterProfile`（字段是后者的超集）；
- `NovelAnalysis` 与新的 `NovelProfile` 等价但字段命名保持旧形式
  （character_info / world_setting / writing_style / raw_data）。
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# 转发：基础数据契约直接来自 inkrealm
from inkrealm.schema import (  # noqa: F401
    ChapterChoices,
    ChapterContent,
    ChapterOutline,
    ChoiceOption,
    PersonaDimension,
    PersonaDimensions,
    PersonaOption,
    PersonaSelection,
    StoryOutline,
    UserChoice,
    UserPersona,
    WorldSetting,
    WritingStyle,
)
from inkrealm.schema import CharacterProfile as _InkCharacter


# 旧 CharacterInfo —— 直接当作 alias
CharacterInfo = _InkCharacter


class Message(BaseModel):
    """旧 Message 兜底（旧代码可能 import）。"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    role: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


class NovelAnalysis(BaseModel):
    """旧 NovelAnalysis = world_setting + character_info + writing_style + raw_data。"""

    world_setting: WorldSetting = Field(default_factory=WorldSetting)
    character_info: CharacterInfo = Field(default_factory=CharacterInfo)
    writing_style: WritingStyle = Field(default_factory=WritingStyle)
    raw_data: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}


# ---------------- StoryState（沿用旧形态，因为 webapp 内部不依赖此模型，仅保留 import 兼容） ----------------

class StoryMetadata(BaseModel):
    story_id: str = ""
    title: str = ""
    novel_title: str = ""
    target_character: str = ""
    user_persona_name: str = ""
    total_chapters: int = 0
    current_chapter: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = {"arbitrary_types_allowed": True}


class StoryState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    novel_title: str = ""
    target_character: str = ""
    user_persona: Optional[UserPersona] = None
    total_chapters: int = 0
    current_chapter: int = 0
    chapters: List[ChapterContent] = Field(default_factory=list)
    choices_history: List[UserChoice] = Field(default_factory=list)
    relationship_meter: Dict[str, int] = Field(default_factory=dict)
    user_power_level: str = ""
    flags: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = {"arbitrary_types_allowed": True}


class GenerationContext(BaseModel):
    novel_analysis: Optional[NovelAnalysis] = None
    user_persona: Optional[UserPersona] = None
    story_outline: Optional[StoryOutline] = None
    previous_chapters: List[ChapterContent] = Field(default_factory=list)
    current_chapter_outline: Optional[ChapterOutline] = None
    relationship_state: Dict[str, int] = Field(default_factory=dict)
    user_power_level: str = ""
    flags: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


__all__ = [
    "Message",
    "CharacterInfo",
    "WorldSetting",
    "WritingStyle",
    "NovelAnalysis",
    "UserPersona",
    "PersonaSelection",
    "PersonaOption",
    "PersonaDimensions",
    "ChapterOutline",
    "StoryOutline",
    "ChapterContent",
    "ChoiceOption",
    "ChapterChoices",
    "UserChoice",
    "StoryMetadata",
    "StoryState",
    "GenerationContext",
]
