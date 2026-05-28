"""LLM 抽象基类 —— 任何后端都要实现这套异步接口。

参照 MetaGPT.provider.base_llm.BaseLLM 的最小契约：
- aask(prompt, system_msgs, history, stream) -> str
- aask_stream(...) -> AsyncIterator[str]
- achat(messages, ...) -> str
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional


class BaseLLM(ABC):
    """所有 LLM provider 的统一异步接口。"""

    def __init__(self, llm_config) -> None:
        self.config = llm_config

    # ---------------- 必须实现 ----------------

    @abstractmethod
    async def achat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str:
        """非流式聊天。"""

    @abstractmethod
    async def achat_stream(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """流式聊天。yield token 字符串片段。"""

    # ---------------- 高阶便捷方法 ----------------

    async def aask(
        self,
        prompt: str,
        system_msgs: Optional[List[str]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """与 MetaGPT.aask 同名同义：把 system + history + prompt 拼成 messages 调 achat。"""
        messages: List[Dict[str, str]] = []
        for s in system_msgs or []:
            if s:
                messages.append({"role": "system", "content": s})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return await self.achat(
            messages, temperature=temperature, max_tokens=max_tokens
        )

    async def aask_stream(
        self,
        prompt: str,
        system_msgs: Optional[List[str]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """流式版的 aask。"""
        messages: List[Dict[str, str]] = []
        for s in system_msgs or []:
            if s:
                messages.append({"role": "system", "content": s})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        async for chunk in self.achat_stream(
            messages, temperature=temperature, max_tokens=max_tokens
        ):
            yield chunk

    async def aask_json(
        self,
        prompt: str,
        system_msgs: Optional[List[str]] = None,
        *,
        temperature: Optional[float] = None,
    ) -> Any:
        """约束 JSON 输出 + 健壮解析。失败返回 {}。"""
        sys_msgs = list(system_msgs or []) + [
            "你必须严格以 JSON 格式返回，不要包裹任何 markdown 代码块标记，不要附加解释。"
        ]
        raw = await self.aask(prompt, system_msgs=sys_msgs, temperature=temperature or 0.3)
        return self._safe_parse_json(raw)

    @staticmethod
    def _safe_parse_json(raw: str) -> Any:
        """容错的 JSON 解析：移除 ```json ... ``` 包裹、抽取第一个 {...} 或 [...]。"""
        if not raw:
            return {}
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except Exception:
            pass
        # 兜底：找 {...} 或 [...] 的最大块
        for open_c, close_c in (("{", "}"), ("[", "]")):
            i = text.find(open_c)
            j = text.rfind(close_c)
            if i >= 0 and j > i:
                try:
                    return json.loads(text[i : j + 1])
                except Exception:
                    continue
        return {}
