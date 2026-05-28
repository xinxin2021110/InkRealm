"""PlotDirector —— 剧情导演 Role，生成章末互动选项。"""
from __future__ import annotations

from typing import Any, Dict

from inkrealm.roles.role import Role
from inkrealm.schema import (
    ChapterChoices,
    ChapterContent,
    CharacterProfile,
    UserPersona,
)

from ..actions import GenerateChapterChoicesAction


class PlotDirector(Role):
    def __init__(self) -> None:
        super().__init__(
            name="PlotDirector",
            profile="剧情导演",
            goal="为读者在每章末尾提供 4 个能真正影响后续剧情的抉择",
        )
        self.action = GenerateChapterChoicesAction()
        self.set_actions([self.action])

    async def generate_choices(
        self,
        chapter: ChapterContent,
        user_persona: UserPersona,
        protagonist: CharacterProfile,
        relationship_state: Dict[str, int],
        user_power_level: str,
        flags: Dict[str, Any],
    ) -> ChapterChoices:
        out = await self.action.run(
            chapter,
            user_persona,
            protagonist,
            relationship_state,
            user_power_level,
            flags,
        )
        return out.instruct_content  # type: ignore[return-value]
