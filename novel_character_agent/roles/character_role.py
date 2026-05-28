"""CharacterRole —— 仿 MetaGPT 风格的"小说角色复刻 Role"。

ReAct 模式：BY_ORDER（顺序触发 RetrieveMemory → RetrieveQuotes → SpeakInCharacter）。
对外保留 webapp 与旧示例使用的便捷 API：respond / respond_stream / clear_dialogue_history /
get_character_info / dialogue_history / memory_retrieve_action / quote_retrieve_action。
"""
from __future__ import annotations

from typing import AsyncIterator, Dict, List, Optional

from inkrealm.data.jsonl_loader import JsonlLoader
from inkrealm.data.profile_builder import ProfileBuilder
from inkrealm.retrieval import MemoryRetriever, QuoteRetriever
from inkrealm.roles.role import Role, RoleReactMode
from inkrealm.schema import (
    AIMessage,
    CharacterProfile,
    Message,
    UserMessage,
    WorldSetting,
)

from ..actions import (
    RetrieveMemoryAction,
    RetrieveQuotesAction,
    SpeakInCharacterAction,
)


# ---------------- DialogueHistory ----------------

class DialogueHistory:
    """轻量对话历史，提供 webapp 现有调用方式。"""

    def __init__(self, max_history: int = 20) -> None:
        self.max_history = max_history
        self._history: List[Message] = []

    def add_user_message(self, content: str) -> None:
        self._history.append(UserMessage(content=content, sent_from="user"))
        self._trim()

    def add_assistant_message(self, content: str, cause_by: str = "SpeakInCharacter") -> None:
        self._history.append(AIMessage(content=content, cause_by=cause_by))
        self._trim()

    def get_history(self) -> List[Message]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()

    def get_turn_count(self) -> int:
        return len(self._history) // 2

    def _trim(self) -> None:
        if len(self._history) > self.max_history * 2:
            self._history = self._history[-self.max_history * 2 :]


# ---------------- CharacterRole ----------------

class CharacterRole(Role):
    """复刻一位小说角色。"""

    def __init__(
        self,
        profile: CharacterProfile,
        *,
        world: Optional[WorldSetting] = None,
    ) -> None:
        super().__init__(
            name=profile.name or "Character",
            profile=f"小说《{profile.book_title}》中的角色 {profile.name}",
            goal="以角色本人的口吻与读者对话，做到符合原著",
            desc=profile.profile or "",
        )
        self.character_profile = profile
        self.world = world or WorldSetting()
        self.dialogue_history = DialogueHistory()

        # 长期记忆 + 检索器（MetaGPT 风格的 long-term memory）
        self.memory_retriever = MemoryRetriever(profile)
        self.quote_retriever = QuoteRetriever(profile)

        # 三个 Action（兼容旧字段名）
        self.memory_retrieve_action = RetrieveMemoryAction(self.memory_retriever)
        self.quote_retrieve_action = RetrieveQuotesAction(self.quote_retriever)
        self.chat_action = SpeakInCharacterAction(profile, world=self.world)

        self.set_actions(
            [
                self.memory_retrieve_action,
                self.quote_retrieve_action,
                self.chat_action,
            ]
        )
        self.set_react_mode(RoleReactMode.BY_ORDER, max_loop=1)

    # ---------------- 公共便捷 API ----------------

    async def respond(self, user_input: str) -> str:
        """一次性、非流式回复。"""
        self.dialogue_history.add_user_message(user_input)
        await self.memory_retrieve_action.run(user_input)
        await self.quote_retrieve_action.run(user_input)
        ans = await self.chat_action.run(
            user_input,
            retrieved_memories=self.memory_retrieve_action.retrieved,
            retrieved_quotes=self.quote_retrieve_action.retrieved,
            history=self._history_for_llm(),
        )
        text = ans.content
        self.dialogue_history.add_assistant_message(text)
        return text

    async def respond_stream(self, user_input: str) -> AsyncIterator[str]:
        """流式回复：边生成边 yield，最终统一过滤动作描写后落库。"""
        self.dialogue_history.add_user_message(user_input)
        await self.memory_retrieve_action.run(user_input)
        await self.quote_retrieve_action.run(user_input)
        chunks: List[str] = []
        async for chunk in self.chat_action.run_stream(
            user_input,
            retrieved_memories=self.memory_retrieve_action.retrieved,
            retrieved_quotes=self.quote_retrieve_action.retrieved,
            history=self._history_for_llm(),
        ):
            chunks.append(chunk)
            yield chunk
        final = self.chat_action._post("".join(chunks))
        self.dialogue_history.add_assistant_message(final)

    def clear_dialogue_history(self) -> None:
        self.dialogue_history.clear_history()
        self.rc.memory.clear()
        self.rc.working_memory.clear()

    def get_character_info(self) -> Dict:
        p = self.character_profile
        return {
            "name": p.name,
            "profile": p.profile,
            "aliases": p.aliases,
            "book": p.book_title,
            "personality_traits": p.personality_traits,
            "speech_style": p.speech_style,
            "total_memories": len(p.memories),
            "total_quotes": len(p.dialogue_examples),
            "dialogue_turns": self.dialogue_history.get_turn_count(),
        }

    # ---------------- 私有 ----------------

    def _history_for_llm(self) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        for m in self.dialogue_history.get_history()[-10:]:
            role = "user" if m.role == "user" else "assistant"
            out.append({"role": role, "content": m.content})
        # 最后一条是刚 add 的 user，要去重
        if out and out[-1]["role"] == "user":
            out = out[:-1]
        return out

    # ---------------- 工厂方法 ----------------

    @classmethod
    def from_data_file(
        cls,
        data_file: str,
        target_character: Optional[str] = None,
        world: Optional[WorldSetting] = None,
    ) -> "CharacterRole":
        loader = JsonlLoader(data_file)
        profile = loader.build_profile(target_character)
        profile = ProfileBuilder(profile).build()
        return cls(profile=profile, world=world)
