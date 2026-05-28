"""小说 / 角色 schemas"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class CharacterBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    novel_id: int
    name: str
    aliases: List[str] = []
    is_protagonist: bool = False
    profile_summary: str = ""
    avatar_emoji: str = "🪶"
    memory_count: int = 0
    quote_count: int = 0
    analyzed: bool = False


class NovelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str = ""
    cover_emoji: str = "📜"
    description: str = ""
    characters_count: int = 0
    created_at: datetime


class NovelDetail(NovelOut):
    characters: List[CharacterBrief] = []


class CharacterDetail(CharacterBrief):
    book_title: str = ""
    personality_traits: List[str] = []
    speech_style: List[str] = []
    emotional_states: List[str] = []
    key_motivations: List[str] = []
    relationships: List[dict] = []
    sample_quotes: List[str] = []  # 前端预览用 (10 条)


class NovelUploadIn(BaseModel):
    title: str
    author: Optional[str] = ""
    description: Optional[str] = ""
