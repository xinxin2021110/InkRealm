"""Memory —— 角色的工作记忆。

照搬 MetaGPT.memory.Memory：list + 按 cause_by 的反向索引，
提供 add / get / get_by_action / find_news 等。
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Set

from ..schema import Message, any_to_str, any_to_str_set


class Memory:
    """轻量工作记忆。"""

    def __init__(self, max_size: int = 200) -> None:
        self.storage: List[Message] = []
        self.index: Dict[str, List[Message]] = defaultdict(list)
        self.max_size = max_size

    # ---------------- 增 ----------------

    def add(self, msg: Message) -> None:
        if msg in self.storage:
            return
        self.storage.append(msg)
        if msg.cause_by:
            self.index[msg.cause_by].append(msg)
        # 软上限：保留最近 max_size
        if len(self.storage) > self.max_size:
            drop = self.storage[: len(self.storage) - self.max_size]
            self.storage = self.storage[-self.max_size :]
            for m in drop:
                if m.cause_by and m in self.index[m.cause_by]:
                    self.index[m.cause_by].remove(m)

    def add_batch(self, msgs: Iterable[Message]) -> None:
        for m in msgs:
            self.add(m)

    # ---------------- 查 ----------------

    def get(self, k: int = 0) -> List[Message]:
        if k <= 0:
            return list(self.storage)
        return self.storage[-k:]

    def get_by_action(self, action) -> List[Message]:
        return list(self.index.get(any_to_str(action), []))

    def get_by_actions(self, actions) -> List[Message]:
        actions_set: Set[str] = any_to_str_set(actions)
        out: List[Message] = []
        for a in actions_set:
            out.extend(self.index.get(a, []))
        return out

    def get_by_role(self, role: str) -> List[Message]:
        return [m for m in self.storage if m.role == role]

    def find_news(self, observed: List[Message], k: int = 0) -> List[Message]:
        """从 observed 里挑出尚未存进 storage 的"新消息"。"""
        seen = {m.id for m in self.storage}
        news = [m for m in observed if m.id not in seen]
        if k > 0:
            news = news[-k:]
        return news

    # ---------------- 工具 ----------------

    def clear(self) -> None:
        self.storage.clear()
        self.index.clear()

    def __len__(self) -> int:
        return len(self.storage)
