"""RetrieveQuotesAction —— 检索原著真实语录（≥100 条）。

升级点：
1. evidence_quotes 与 dialogue_examples 同池检索，evidence 自带打分加权；
2. 返回时**仍然用前 N 条**作为提示用，但额外暴露统计供调用方写日志/前端显示；
3. 文本清洗：剥离括号动作描写，避免污染 prompt。
"""
from __future__ import annotations

import re
from typing import List, Optional

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.context import get_context
from inkrealm.retrieval import QuoteRetriever
from inkrealm.schema import DialogueExample


class RetrieveQuotesAction(Action):
    name = "RetrieveQuotes"
    desc = "检索原著真实语录用于风格对齐（默认 ≥100 条，至多 50 条进入 prompt）"

    def __init__(
        self,
        retriever: QuoteRetriever,
        min_quotes: Optional[int] = None,
        max_in_prompt: int = 50,
    ) -> None:
        super().__init__()
        self.retriever = retriever
        cfg = get_context().config.memory
        self.min_quotes = min_quotes or cfg.max_quotes_per_turn
        self.max_in_prompt = max_in_prompt
        self._retrieved: List[DialogueExample] = []

    async def run(self, query: str) -> ActionOutput:  # type: ignore[override]
        if not self.retriever:
            return ActionOutput(content="（无可用语录库）")
        self._retrieved = self.retriever.retrieve(query, min_quotes=self.min_quotes)
        if not self._retrieved:
            return ActionOutput(content="（暂无可参考的真实语录）")

        view = self._retrieved[: self.max_in_prompt]
        lines: List[str] = []
        for i, q in enumerate(view, 1):
            cleaned = self._clean(q.content)
            if not cleaned:
                continue
            tag = "原著" if q.is_evidence else "片段"
            lines.append(f"{i}. ({tag}) {cleaned}")
        return ActionOutput(content="\n".join(lines))

    @property
    def retrieved(self) -> List[DialogueExample]:
        return self._retrieved

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"[（(].*?[）)]", "", text or "")
        text = re.sub(r"[\[【].*?[\]】]", "", text)
        return " ".join(text.split()).strip()
