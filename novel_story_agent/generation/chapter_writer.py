"""ChapterWriter / ChoiceGenerator —— webapp 仍在用的入口。

内部委托给 ChapterWriterRole 与 PlotDirector Role。
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..roles.chapter_writer_role import ChapterWriterRole
from ..roles.plot_director import PlotDirector
from ..schema import (
    ChapterChoices,
    ChapterContent,
    ChapterOutline,
    CharacterInfo,
    UserPersona,
    WorldSetting,
    WritingStyle,
)


class ChapterWriter:
    def __init__(self) -> None:
        self._role = ChapterWriterRole()
        # webapp 调过 writer.choice_generator.generate_choices(...) —— 给它挂上
        self.choice_generator = ChoiceGenerator()

    async def write_chapter(
        self,
        chapter_outline: ChapterOutline,
        user_persona: UserPersona,
        character_info: CharacterInfo,
        world_setting: WorldSetting,
        writing_style: WritingStyle,
        previous_chapters: List[ChapterContent],
        relationship_state: Dict[str, int],
        user_power_level: str,
        flags: Dict[str, Any],
    ) -> ChapterContent:
        return await self._role.write_chapter(
            chapter_outline=chapter_outline,
            user_persona=user_persona,
            protagonist=character_info,
            world=world_setting,
            style=writing_style,
            previous_chapters=previous_chapters,
            relationship_state=relationship_state,
            user_power_level=user_power_level,
            flags=flags,
        )


class ChoiceGenerator:
    """webapp 仍在用：写章节后单独生成 4 个选项的接口。"""

    def __init__(self) -> None:
        self._director = PlotDirector()

    async def generate_choices(
        self,
        chapter_content: ChapterContent,
        user_persona: UserPersona,
        character_info: CharacterInfo,
        relationship_state: Dict[str, int],
        user_power_level: str,
        flags: Dict[str, Any],
    ) -> ChapterChoices:
        return await self._director.generate_choices(
            chapter=chapter_content,
            user_persona=user_persona,
            protagonist=character_info,
            relationship_state=relationship_state,
            user_power_level=user_power_level,
            flags=flags,
        )

    @staticmethod
    def format_choices_for_display(choices: ChapterChoices) -> str:
        lines: List[str] = []
        lines.append("\n" + "=" * 60)
        lines.append("【互动选择】")
        lines.append(f"当前情境: {choices.situation_summary}")
        lines.append("=" * 60)
        for opt in choices.options:
            lines.append(f"\n【{opt.option_id}】{opt.text}")
            if opt.description:
                lines.append(f"  详情: {opt.description}")
            if opt.impact:
                lines.append(f"  影响: {opt.impact}")
            if opt.risk:
                lines.append(f"  风险: {opt.risk}")
        lines.append("\n" + "=" * 60)
        lines.append("请输入选项字母(A/B/C/D)进行选择")
        lines.append("=" * 60)
        return "\n".join(lines)
