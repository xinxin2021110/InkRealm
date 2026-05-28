"""ChapterWriterRole —— 同人作者 Role。

ReAct 模式：BY_ORDER（DraftChapter → SummarizeChapter → ExtractKeyEvents 串行执行）。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from inkrealm.roles.role import Role, RoleReactMode
from inkrealm.schema import (
    ChapterContent,
    ChapterOutline,
    CharacterProfile,
    UserPersona,
    WorldSetting,
    WritingStyle,
)

from ..actions import (
    DraftChapterAction,
    ExtractKeyEventsAction,
    SummarizeChapterAction,
)


class ChapterWriterRole(Role):
    def __init__(self) -> None:
        super().__init__(
            name="ChapterWriter",
            profile="同人作者",
            goal="按大纲撰写风格对齐的章节，并附摘要 / 关键事件",
        )
        self.draft = DraftChapterAction()
        self.summarize = SummarizeChapterAction()
        self.extract = ExtractKeyEventsAction()
        self.set_actions([self.draft, self.summarize, self.extract])
        self.set_react_mode(RoleReactMode.BY_ORDER, max_loop=3)

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
        *,
        min_len: int = 2000,
        max_len: int = 5000,
    ) -> ChapterContent:
        draft_out = await self.draft.run(
            chapter_outline,
            user_persona,
            protagonist,
            world,
            style,
            previous_chapters,
            relationship_state,
            user_power_level,
            flags,
            min_len=min_len,
            max_len=max_len,
        )
        chapter: ChapterContent = draft_out.instruct_content  # type: ignore[assignment]

        sum_out = await self.summarize.run(chapter.content)
        chapter.summary = sum_out.content

        kev_out = await self.extract.run(chapter.content)
        try:
            chapter.key_events = json.loads(kev_out.content or "[]")
        except Exception:
            chapter.key_events = []

        return chapter
