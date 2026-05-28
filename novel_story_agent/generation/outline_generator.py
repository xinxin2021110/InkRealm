"""OutlineGenerator —— webapp 仍在用的入口；内部用 OutlinePlanner Role。"""
from __future__ import annotations

from typing import List

from ..roles.outline_planner import OutlinePlanner
from ..schema import (
    CharacterInfo,
    StoryOutline,
    UserPersona,
    WorldSetting,
)


class OutlineGenerator:
    def __init__(self) -> None:
        self._planner = OutlinePlanner()

    async def generate_outline(
        self,
        user_persona: UserPersona,
        world_setting: WorldSetting,
        character_info: CharacterInfo,
        total_chapters: int,
    ) -> StoryOutline:
        return await self._planner.propose(
            protagonist=character_info,
            world=world_setting,
            user_persona=user_persona,
            total_chapters=total_chapters,
        )

    @staticmethod
    def format_outline_for_display(outline: StoryOutline) -> str:
        lines: List[str] = []
        lines.append("=" * 60)
        lines.append(f"故事大纲: {outline.title}")
        lines.append(f"主题: {outline.theme}")
        lines.append(f"总章节数: {outline.total_chapters}")
        lines.append("=" * 60)
        for ch in outline.chapters:
            lines.append(f"\n【第{ch.chapter_number}章】{ch.title}")
            lines.append(f"  核心冲突: {ch.core_conflict}")
            lines.append(f"  场景: {ch.scene_setting}")
            lines.append(f"  角色互动: {ch.character_interaction}")
            lines.append(f"  剧情作用: {ch.plot_function}")
            if ch.branch_points:
                lines.append(f"  选择分支: {', '.join(ch.branch_points)}")
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
