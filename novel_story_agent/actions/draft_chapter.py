"""DraftChapterAction —— 写一章正文（题材无关、风格对齐）。"""
from __future__ import annotations

from typing import Any, Dict, List

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.schema import (
    ChapterContent,
    ChapterOutline,
    CharacterProfile,
    UserPersona,
    WorldSetting,
    WritingStyle,
)


CHAPTER_PROMPT = """\
你将续写《{book}》的同人章节。语言、节奏要严格贴合"作者风格"。

## 作者风格签名
{author_signature}

## 写作风格特征（必须遵循）
- 叙事：{narrative_features}
- 对话：{dialogue_features}
- 描写：{description_features}

## 风格样本（请学习此节奏与口吻，不要照抄）
{style_samples}

## 作品世界观
- 类型：{genre}
- 背景：{world_background}
- 力量/能力体系：{power_system}
- 等级阶梯（若适用）：{power_levels}

## 主角 {protagonist} 档案
- 性格：{personality}
- 说话风格：{speech_style}
- 关键动机：{motivations}

## 用户角色 {user} 档案
- 出身：{user_background}
- 性格：{user_personality}
- 与主角关系：{user_relation}
- 立足之本：{user_ability}
- 当前实力（如不适用力量体系，请视为"经验/资源等级"）：{user_power_level}
- 详细背景：{user_background_detail}

## 当前关系状态
{relationship_block}

## 前情提要
{previous_summary}

## 本章大纲
- 编号与标题：第{chapter_number}章 {chapter_title}
- 核心冲突：{core_conflict}
- 场景：{scene_setting}
- 互动点：{character_interaction}
- 剧情作用：{plot_function}

## 写作要求
1. 字数 {min_len}–{max_len} 之间。
2. 严格使用作品本身的术语，不要引入与世界观不符的概念。
3. 至少一处 {user} 与 {protagonist} 的实质互动。
4. 结尾留出张力（悬念/抉择/未决冲突），不要圆满收束。
5. 章节正文输出格式：第一行是 "第{chapter_number}章 {chapter_title}"，下一行起为正文段落，段落之间空一行。
6. **禁止在正文中夹杂作者旁白说明**，直接呈现故事。

直接输出章节正文，不要任何解释、JSON 或代码块。
"""


class DraftChapterAction(Action):
    name = "DraftChapter"
    desc = "根据大纲 + 上下文产出一章风格对齐的正文"

    async def run(
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
    ) -> ActionOutput:  # type: ignore[override]

        previous_summary = self._format_previous(previous_chapters)
        prompt = CHAPTER_PROMPT.format(
            book=protagonist.book_title,
            author_signature=style.author_signature or "（风格签名待补）",
            narrative_features="；".join(style.narrative_features[:6]) or "（资料不足）",
            dialogue_features="；".join(style.dialogue_features[:6]) or "（资料不足）",
            description_features="；".join(style.description_features[:6]) or "（资料不足）",
            style_samples=self._format_samples(style.sample_texts[:3]),
            genre=world.genre or "（未明确）",
            world_background=world.world_background or "（资料较少）",
            power_system=(world.power_system_desc or "（无显式力量体系）"),
            power_levels="、".join(world.power_levels) or "（无）",
            protagonist=protagonist.name,
            personality="，".join(protagonist.personality_traits[:6]) or "（资料不足）",
            speech_style="，".join(protagonist.speech_style[:5]) or "（资料不足）",
            motivations="；".join(protagonist.key_motivations[:4]) or "（资料不足）",
            user=user_persona.name,
            user_background=user_persona.background,
            user_personality=user_persona.personality,
            user_relation=user_persona.relationship_to_protagonist,
            user_ability=user_persona.initial_ability,
            user_power_level=user_power_level or "（初始水平）",
            user_background_detail=user_persona.background_detail[:200],
            relationship_block=self._format_rels(relationship_state),
            previous_summary=previous_summary,
            chapter_number=chapter_outline.chapter_number,
            chapter_title=chapter_outline.title,
            core_conflict=chapter_outline.core_conflict,
            scene_setting=chapter_outline.scene_setting,
            character_interaction=chapter_outline.character_interaction,
            plot_function=chapter_outline.plot_function,
            min_len=min_len,
            max_len=max_len,
        )

        content = await self._aask(prompt, temperature=0.85, max_tokens=4096)
        chapter = ChapterContent(
            chapter_number=chapter_outline.chapter_number,
            title=chapter_outline.title,
            content=content.strip(),
            characters_present=[protagonist.name, user_persona.name],
            power_level_after=user_power_level,
        )
        return ActionOutput(content=content, instruct_content=chapter)

    # helper ----------------------------------
    @staticmethod
    def _format_previous(prev: List[ChapterContent]) -> str:
        if not prev:
            return "（本章为故事第一章）"
        last = prev[-1]
        return (
            f"- 上一章标题：第{last.chapter_number}章 {last.title}\n"
            f"- 上一章摘要：{last.summary or '（无摘要）'}\n"
            f"- 关键事件：{', '.join(last.key_events[:5]) or '（无）'}"
        )

    @staticmethod
    def _format_samples(samples: List[str]) -> str:
        if not samples:
            return "（无）"
        return "\n\n".join([f"样本{i+1}: {s}" for i, s in enumerate(samples)])

    @staticmethod
    def _format_rels(rels: Dict[str, int]) -> str:
        if not rels:
            return "（无）"
        def tag(v: int) -> str:
            if v >= 60: return "亲密"
            if v >= 30: return "友好"
            if v > 0:   return "中立"
            if v > -30: return "冷淡"
            return "敌对"
        return "\n".join(f"- 与{name}：{v}（{tag(v)}）" for name, v in rels.items())
