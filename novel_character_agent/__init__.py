"""novel_character_agent —— 仿 MetaGPT 风格的"小说角色复刻"功能包。

本包基于 `inkrealm` 提供的 Role / Action / Environment / Memory / Provider 抽象，
实现具体的：
- `roles.CharacterRole`           — 一个 ReAct(BY_ORDER) 的角色 Role
- `actions.RetrieveMemoryAction`  — 多通道+多 hop 记忆检索
- `actions.RetrieveQuotesAction`  — 100+ 真实语录检索
- `actions.SpeakInCharacterAction`— 多维上下文入戏回话（含流式）
- `environment.ChatEnvironment`   — 聊天环境

对外仍暴露旧 webapp 在用的 `NovelCharacter` 名字（薄包装到 CharacterRole）。
"""
from __future__ import annotations

from .actions import (
    RetrieveMemoryAction,
    RetrieveQuotesAction,
    SpeakInCharacterAction,
)
from .config import init_config
from .environment.chat_environment import ChatEnvironment
from .novel_characters.novel_character import NovelCharacter
from .roles.character_role import CharacterRole, DialogueHistory
from .schema import (
    CharacterProfile,
    DialogueExample,
    MemoryItem,
    Message,
    Relationship,
)

__version__ = "3.0.0"
__all__ = [
    "Message",
    "CharacterProfile",
    "MemoryItem",
    "Relationship",
    "DialogueExample",
    "CharacterRole",
    "DialogueHistory",
    "ChatEnvironment",
    "NovelCharacter",
    "RetrieveMemoryAction",
    "RetrieveQuotesAction",
    "SpeakInCharacterAction",
    "init_config",
]
