"""Action 基类 —— 任何 LLM/检索/工具操作的最小单元。

参考 MetaGPT.actions.Action：
- 有 `name / desc / node`；
- `run(*args, **kwargs)` 是子类必须实现的入口；
- 通过 ContextMixin 拿到全局 LLM；
- 可以挂一个 ActionNode 做结构化输出（子类按需用）。
"""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional

from ..context import ContextMixin
from .action_node import ActionNode
from .action_output import ActionOutput


class Action(ContextMixin):
    """Action 抽象基类。"""

    name: str = ""
    desc: str = ""
    node: Optional[ActionNode] = None

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        desc: Optional[str] = None,
        node: Optional[ActionNode] = None,
    ) -> None:
        if name is not None:
            self.name = name
        elif not self.name:
            self.name = self.__class__.__name__
        if desc is not None:
            self.desc = desc
        if node is not None:
            self.node = node
        self._context_kv: Dict[str, Any] = {}

    # ---------------- LLM 便捷调用 ----------------

    async def _aask(
        self,
        prompt: str,
        *,
        system_msgs: Optional[List[str]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        return await self.llm.aask(
            prompt,
            system_msgs=system_msgs,
            history=history,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def _aask_stream(
        self,
        prompt: str,
        *,
        system_msgs: Optional[List[str]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        async for chunk in self.llm.aask_stream(
            prompt,
            system_msgs=system_msgs,
            history=history,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk

    async def _aask_json(
        self,
        prompt: str,
        *,
        system_msgs: Optional[List[str]] = None,
        temperature: Optional[float] = 0.3,
    ) -> Any:
        return await self.llm.aask_json(prompt, system_msgs=system_msgs, temperature=temperature)

    # ---------------- 状态 ----------------

    def set_kv(self, **kwargs: Any) -> "Action":
        self._context_kv.update(kwargs)
        return self

    def get_kv(self, key: str, default: Any = None) -> Any:
        return self._context_kv.get(key, default)

    # ---------------- 子类必须实现 ----------------

    async def run(self, *args: Any, **kwargs: Any) -> ActionOutput:
        raise NotImplementedError(f"{self.__class__.__name__} 需实现 run()")
