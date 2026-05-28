"""JSONL 角色数据加载 —— 充分利用所有字段构建 CharacterProfile。

PRD 字段使用策略：
| jsonl 字段           | 取出方向                                              |
|----------------------|-------------------------------------------------------|
| book_title           | profile.book_title                                    |
| target_character     | profile.name                                          |
| aliases              | profile.aliases                                       |
| chapter_order        | MemoryItem.chapter_order / DialogueExample.chapter_order |
| chapter_title        | MemoryItem.chapter / DialogueExample.chapter          |
| mention_count        | MemoryItem.mention_count / DialogueExample.mention_count；用作 weight 主因素 |
| is_relevant          | 过滤无关章节（is_relevant=False 跳过）                |
| summary              | 单独成为 SCENE 类记忆 + 注入到 MemoryItem.scene_summary |
| memory_points        | EVENT 类记忆（细粒度事件）                            |
| personality_traits   | profile.personality_traits + 章节级 PERSONALITY_DESC 记忆 |
| emotional_state      | profile.emotional_states + MemoryItem.emotion         |
| speech_style         | profile.speech_style                                  |
| dialogue_examples    | DIALOGUE_SAMPLE 类记忆（较完整对话） + DialogueExample(is_evidence=False) |
| relationships        | profile.relationships + 提取人名做 related_people     |
| key_motivations      | profile.key_motivations + MOTIVATION 类记忆           |
| evidence_quotes      | DialogueExample(is_evidence=True) (主语录池，≥100 条注入) |
| confidence           | 透传到 MemoryItem.confidence / DialogueExample.confidence |
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from ..logs import logger
from ..schema import (
    CharacterProfile,
    DialogueExample,
    MemoryItem,
    MemoryType,
    Relationship,
)


class JsonlLoader:
    """读 JSONL → 给定 target_character → CharacterProfile。"""

    def __init__(self, data_file: str) -> None:
        self.data_file = Path(data_file)
        if not self.data_file.exists():
            raise FileNotFoundError(f"数据文件不存在: {data_file}")
        self._raw: List[Dict[str, Any]] = []

    # ---------------- 公开 ----------------

    def load_raw(self) -> List[Dict[str, Any]]:
        if self._raw:
            return self._raw
        out: List[Dict[str, Any]] = []
        with open(self.data_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"跳过损坏的行: {e}")
        self._raw = out
        return out

    def available_characters(self) -> List[str]:
        return sorted(
            {
                (r.get("target_character") or "").strip()
                for r in self.load_raw()
                if r.get("target_character")
            }
        )

    def build_profile(self, target_character: Optional[str] = None) -> CharacterProfile:
        rows = self.load_raw()
        if not rows:
            raise ValueError("JSONL 为空")
        if target_character is None:
            target_character = rows[0].get("target_character", "")

        # 关键：尊重 is_relevant；同时按 chapter_order 升序保证时序
        chapter_rows = [
            r for r in rows
            if r.get("target_character") == target_character
            and r.get("is_relevant", True) is not False
        ]
        if not chapter_rows:
            raise ValueError(f"角色不存在: {target_character}")
        chapter_rows.sort(key=lambda r: int(r.get("chapter_order") or 0))

        first = chapter_rows[0]
        book_title = first.get("book_title", "")
        aliases = [a for a in (first.get("aliases") or []) if isinstance(a, str) and a]

        # 聚合维度（角色级）
        personality: List[str] = []
        emotional: List[str] = []
        speech: List[str] = []
        motivations: List[str] = []
        seen_pers: Set[str] = set()
        seen_emo: Set[str] = set()
        seen_sty: Set[str] = set()
        seen_mot: Set[str] = set()

        relations: List[Relationship] = []
        memories: List[MemoryItem] = []
        quotes: List[DialogueExample] = []

        # mention_count 全局最大值，用于 weight 归一化
        max_mention = max((int(ch.get("mention_count") or 0) for ch in chapter_rows), default=1) or 1

        for ch in chapter_rows:
            chap_order = int(ch.get("chapter_order") or 0)
            chap_title = ch.get("chapter_title", "") or ""
            mention = int(ch.get("mention_count") or 0)
            confidence = float(ch.get("confidence") or 1.0)
            chap_summary = (ch.get("summary") or "").strip()
            chap_emo_raw = ch.get("emotional_state") or []
            chap_emo: List[str] = (
                [chap_emo_raw] if isinstance(chap_emo_raw, str) else list(chap_emo_raw)
            )
            primary_emo = chap_emo[0] if chap_emo else ""

            # weight = 0.5 + 0.5 * (mention/max) 然后乘以 confidence；落在 [0.5*conf, 1.0*conf]
            weight = (0.5 + 0.5 * (mention / max_mention)) * confidence

            # 1) 性格关键词（角色级 + 章节级 PERSONALITY_DESC 记忆）
            traits = ch.get("personality_traits") or []
            for t in traits:
                if t and t not in seen_pers:
                    seen_pers.add(t)
                    personality.append(t)
            if traits:
                memories.append(self._make_memory(
                    content=f"在『{chap_title}』中体现的性格：{', '.join(traits)}",
                    chap_order=chap_order, chap_title=chap_title,
                    mtype=MemoryType.PERSONALITY_DESC.value,
                    mention=mention, confidence=confidence,
                    weight=weight, scene_summary=chap_summary, emotion=primary_emo,
                ))

            # 2) 情绪
            for e in chap_emo:
                if e and e not in seen_emo:
                    seen_emo.add(e)
                    emotional.append(e)

            # 3) 说话风格
            sty = ch.get("speech_style") or []
            if isinstance(sty, str):
                sty = [sty]
            for s in sty:
                if s and s not in seen_sty:
                    seen_sty.add(s)
                    speech.append(s)

            # 4) 动机：角色级 + MOTIVATION 类记忆
            motiv = ch.get("key_motivations") or []
            for m in motiv:
                if m and m not in seen_mot:
                    seen_mot.add(m)
                    motivations.append(m)
            if motiv:
                memories.append(self._make_memory(
                    content=f"动机驱动：{'；'.join(motiv)}",
                    chap_order=chap_order, chap_title=chap_title,
                    mtype=MemoryType.MOTIVATION.value,
                    mention=mention, confidence=confidence,
                    weight=weight * 1.1,  # 动机略加权（更核心）
                    scene_summary=chap_summary, emotion=primary_emo,
                ))

            # 5) 关系
            rel_names_in_chapter: List[str] = []
            for r in (ch.get("relationships") or []):
                rel_name = r.get("name", "") or ""
                if rel_name:
                    rel_names_in_chapter.append(rel_name)
                relations.append(Relationship(
                    name=rel_name,
                    relation=r.get("relation", "") or "",
                    interaction=r.get("interaction", "") or "",
                    attitude=r.get("attitude", "") or "",
                ))

            # 6) summary → SCENE 记忆（让"问起 XX 章发生了什么"能命中）
            if chap_summary:
                memories.append(self._make_memory(
                    content=chap_summary,
                    chap_order=chap_order, chap_title=chap_title,
                    mtype=MemoryType.SCENE.value,
                    mention=mention, confidence=confidence,
                    weight=weight * 1.05,  # 场景级也略加权
                    scene_summary=chap_summary, emotion=primary_emo,
                    related_people=rel_names_in_chapter,
                ))

            # 7) memory_points → EVENT 记忆（最细粒度，含场景上下文）
            for mp in (ch.get("memory_points") or []):
                if not mp:
                    continue
                memories.append(self._make_memory(
                    content=mp,
                    chap_order=chap_order, chap_title=chap_title,
                    mtype=MemoryType.EVENT.value,
                    mention=mention, confidence=confidence,
                    weight=weight,
                    scene_summary=chap_summary, emotion=primary_emo,
                    related_people=self._mention_filter(mp, rel_names_in_chapter),
                ))

            # 8) dialogue_examples → DIALOGUE_SAMPLE 记忆 + 同时入语录池（is_evidence=False）
            for d in (ch.get("dialogue_examples") or []):
                if not d or len(d) < 5:
                    continue
                memories.append(self._make_memory(
                    content=d,
                    chap_order=chap_order, chap_title=chap_title,
                    mtype=MemoryType.DIALOGUE_SAMPLE.value,
                    mention=mention, confidence=confidence,
                    weight=weight,
                    scene_summary=chap_summary, emotion=primary_emo,
                    related_people=self._mention_filter(d, rel_names_in_chapter),
                ))
                quotes.append(DialogueExample(
                    content=d,
                    context=chap_summary[:200],
                    emotion=primary_emo or self._guess_emotion(d, chap_emo),
                    chapter=chap_title,
                    chapter_order=chap_order,
                    mention_count=mention,
                    confidence=confidence,
                    is_evidence=False,
                    related_people=self._mention_filter(d, rel_names_in_chapter),
                ))

            # 9) evidence_quotes → 强证据语录（主语录池）
            for q in (ch.get("evidence_quotes") or []):
                if not q or len(q) < 5:
                    continue
                quotes.append(DialogueExample(
                    content=q,
                    context=chap_summary[:200],
                    emotion=primary_emo or self._guess_emotion(q, chap_emo),
                    chapter=chap_title,
                    chapter_order=chap_order,
                    mention_count=mention,
                    confidence=confidence,
                    is_evidence=True,
                    related_people=self._mention_filter(q, rel_names_in_chapter),
                ))

        profile = CharacterProfile(
            name=target_character,
            aliases=aliases,
            book_title=book_title,
            profile=f"《{book_title}》中的角色 {target_character}",
            personality_traits=personality,
            emotional_states=emotional,
            speech_style=speech,
            key_motivations=motivations,
            relationships=relations,
            memories=memories,
            dialogue_examples=quotes,
            total_chapters=len(chapter_rows),
            total_quotes=len(quotes),
        )
        logger.info(
            f"[JsonlLoader] {target_character}@{book_title}: "
            f"{len(chapter_rows)} 章 / {len(memories)} 记忆 "
            f"(EVENT/SCENE/MOTIVATION/PERSONALITY_DESC/DIALOGUE_SAMPLE) / {len(quotes)} 语录"
        )
        return profile

    # ---------------- helper ----------------

    @staticmethod
    def _make_memory(
        *,
        content: str,
        chap_order: int,
        chap_title: str,
        mtype: str,
        mention: int,
        confidence: float,
        weight: float,
        scene_summary: str = "",
        emotion: str = "",
        related_people: Optional[List[str]] = None,
    ) -> MemoryItem:
        return MemoryItem(
            content=content,
            chapter=chap_title,
            chapter_order=chap_order,
            memory_type=mtype,
            mention_count=mention,
            confidence=confidence,
            weight=weight,
            scene_summary=scene_summary,
            emotion=emotion,
            related_people=list(related_people or []),
        )

    @staticmethod
    def _mention_filter(text: str, names: Iterable[str]) -> List[str]:
        """从文本里挑出确实出现过的人名。"""
        return [n for n in names if n and n in text]

    _EMO_KW = {
        "喜悦": ["笑", "乐", "高兴", "开心", "哈哈"],
        "悲伤": ["哭", "泪", "伤心", "难过", "悲"],
        "愤怒": ["怒", "怒火", "气", "讨厌", "可恶"],
        "关切": ["关心", "担心", "保重", "怎么样"],
        "感激": ["谢谢", "感激", "感动"],
        "尴尬": ["尴尬", "不好意思"],
    }

    @classmethod
    def _guess_emotion(cls, text: str, chapter_emos) -> str:
        for e, kws in cls._EMO_KW.items():
            for kw in kws:
                if kw in text:
                    return e
        if chapter_emos:
            if isinstance(chapter_emos, str):
                return chapter_emos
            if isinstance(chapter_emos, list) and chapter_emos:
                return chapter_emos[0]
        return "中性"
