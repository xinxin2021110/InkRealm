"""InkRealm — MetaGPT 风格的多 Agent 小说复刻与共创框架。

设计原则：
1. 与具体小说彻底解耦 —— 任何 prompt / 算法都不出现具体角色名 / 世界观术语；
   所有内容都从 NovelProfile / WorldSetting 动态注入。
2. 多 Agent 协作 —— 通过 Message + Memory + Environment + Team 编排，
   照搬 MetaGPT 的 Role / Action / ActionNode 抽象。
3. 异步流式 —— BaseLLM 暴露 `aask` 与 `aask_stream`，便于 Web 端 SSE。
"""
from __future__ import annotations

__version__ = "2.0.0"

from .context import Context, get_context, init_context
from .logs import logger
from .schema import (
    AIMessage,
    Message,
    MessageQueue,
    SystemMessage,
    UserMessage,
)

__all__ = [
    "__version__",
    "Context",
    "get_context",
    "init_context",
    "logger",
    "Message",
    "UserMessage",
    "SystemMessage",
    "AIMessage",
    "MessageQueue",
]
