"""NovelCharacter —— 兼容 webapp 旧调用的薄包装。

内部就是一个 CharacterRole；保留 webapp 已使用的全部公开 API：
- `from_data_file(data_file, target_character)`
- `profile / name / dialogue_history`
- `await respond(text)` / `respond_stream(text)`
- `clear_dialogue_history()` / `get_character_info()`
- `memory_retrieve_action.get_retrieved_memories()`
- `quote_retrieve_action.get_retrieved_quotes()`
"""
from __future__ import annotations

from typing import AsyncIterator, List, Optional

from inkrealm.schema import CharacterProfile, DialogueExample, MemoryItem

from ..roles.character_role import CharacterRole


class _RetrieveCompat:
    """把 RetrieveMemory/QuoteAction 包装出"get_retrieved_*"老方法。"""

    def __init__(self, inner) -> None:
        self._inner = inner

    def get_retrieved_memories(self) -> List[MemoryItem]:
        return list(getattr(self._inner, "retrieved", []) or [])

    def get_retrieved_quotes(self) -> List[DialogueExample]:
        return list(getattr(self._inner, "retrieved", []) or [])

    async def run(self, *args, **kwargs):
        return await self._inner.run(*args, **kwargs)


class NovelCharacter:
    """旧 NovelCharacter 兼容入口。"""

    def __init__(
        self,
        profile: CharacterProfile,
        *,
        _role: Optional[CharacterRole] = None,
    ) -> None:
        self._role: CharacterRole = _role or CharacterRole(profile=profile)
        self.profile = self._role.character_profile
        self.name = self._role.name
        self.dialogue_history = self._role.dialogue_history
        self.memory_retrieve_action = _RetrieveCompat(self._role.memory_retrieve_action)
        self.quote_retrieve_action = _RetrieveCompat(self._role.quote_retrieve_action)

    async def respond(self, user_input: str) -> str:
        return await self._role.respond(user_input)

    async def respond_stream(self, user_input: str) -> AsyncIterator[str]:
        async for chunk in self._role.respond_stream(user_input):
            yield chunk

    def clear_dialogue_history(self) -> None:
        self._role.clear_dialogue_history()

    def get_character_info(self):
        return self._role.get_character_info()

    @classmethod
    def from_data_file(
        cls,
        data_file: str,
        target_character: Optional[str] = None,
        llm_provider=None,  # 兼容旧签名（忽略）
    ) -> "NovelCharacter":
        role = CharacterRole.from_data_file(data_file, target_character)
        return cls(profile=role.character_profile, _role=role)
