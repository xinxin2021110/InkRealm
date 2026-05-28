"""聊天 schemas"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreate(BaseModel):
    novel_id: int
    character_id: int
    user_name: str = "少侠"


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    retrieved_memories: int = 0
    retrieved_quotes: int = 0
    created_at: datetime


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    novel_id: int
    character_id: int
    character_name: str = ""
    novel_title: str = ""
    user_name: str
    title: str = ""
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_preview: str = ""


class ChatSessionDetail(ChatSessionOut):
    messages: List[ChatMessageOut] = []


class SendMessageIn(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


class SendMessageOut(BaseModel):
    user_message: ChatMessageOut
    character_message: ChatMessageOut
