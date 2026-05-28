"""OutlinePlanner —— 故事大纲编辑 Role。"""
from __future__ import annotations

from inkrealm.roles.role import Role
from inkrealm.schema import (
    CharacterProfile,
    StoryOutline,
    UserPersona,
    WorldSetting,
)

from ..actions import ProposeStoryOutlineAction


class OutlinePlanner(Role):
    def __init__(self) -> None:
        super().__init__(
            name="OutlinePlanner",
            profile="故事大纲编辑",
            goal="为用户角色与原著主角设计有起承转合的故事大纲",
        )
        self.action = ProposeStoryOutlineAction()
        self.set_actions([self.action])

    async def propose(
        self,
        protagonist: CharacterProfile,
        world: WorldSetting,
        user_persona: UserPersona,
        total_chapters: int,
    ) -> StoryOutline:
        out = await self.action.run(protagonist, world, user_persona, total_chapters)
        return out.instruct_content  # type: ignore[return-value]
