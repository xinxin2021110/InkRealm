"""SummarizeChapterAction / ExtractKeyEventsAction —— 写章节摘要与抽取关键事件。"""
from __future__ import annotations

import json

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput


class SummarizeChapterAction(Action):
    name = "SummarizeChapter"
    desc = "为章节生成 100-150 字摘要"

    async def run(self, content: str) -> ActionOutput:  # type: ignore[override]
        if not content:
            return ActionOutput(content="")
        prompt = (
            "请为下面这一章生成 100-150 字的剧情摘要，只输出摘要文本，"
            "不要使用任何 markdown、章节号、引号。\n\n"
            f"【章节正文（节选）】\n{content[:2400]}"
        )
        summary = await self._aask(prompt, temperature=0.3, max_tokens=400)
        return ActionOutput(content=summary.strip())


class ExtractKeyEventsAction(Action):
    name = "ExtractKeyEvents"
    desc = "提取章节关键事件（3-5 条）"

    async def run(self, content: str) -> ActionOutput:  # type: ignore[override]
        if not content:
            return ActionOutput(content="[]")
        prompt = (
            "请从以下章节中提取 3-5 个关键事件，输出 JSON 数组（仅含字符串），"
            "不要包含其它解释。\n\n"
            f"【章节正文（节选）】\n{content[:2400]}"
        )
        data = await self._aask_json(prompt, temperature=0.3)
        if not isinstance(data, list):
            data = []
        events = [str(x) for x in data][:5]
        return ActionOutput(content=json.dumps(events, ensure_ascii=False))
