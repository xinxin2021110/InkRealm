"""ChatEnvironment —— 角色复刻产品的聊天环境，继承自 inkrealm.Environment。"""
from __future__ import annotations

from typing import AsyncIterator, List, Optional

from inkrealm.environment.base_env import Environment
from inkrealm.schema import Message, UserMessage

from ..roles.character_role import CharacterRole


class ChatEnvironment(Environment):
    """专用于"1 名角色 + 用户"的聊天会话环境。"""

    def __init__(self, desc: str = "小说角色聊天环境") -> None:
        super().__init__(desc=desc)
        self.active_character: Optional[CharacterRole] = None
        self.user_id = "user"

    # ---------------- 角色管理 ----------------

    def set_character(self, character: CharacterRole) -> None:
        self.active_character = character
        super().add_role(character)

    def add_role(self, role) -> None:  # type: ignore[override]
        super().add_role(role)
        if isinstance(role, CharacterRole) and self.active_character is None:
            self.active_character = role

    # ---------------- 聊天 API ----------------

    async def chat(self, user_input: str) -> str:
        if not self.active_character:
            raise RuntimeError("没有活跃的 CharacterRole")
        msg = UserMessage(
            content=user_input,
            sent_from=self.user_id,
            send_to={self.active_character.name},
        )
        self.publish_message(msg)
        return await self.active_character.respond(user_input)

    async def chat_stream(self, user_input: str) -> AsyncIterator[str]:
        if not self.active_character:
            raise RuntimeError("没有活跃的 CharacterRole")
        msg = UserMessage(
            content=user_input,
            sent_from=self.user_id,
            send_to={self.active_character.name},
        )
        self.publish_message(msg)
        async for chunk in self.active_character.respond_stream(user_input):
            yield chunk

    # ---------------- 工具 ----------------

    def get_history(self) -> List[Message]:
        return list(self.history.storage)

    def clear_history(self) -> None:
        self.history.clear()
        if self.active_character:
            self.active_character.clear_dialogue_history()

    def get_character(self) -> Optional[CharacterRole]:
        return self.active_character

    def get_stats(self):
        return {
            "total_messages": len(self.history.storage),
            "total_roles": len(self.roles),
            "has_active_character": self.active_character is not None,
            "character": (
                self.active_character.get_character_info() if self.active_character else None
            ),
        }
