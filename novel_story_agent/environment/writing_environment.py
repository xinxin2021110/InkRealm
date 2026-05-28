"""WritingEnvironment —— 故事共创的多 Agent 环境。"""
from __future__ import annotations

from typing import Any, Dict, List

from inkrealm.environment.base_env import Environment
from inkrealm.schema import (
    ChapterChoices,
    ChapterContent,
    ChapterOutline,
    CharacterProfile,
    NovelProfile,
    PersonaDimensions,
    StoryOutline,
    UserPersona,
    WorldSetting,
    WritingStyle,
)

from ..roles import (
    ChapterWriterRole,
    OutlinePlanner,
    PersonaDesigner,
    PlotDirector,
    WorldAnalyst,
)


class WritingEnvironment(Environment):
    """编排"作品分析 → 人设 → 大纲 → 章节 → 互动选项"流水线。"""

    def __init__(self) -> None:
        super().__init__(desc="协作写作")
        self.world_analyst = WorldAnalyst()
        self.persona_designer = PersonaDesigner()
        self.outline_planner = OutlinePlanner()
        self.chapter_writer = ChapterWriterRole()
        self.plot_director = PlotDirector()
        for r in (
            self.world_analyst,
            self.persona_designer,
            self.outline_planner,
            self.chapter_writer,
            self.plot_director,
        ):
            self.add_role(r)

    # ---------------- 高阶 API ----------------

    async def analyze_novel(
        self,
        basic_profile: CharacterProfile,
        raw_chapters: List[Dict[str, Any]],
        style_samples: List[str],
    ) -> NovelProfile:
        return await self.world_analyst.analyze(basic_profile, raw_chapters, style_samples)

    async def persona_dimensions(
        self, world: WorldSetting, protagonist: CharacterProfile
    ) -> PersonaDimensions:
        return await self.persona_designer.design_dimensions(world, protagonist)

    async def build_persona(
        self,
        user_name: str,
        selections: Dict[str, str],
        dimensions: PersonaDimensions,
        protagonist: CharacterProfile,
        world: WorldSetting,
    ) -> UserPersona:
        return await self.persona_designer.build_persona(
            user_name, selections, dimensions, protagonist, world
        )

    async def propose_outline(
        self,
        protagonist: CharacterProfile,
        world: WorldSetting,
        user_persona: UserPersona,
        total_chapters: int,
    ) -> StoryOutline:
        return await self.outline_planner.propose(protagonist, world, user_persona, total_chapters)

    async def write_chapter(
        self,
        chapter_outline: ChapterOutline,
        user_persona: UserPersona,
        protagonist: CharacterProfile,
        world: WorldSetting,
        style: WritingStyle,
        previous_chapters: List[ChapterContent],
        relationship_state: Dict[str, int],
        user_power_level: str,
        flags: Dict[str, Any],
    ) -> ChapterContent:
        return await self.chapter_writer.write_chapter(
            chapter_outline,
            user_persona,
            protagonist,
            world,
            style,
            previous_chapters,
            relationship_state,
            user_power_level,
            flags,
        )

    async def generate_choices(
        self,
        chapter: ChapterContent,
        user_persona: UserPersona,
        protagonist: CharacterProfile,
        relationship_state: Dict[str, int],
        user_power_level: str,
        flags: Dict[str, Any],
    ) -> ChapterChoices:
        return await self.plot_director.generate_choices(
            chapter, user_persona, protagonist, relationship_state, user_power_level, flags
        )
