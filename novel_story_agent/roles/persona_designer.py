"""PersonaDesigner —— 给用户角色出 4 维度选项 & 构建完整 UserPersona。"""
from __future__ import annotations

from typing import Dict

from inkrealm.roles.role import Role
from inkrealm.schema import (
    CharacterProfile,
    PersonaDimensions,
    UserPersona,
    WorldSetting,
)

from ..actions import (
    BuildUserPersonaAction,
    GeneratePersonaDimensionsAction,
)


class PersonaDesigner(Role):
    def __init__(self) -> None:
        super().__init__(
            name="PersonaDesigner",
            profile="人设设计师",
            goal="为用户在同人故事中构建一个生动、与世界观契合的角色",
        )
        self.dimensions_action = GeneratePersonaDimensionsAction()
        self.persona_action = BuildUserPersonaAction()
        self.set_actions([self.dimensions_action, self.persona_action])

    async def design_dimensions(
        self,
        world: WorldSetting,
        protagonist: CharacterProfile,
    ) -> PersonaDimensions:
        out = await self.dimensions_action.run(world, protagonist)
        return out.instruct_content  # type: ignore[return-value]

    async def build_persona(
        self,
        user_name: str,
        selections: Dict[str, str],
        dimensions: PersonaDimensions,
        protagonist: CharacterProfile,
        world: WorldSetting,
    ) -> UserPersona:
        out = await self.persona_action.run(
            user_name=user_name,
            selections=selections,
            dimensions=dimensions,
            protagonist=protagonist,
            world=world,
        )
        return out.instruct_content  # type: ignore[return-value]
