"""Schema —— 全系统的"数据契约"。

照搬 MetaGPT.schema 的精髓：
1. `Message` 是所有 Agent 通信的"总线货币"，带 cause_by / sent_from / send_to
   / instruct_content；
2. `UserMessage / SystemMessage / AIMessage` 是 role 预填子类；
3. `MessageQueue` 包 asyncio.Queue，便于 Role 的 _observe；
4. 业务数据契约（CharacterProfile / NovelProfile / Persona / Chapter…）
   全部用 pydantic，避免 dict 漂移。
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

from .const import MESSAGE_ROUTE_TO_ALL


# ---------------- 工具：将 Action / Role 实例转字符串 ----------------

def any_to_str(val: Any) -> str:
    """模仿 MetaGPT.utils.common.any_to_str —— 任何 cause_by 都转成 'Module.Class'。"""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, type):
        return f"{val.__module__}.{val.__name__}"
    cls = val.__class__
    return f"{cls.__module__}.{cls.__name__}"


def any_to_str_set(vals: Any) -> Set[str]:
    if vals is None:
        return set()
    if isinstance(vals, str):
        return {vals}
    if isinstance(vals, (list, tuple, set)):
        return {any_to_str(v) for v in vals}
    return {any_to_str(vals)}


# ---------------- Message ----------------

class Message(BaseModel):
    """系统总线货币 —— 所有 observe/think/act/publish 都围绕它。

    字段含义沿用 MetaGPT：
    - cause_by: 触发本消息的 Action 全名，用于其他 Role 的 watch 过滤
    - sent_from: 发送者标识
    - send_to: 接收者集合；包含 `<all>` 时所有 Role 都能观察到
    - instruct_content: 结构化业务对象（pydantic），content 是其文本表达
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    role: str = "user"  # user / assistant / system
    cause_by: str = ""
    sent_from: str = ""
    send_to: Set[str] = Field(default_factory=lambda: {MESSAGE_ROUTE_TO_ALL})
    instruct_content: Optional[BaseModel] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {"arbitrary_types_allowed": True}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "cause_by": self.cause_by,
            "sent_from": self.sent_from,
            "send_to": list(self.send_to),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        head = f"[{self.role}|{self.sent_from or '-'}]"
        snippet = (self.content[:60] + "…") if len(self.content) > 60 else self.content
        return f"{head} {snippet}"


class UserMessage(Message):
    role: str = "user"


class SystemMessage(Message):
    role: str = "system"


class AIMessage(Message):
    role: str = "assistant"


# ---------------- MessageQueue ----------------

class MessageQueue:
    """对 asyncio.Queue 的最小封装，提供同步弹空便捷接口。"""

    def __init__(self) -> None:
        self._q: asyncio.Queue[Message] = asyncio.Queue()

    def empty(self) -> bool:
        return self._q.empty()

    def push(self, msg: Message) -> None:
        self._q.put_nowait(msg)

    def pop_all(self) -> List[Message]:
        out: List[Message] = []
        while not self._q.empty():
            try:
                out.append(self._q.get_nowait())
            except asyncio.QueueEmpty:
                break
        return out


# ---------------- 业务契约 ----------------
# ★ 关键：以下契约对"任何小说"都通用，不假设修真 / 玄幻 / 都市。

class Relationship(BaseModel):
    name: str = ""
    relation: str = ""
    interaction: str = ""
    attitude: str = ""

    model_config = {"arbitrary_types_allowed": True}


class MemoryType(str, Enum):
    EVENT = "event"                  # 章节中发生的具体事件（memory_points）
    RELATIONSHIP = "relationship"    # 关系类记忆
    EMOTION = "emotion"              # 情绪经历
    DIALOGUE = "dialogue"            # 角色说过的话（含上下文）
    PERSONALITY = "personality"      # 性格描写
    SCENE = "scene"                  # 章节级摘要（summary 字段）
    MOTIVATION = "motivation"        # 关键动机（key_motivations 字段）
    PERSONALITY_DESC = "personality_desc"  # 章节级性格描述
    DIALOGUE_SAMPLE = "dialogue_sample"    # 较完整的对话样本（dialogue_examples 字段）


