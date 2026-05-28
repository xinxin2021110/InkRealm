"""LongTermMemory —— 角色的长期记忆（小说事件 / 关系 / 情绪 / 对话）。

参照 MetaGPT.memory.longterm_memory：除了基本的 list/index，还多一个
按 type 的辅助索引；底层检索委托给 retrieval 模块的 Retriever。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from ..schema import CharacterProfile, MemoryItem


class LongTermMemory:
    """围绕 CharacterProfile.memories 构建的长期记忆视图。"""

    def __init__(self, profile: CharacterProfile) -> None:
        self.profile = profile
        self._by_type: Dict[str, List[MemoryItem]] = defaultdict(list)
        self._by_chapter: Dict[str, List[MemoryItem]] = defaultdict(list)
        for m in profile.memories:
            self._by_type[m.memory_type].append(m)
            if m.chapter:
                self._by_chapter[m.chapter].append(m)

    # ---------------- 取 ----------------

    def all(self) -> List[MemoryItem]:
        return list(self.profile.memories)

    def by_type(self, t: str) -> List[MemoryItem]:
        return list(self._by_type.get(t, []))

    def by_chapter(self, c: str) -> List[MemoryItem]:
        return list(self._by_chapter.get(c, []))

    def recent(self, n: int = 10) -> List[MemoryItem]:
        return list(self.profile.memories[-n:])

    def stats(self) -> Dict[str, int]:
        return {
            "total": len(self.profile.memories),
            **{f"type:{k}": len(v) for k, v in self._by_type.items()},
            "chapters": len(self._by_chapter),
        }
