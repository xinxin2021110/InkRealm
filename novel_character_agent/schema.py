"""adapter: 旧 schema 全部转发到 inkrealm.schema。"""
from __future__ import annotations

from inkrealm.schema import (  # noqa: F401
    AIMessage,
    CharacterProfile,
    DialogueExample,
    MemoryItem,
    MemoryType,
    Message,
    Relationship,
    SystemMessage,
    UserMessage,
)


class ChatContext:
    """旧 ChatContext 兜底（不再使用）"""
    pass


class RoleContext:
    """旧 RoleContext 兜底（不再使用）"""
    pass


class ActionOutput:
    """旧 ActionOutput 兜底（部分外部代码可能引用）"""

    def __init__(self, content: str = "", action_name: str = ""):
        self.content = content
        self.action_name = action_name


__all__ = [
    "Message",
    "UserMessage",
    "SystemMessage",
    "AIMessage",
    "CharacterProfile",
    "MemoryItem",
    "MemoryType",
    "Relationship",
    "DialogueExample",
    "ChatContext",
    "RoleContext",
    "ActionOutput",
]