class MemoryItem(BaseModel):
    """章节级或事件级记忆条目。

    新增字段（用于充分利用 jsonl 数据 + 提升检索质量）：
    - chapter_order:   章节序号，便于"时序加权"和"找到角色后期/前期记忆"
    - mention_count:   该章中角色被提及次数，越高代表该章对此人物越重要
    - confidence:      源数据置信度（jsonl confidence 字段），低于阈值可降权
    - weight:          检索时叠加的静态权重（来源于 mention_count + confidence）
    - scene_summary:   该记忆所在章节的 summary，让记忆"自带场景"
    - related_people:  该记忆涉及的人名（来源 relationships 命中），用于实体检索
    - emotion:         该记忆隐含的情绪标签（来源 emotional_state）
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    chapter: str = ""
    chapter_order: int = 0
    memory_type: str = MemoryType.EVENT.value
    keywords: List[str] = Field(default_factory=list)
    mention_count: int = 0
    confidence: float = 1.0
    weight: float = 1.0
    scene_summary: str = ""
    related_people: List[str] = Field(default_factory=list)
    emotion: str = ""

    model_config = {"arbitrary_types_allowed": True}


class DialogueExample(BaseModel):
    """角色语录条目。

    新增字段：
    - chapter_order:  章节序号
    - mention_count / confidence:  数据源元信息
    - is_evidence:    True = 来自 evidence_quotes（强证据），False = dialogue_examples（更完整对话样本）
    - related_people: 该语录涉及的对象
    """

    content: str = ""
    context: str = ""
    emotion: str = ""
    chapter: str = ""
    chapter_order: int = 0
    mention_count: int = 0
    confidence: float = 1.0
    is_evidence: bool = True
    related_people: List[str] = Field(default_factory=list)


class CharacterProfile(BaseModel):
    """小说角色画像 —— 与具体作品无关的字段。"""

    name: str = ""
    aliases: List[str] = Field(default_factory=list)
    book_title: str = ""
    profile: str = ""

    personality_traits: List[str] = Field(default_factory=list)
    emotional_states: List[str] = Field(default_factory=list)
    speech_style: List[str] = Field(default_factory=list)
    key_motivations: List[str] = Field(default_factory=list)

    relationships: List[Relationship] = Field(default_factory=list)
    memories: List[MemoryItem] = Field(default_factory=list)
    dialogue_examples: List[DialogueExample] = Field(default_factory=list)

    total_chapters: int = 0
    total_quotes: int = 0

    model_config = {"arbitrary_types_allowed": True}


class WorldSetting(BaseModel):
    """通用世界观 —— 任意题材（玄幻/都市/历史/科幻）皆可填。"""

    genre: str = ""  # 玄幻 / 武侠 / 都市 / 言情 / 科幻 / 历史 …
    power_system_name: str = ""  # 该书"力量体系"的名字，可空（如非超能题材）
    power_system_desc: str = ""  # 力量体系详述
    power_levels: List[str] = Field(default_factory=list)  # 等级阶梯
    major_forces: List[Dict[str, str]] = Field(default_factory=list)  # 派系
    world_background: str = ""
    current_timeline: str = ""
    key_locations: List[str] = Field(default_factory=list)  # 重要地点


class WritingStyle(BaseModel):
    """通用写作风格 —— 不假设具体作者。"""

    author_signature: str = ""  # 简短一句作者风格签名
    narrative_features: List[str] = Field(default_factory=list)
    dialogue_features: List[str] = Field(default_factory=list)
    description_features: List[str] = Field(default_factory=list)
    sample_texts: List[str] = Field(default_factory=list)


class NovelProfile(BaseModel):
    """一本小说的整体画像。"""

    book_title: str = ""
    author: str = ""
    target_character: CharacterProfile = Field(default_factory=CharacterProfile)
    world_setting: WorldSetting = Field(default_factory=WorldSetting)
    writing_style: WritingStyle = Field(default_factory=WritingStyle)


# ---------------- 续写相关 ----------------

class PersonaSelection(BaseModel):
    background: str = "A"
    personality: str = "A"
    relationship: str = "A"
    ability: str = "A"


class PersonaOption(BaseModel):
    id: str  # A/B/C/D
    title: str
    description: str
    implications: str = ""


class PersonaDimension(BaseModel):
    key: str  # background / personality / relationship / ability
    title: str  # 中文显示名
    description: str  # 维度说明
    options: List[PersonaOption]


class PersonaDimensions(BaseModel):
    background: PersonaDimension
    personality: PersonaDimension
    relationship: PersonaDimension
    ability: PersonaDimension


class UserPersona(BaseModel):
    name: str = ""
    background: str = ""
    personality: str = ""
    relationship_to_protagonist: str = ""
    initial_ability: str = ""
    story_goal: str = ""
    background_detail: str = ""
    personality_detail: str = ""
    relationship_detail: str = ""
    ability_detail: str = ""


class ChapterOutline(BaseModel):
    chapter_number: int = 0
    title: str = ""
    core_conflict: str = ""
    scene_setting: str = ""
    character_interaction: str = ""
    plot_function: str = ""
    branch_points: List[str] = Field(default_factory=list)


class StoryOutline(BaseModel):
    total_chapters: int = 0
    title: str = ""
    theme: str = ""
    chapters: List[ChapterOutline] = Field(default_factory=list)


class ChapterContent(BaseModel):
    chapter_number: int = 0
    title: str = ""
    content: str = ""
    summary: str = ""
    key_events: List[str] = Field(default_factory=list)
    characters_present: List[str] = Field(default_factory=list)
    power_level_after: str = ""  # ★ 由 LLM 在 prompt 里填，避免外部硬编码阶梯


class ChoiceOption(BaseModel):
    option_id: str  # A/B/C/D
    text: str
    description: str = ""
    impact: str = ""
    risk: str = ""
    tone: str = ""  # 由 LLM 自由命名（友善 / 谋略 / 探索 / 情感 ...）
    relationship_change: Dict[str, int] = Field(default_factory=dict)
    flags_set: List[str] = Field(default_factory=list)


class ChapterChoices(BaseModel):
    chapter_number: int = 0
    situation_summary: str = ""
    options: List[ChoiceOption] = Field(default_factory=list)


class UserChoice(BaseModel):
    chapter_number: int
    selected_option: str
    timestamp: datetime = Field(default_factory=datetime.now)


__all__ = [
    "Message",
    "UserMessage",
    "SystemMessage",
    "AIMessage",
    "MessageQueue",
    "any_to_str",
    "any_to_str_set",
    "Relationship",
    "MemoryType",
    "MemoryItem",
    "DialogueExample",
    "CharacterProfile",
    "WorldSetting",
    "WritingStyle",
    "NovelProfile",
    "PersonaSelection",
    "PersonaOption",
    "PersonaDimension",
    "PersonaDimensions",
    "UserPersona",
    "ChapterOutline",
    "StoryOutline",
    "ChapterContent",
    "ChoiceOption",
    "ChapterChoices",
    "UserChoice",
]
