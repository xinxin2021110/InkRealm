"""ProfileBuilder —— 在 JsonlLoader 输出基础上做轻量整合。

设计变更：
- 旧版会重新分类 memory.memory_type 并覆写，但 JsonlLoader 已经做了精确分类，
  这里只做"关系合并 + 关键词抽取 + 字段去重"，不再篡改 memory_type / weight / scene_summary。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Set

from ..schema import CharacterProfile, MemoryItem, Relationship


class ProfileBuilder:
    def __init__(self, profile: CharacterProfile) -> None:
        self.profile = profile
        self._done = False

    def build(self) -> CharacterProfile:
        if self._done:
            return self.profile

        self.profile.relationships = self._merge_relationships()
        # 仅补充关键词（不动 memory_type / weight 等）
        rel_names = {r.name for r in self.profile.relationships if r.name}
        for m in self.profile.memories:
            if not m.keywords:
                m.keywords = self._extract_keywords(m.content, rel_names)
            # related_people 兜底
            if not m.related_people:
                m.related_people = [n for n in rel_names if n and n in m.content]

        self.profile.speech_style = self._dedup_strs(self.profile.speech_style)
        self.profile.personality_traits = self._dedup_strs(self.profile.personality_traits)
        self.profile.emotional_states = self._dedup_strs(self.profile.emotional_states)
        self.profile.key_motivations = self._dedup_strs(self.profile.key_motivations)

        self._done = True
        return self.profile

    # ---------------- 内部 ----------------

    @staticmethod
    def _dedup_strs(xs: List[str]) -> List[str]:
        seen: Set[str] = set()
        out: List[str] = []
        for x in xs:
            x = (x or "").strip()
            if x and x not in seen:
                seen.add(x)
                out.append(x)
        return out

    def _merge_relationships(self) -> List[Relationship]:
        bucket: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"relation": "", "interactions": [], "attitudes": []}
        )
        for r in self.profile.relationships:
            if not r.name:
                continue
            b = bucket[r.name]
            if r.relation:
                b["relation"] = r.relation
            if r.interaction:
                b["interactions"].append(r.interaction)
            if r.attitude:
                b["attitudes"].append(r.attitude)
        return [
            Relationship(
                name=n,
                relation=b["relation"],
                interaction=" / ".join(list(dict.fromkeys(b["interactions"])))[:600],
                attitude=" / ".join(list(dict.fromkeys(b["attitudes"])))[:200],
            )
            for n, b in bucket.items()
        ]

    # 通用语义关键词，不假设题材
    _GENERIC_KW = (
        "笑", "哭", "怒", "悲", "喜", "怕", "羞", "惊", "感动", "尴尬", "心动",
        "失望", "说", "问", "答", "喊", "叫", "回道", "低声",
    )

    def _extract_keywords(self, content: str, rel_names: Set[str]) -> List[str]:
        out: List[str] = []
        for n in rel_names:
            if n and n in content:
                out.append(n)
        for alias in self.profile.aliases:
            if alias and alias in content:
                out.append(alias)
        for kw in self._GENERIC_KW:
            if kw in content:
                out.append(kw)
        return list(dict.fromkeys(out))
