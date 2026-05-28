"""EntityIndex —— 把"人名 / 地名 / 别名 / 关键术语"做 O(1) 反向索引。

两个用途：
1. 多 hop 检索的第一跳：query 里若提到关系人或地点，先精确捞出全部相关条目。
2. 多通道融合的 entity 通道：命中实体 → 加分。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Set


class EntityIndex:
    """把每条记录与其包含的实体名做双向映射。"""

    def __init__(self) -> None:
        self._by_entity: Dict[str, Set[int]] = defaultdict(set)
        self._entities_of_doc: Dict[int, Set[str]] = defaultdict(set)
        self._entity_pool: Set[str] = set()

    # ---------------- 构建 ----------------

    def add_entities(self, entities: Iterable[str]) -> None:
        for e in entities:
            if e and isinstance(e, str):
                self._entity_pool.add(e.strip())

    def index(self, doc_idx: int, text: str) -> None:
        for e in self._entity_pool:
            if not e:
                continue
            if e in text:
                self._by_entity[e].add(doc_idx)
                self._entities_of_doc[doc_idx].add(e)

    def index_explicit(self, doc_idx: int, entities: Iterable[str]) -> None:
        """给已知该文档相关人名时使用（优于扫描）。"""
        for e in entities:
            if e and e in self._entity_pool:
                self._by_entity[e].add(doc_idx)
                self._entities_of_doc[doc_idx].add(e)

    # ---------------- 查询 ----------------

    def find_entities_in(self, text: str) -> List[str]:
        if not text:
            return []
        return [e for e in self._entity_pool if e and e in text]

    def docs_for_entity(self, entity: str) -> List[int]:
        return list(self._by_entity.get(entity, set()))

    def docs_for_entities(self, entities: Sequence[str]) -> List[int]:
        out: Set[int] = set()
        for e in entities:
            out |= self._by_entity.get(e, set())
        return list(out)

    def entities_of(self, doc_idx: int) -> List[str]:
        return list(self._entities_of_doc.get(doc_idx, set()))

    @property
    def entity_pool(self) -> Set[str]:
        return self._entity_pool
