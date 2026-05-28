"""GenerateChapterChoicesAction —— 章末互动选项（题材无关）。"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.schema import (
    ChapterChoices,
    ChapterContent,
    CharacterProfile,
    ChoiceOption,
    UserPersona,
)


CHOICE_PROMPT = """\
请基于本章结尾的情境，为同人故事提供 4 个有意义的互动选项。

【作品】《{book}》  主角：{protagonist}
【用户角色】{user}（性格：{user_personality}，与主角关系：{user_relation}，立足之本：{user_ability}，当前实力：{user_power_level}）
【本章摘要】{summary}
【本章末段情境】
{ending}
【与主角当前关系值】{rel_value}（正→友好，负→敌对）

请输出 JSON：
{{
  "situation_summary": "用 30-60 字概括当下抉择情境",
  "options": [
    {{
      "option_id": "A",
      "text": "第一人称选项文本（30-50 字）",
      "description": "详细描述（50-90 字）",
      "tone": "本选项体现的情感/策略基调（2-6 字，例如：合作、试探、独行、坦诚……）",
      "impact": "对剧情走向的影响（30-50 字）",
      "risk": "潜在风险/代价（20-30 字）",
      "relationship_change": 5,
      "flags_set": ["可被后续章节读取的剧情标记（可选）"]
    }}
  ]
}}

设计要求：
1. 4 个选项必须风格各异，不要重复表达同一倾向。
2. 不要预设题材专属术语；要符合作品世界观逻辑。
3. 选项必须能"被下一章实际读到并产生差异"。
"""


class GenerateChapterChoicesAction(Action):
    name = "GenerateChapterChoices"
    desc = "为章节末尾生成 4 个互动选项（题材无关）"

    async def run(
        self,
        chapter: ChapterContent,
        user_persona: UserPersona,
        protagonist: CharacterProfile,
        relationship_state: Dict[str, int],
        user_power_level: str,
        flags: Dict[str, Any],
    ) -> ActionOutput:  # type: ignore[override]

        ending = self._extract_ending(chapter.content, length=600)
        prompt = CHOICE_PROMPT.format(
            book=protagonist.book_title,
            protagonist=protagonist.name,
            user=user_persona.name,
            user_personality=user_persona.personality,
            user_relation=user_persona.relationship_to_protagonist,
            user_ability=user_persona.initial_ability,
            user_power_level=user_power_level or "（初始）",
            summary=chapter.summary or "（无）",
            ending=ending,
            rel_value=relationship_state.get(protagonist.name, 0),
        )
        data = await self._aask_json(prompt, temperature=0.7)
        raw_options = (data.get("options") if isinstance(data, dict) else []) or []
        options: List[ChoiceOption] = []
        for o in raw_options[:4]:
            options.append(
                ChoiceOption(
                    option_id=str(o.get("option_id", "")).upper() or "A",
                    text=o.get("text", ""),
                    description=o.get("description", "") or "",
                    impact=o.get("impact", "") or "",
                    risk=o.get("risk", "") or "",
                    tone=o.get("tone", "") or "",
                    relationship_change={protagonist.name: int(o.get("relationship_change", 0) or 0)},
                    flags_set=list(o.get("flags_set") or []),
                )
            )
        while len(options) < 4:
            letter = chr(ord("A") + len(options))
            options.append(
                ChoiceOption(
                    option_id=letter,
                    text=f"（待补{letter}）顺势而为",
                    description="保持现状，观察事态发展",
                    impact="维持当前节奏",
                    risk="可能错失主动",
                    tone="观望",
                    relationship_change={protagonist.name: 0},
                )
            )
        choices = ChapterChoices(
            chapter_number=chapter.chapter_number,
            situation_summary=(data.get("situation_summary") if isinstance(data, dict) else "") or chapter.summary,
            options=options,
        )
        return ActionOutput(content=json.dumps(data, ensure_ascii=False), instruct_content=choices)

    @staticmethod
    def _extract_ending(content: str, length: int = 600) -> str:
        if not content:
            return ""
        lines = content.split("\n")
        if lines and lines[0].startswith("第") and "章" in lines[0]:
            lines = lines[1:]
        clean = "\n".join(lines).strip()
        if len(clean) > length:
            return "…" + clean[-length:]
        return clean
