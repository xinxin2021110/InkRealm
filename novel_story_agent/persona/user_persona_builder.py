"""UserPersonaBuilder —— webapp 仍在用的入口；内部用 PersonaDesigner Role。"""
from __future__ import annotations

from typing import Any, Dict, List

from ..actions.propose_persona_dimensions import GeneratePersonaDimensionsAction
from ..roles.persona_designer import PersonaDesigner
from ..schema import (
    CharacterInfo,
    PersonaDimension,
    PersonaDimensions,
    UserPersona,
    WorldSetting,
)


class UserPersonaBuilder:
    def __init__(self) -> None:
        self._designer = PersonaDesigner()

    async def generate_persona_dimensions(
        self,
        world_setting: WorldSetting,
        character_info: CharacterInfo,
    ) -> Dict[str, Any]:
        dims: PersonaDimensions = await self._designer.design_dimensions(
            world_setting, character_info
        )
        return self._dims_to_dict(dims)

    def _get_default_dimensions(self, book_title: str) -> Dict[str, Any]:
        return GeneratePersonaDimensionsAction._fallback(name="主角")

    async def build_persona(
        self,
        user_name: str,
        selections: Dict[str, str],
        world_setting: WorldSetting,
        character_info: CharacterInfo,
    ) -> UserPersona:
        dims = await self._designer.design_dimensions(world_setting, character_info)
        return await self._designer.build_persona(
            user_name=user_name,
            selections=selections,
            dimensions=dims,
            protagonist=character_info,
            world=world_setting,
        )

    def format_dimensions_for_display(self, dimensions: Dict[str, Any]) -> str:
        title_map = {
            "background": "【维度1】出身背景",
            "personality": "【维度2】性格倾向",
            "relationship": "【维度3】与主角关系",
            "ability": "【维度4】初始能力",
        }
        lines: List[str] = []
        for key, data in dimensions.items():
            lines.append(f"\n{title_map.get(key, key)}")
            lines.append(f"说明: {data.get('description', '')}")
            lines.append("选项:")
            for opt in data.get("options", []):
                lines.append(f"  {opt['id']}. {opt['title']}")
                lines.append(f"     {opt['description']}")
                if opt.get("implications"):
                    lines.append(f"     [影响] {opt['implications']}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _dims_to_dict(dims: PersonaDimensions) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for key in ("background", "personality", "relationship", "ability"):
            d: PersonaDimension = getattr(dims, key)
            out[key] = {
                "description": d.description,
                "options": [
                    {
                        "id": o.id,
                        "title": o.title,
                        "description": o.description,
                        "implications": o.implications,
                    }
                    for o in d.options
                ],
            }
        return out
