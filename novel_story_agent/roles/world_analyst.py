"""WorldAnalyst —— 作品分析师 Role。"""
from __future__ import annotations

from typing import Any, Dict, List

from inkrealm.roles.role import Role
from inkrealm.schema import CharacterProfile, NovelProfile, WorldSetting, WritingStyle

from ..actions import (
    AnalyzeWorldSettingAction,
    AnalyzeWritingStyleAction,
    EnrichCharacterAction,
)


class WorldAnalyst(Role):
    """从原始 JSONL 出发：WorldSetting + WritingStyle + 加强 CharacterProfile。"""

    def __init__(self) -> None:
        super().__init__(
            name="WorldAnalyst",
            profile="作品分析师",
            goal="提炼一本小说的世界观、写作风格与角色画像",
        )
        self.analyze_world = AnalyzeWorldSettingAction()
        self.analyze_style = AnalyzeWritingStyleAction()
        self.enrich_character = EnrichCharacterAction()
        self.set_actions([self.analyze_world, self.analyze_style, self.enrich_character])

    async def analyze(
        self,
        basic_profile: CharacterProfile,
        raw_chapters: List[Dict[str, Any]],
        style_samples: List[str],
    ) -> NovelProfile:
        world_out = await self.analyze_world.run(
            basic_profile.book_title, basic_profile.name, raw_chapters
        )
        world: WorldSetting = world_out.instruct_content or WorldSetting()

        style_out = await self.analyze_style.run(style_samples)
        style: WritingStyle = style_out.instruct_content or WritingStyle(sample_texts=style_samples)

        enriched_out = await self.enrich_character.run(basic_profile, raw_chapters[:5])
        enriched: CharacterProfile = enriched_out.instruct_content or basic_profile

        return NovelProfile(
            book_title=basic_profile.book_title,
            author="",
            target_character=enriched,
            world_setting=world,
            writing_style=style,
        )
