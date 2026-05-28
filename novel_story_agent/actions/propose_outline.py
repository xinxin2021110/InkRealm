"""ProposeStoryOutlineAction —— 整本故事大纲。"""
from __future__ import annotations

import json
from typing import List

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.schema import (
    ChapterOutline,
    CharacterProfile,
    StoryOutline,
    UserPersona,
    WorldSetting,
)


PROMPT = """\
请为《{book}》的同人故事生成 {n} 章大纲。主线必须围绕"用户角色 {user}"与原著主角"{protagonist}"的互动展开。

【作品类型】{genre}
【世界观摘要】
{world_background}
【力量/能力体系（若适用）】
{power_system}

【主角档案】
- 性格：{personality}
- 动机：{motivations}

【用户角色档案】
- 名字：{user}
- 出身：{user_background}
- 性格：{user_personality}
- 与主角关系：{user_relation}
- 立足之本：{user_ability}
- 详细背景：{user_background_detail}

请输出 JSON：
{{
  "title": "故事总标题",
  "theme": "故事主题（≤30 字）",
  "chapters": [
    {{
      "chapter_number": 1,
      "title": "章节标题",
      "core_conflict": "本章核心冲突",
      "scene_setting": "主要场景",
      "character_interaction": "用户角色与主角的互动点",
      "plot_function": "本章在整体的作用",
      "branch_points": ["可分支选择 1", "可分支选择 2"]
    }}
  ]
}}

设计原则：
1. 开篇必须迅速建立"用户角色 ↔ 主角"的连接（相遇/冲突/羁绊）。
2. 中段安排成长 / 困境 / 转折。
3. 高潮章包含决定性事件。
4. 每章留出"用户可影响剧情"的分支点。
5. ★ 不要使用任何题材外的术语；若世界观未提到"修炼/灵气/异能"等，请勿擅自添加。
"""


class ProposeStoryOutlineAction(Action):
    name = "ProposeStoryOutline"
    desc = "基于世界观 + 主角 + 用户人设，产出整本故事大纲"

    async def run(
        self,
        protagonist: CharacterProfile,
        world: WorldSetting,
        user_persona: UserPersona,
        total_chapters: int,
    ) -> ActionOutput:  # type: ignore[override]
        prompt = PROMPT.format(
            book=protagonist.book_title,
            n=total_chapters,
            user=user_persona.name,
            protagonist=protagonist.name,
            genre=world.genre or "（未明确）",
            world_background=world.world_background or "（资料较少）",
            power_system=(world.power_system_desc or "（该题材无显式力量体系）"),
            personality="，".join(protagonist.personality_traits[:6]) or "（资料不足）",
            motivations="；".join(protagonist.key_motivations[:4]) or "（资料不足）",
            user_background=user_persona.background,
            user_personality=user_persona.personality,
            user_relation=user_persona.relationship_to_protagonist,
            user_ability=user_persona.initial_ability,
            user_background_detail=user_persona.background_detail[:200],
        )
        data = await self._aask_json(prompt, temperature=0.75)

        chapters_data = data.get("chapters") or []
        chapters: List[ChapterOutline] = []
        for i, ch in enumerate(chapters_data):
            chapters.append(
                ChapterOutline(
                    chapter_number=int(ch.get("chapter_number", i + 1)),
                    title=ch.get("title", f"第 {i + 1} 章"),
                    core_conflict=ch.get("core_conflict", "") or "",
                    scene_setting=ch.get("scene_setting", "") or "",
                    character_interaction=ch.get("character_interaction", "") or "",
                    plot_function=ch.get("plot_function", "") or "",
                    branch_points=list(ch.get("branch_points") or []),
                )
            )
        while len(chapters) < total_chapters:
            n = len(chapters) + 1
            chapters.append(
                ChapterOutline(
                    chapter_number=n,
                    title=f"第 {n} 章",
                    core_conflict="新的事件/冲突",
                    scene_setting=protagonist.book_title,
                    character_interaction=f"{user_persona.name}与{protagonist.name}进一步互动",
                    plot_function="推进主线",
                    branch_points=["关键抉择点"],
                )
            )
        chapters = chapters[:total_chapters]

        outline = StoryOutline(
            total_chapters=total_chapters,
            title=data.get("title", f"《{protagonist.book_title}》同人：{user_persona.name}的故事"),
            theme=data.get("theme", "成长与羁绊"),
            chapters=chapters,
        )
        return ActionOutput(content=json.dumps(data, ensure_ascii=False), instruct_content=outline)
