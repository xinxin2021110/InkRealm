"""RetrieveMemoryAction —— 检索与本轮对话强相关的角色记忆。

升级点：
1. 默认启用"多 hop"检索（query 含人名时先精确捞实体相关记忆）。
2. 返回**分层后**的记忆，保证 prompt 里 SCENE / EVENT / MOTIVATION / DIALOGUE_SAMPLE 都有代表。
3. 输出格式带"[type @第N章]"前缀，让 LLM 知道每条记忆的类型与时序。
"""
from __future__ import annotations

from typing import List, Optional

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.context import get_context
from inkrealm.retrieval import MemoryRetriever
from inkrealm.schema import MemoryItem


class RetrieveMemoryAction(Action):
    name = "RetrieveMemory"
    desc = "对用户最新发言做多通道+多 hop 记忆检索，返回分层后的 top-k 条记忆"

    def __init__(
        self,
        retriever: MemoryRetriever,
        max_memories: Optional[int] = None,
        use_hops: bool = True,
    ) -> None:
        super().__init__()
        self.retriever = retriever
        cfg = get_context().config.memory
        self.max_memories = max_memories or cfg.max_relevant_memories
        self.use_hops = use_hops
        self._retrieved: List[MemoryItem] = []

    async def run(self, query: str) -> ActionOutput:  # type: ignore[override]
        if not self.retriever:
            return ActionOutput(content="（无可用记忆库）")
        if self.use_hops:
            self._retrieved = self.retriever.retrieve_with_hops(query, top_k=self.max_memories)
        else:
            self._retrieved = self.retriever.retrieve(query, top_k=self.max_memories)
        if not self._retrieved:
            return ActionOutput(content="（暂无与当前对话强相关的记忆）")
        return ActionOutput(content=self._format(self._retrieved))

    @property
    def retrieved(self) -> List[MemoryItem]:
        return self._retrieved

    @staticmethod
    def _format(items: List[MemoryItem]) -> str:
        lines: List[str] = []
        for i, m in enumerate(items, 1):
            chap = f"第{m.chapter_order}章" if m.chapter_order else "未知章节"
            tag = m.memory_type
            lines.append(f"{i}. [{tag} @ {chap}] {m.content}")
        return "\n".join(lines)
