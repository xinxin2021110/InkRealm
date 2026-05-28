"""logging — 双通道（stderr + 日期文件） + 可注入的流式回调。

照搬 MetaGPT logs.py 的精髓：用 ContextVar 把"LLM 流式 token"打通到
任何上层消费者（命令行 print / FastAPI SSE / 单测）。
"""
from __future__ import annotations

import asyncio
import logging
import sys
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable, Optional


# ---------------- logger ----------------

class _Logger:
    """轻量 logger，避免硬依赖 loguru。"""

    def __init__(self, name: str = "inkrealm") -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            self._setup()

    def _setup(self) -> None:
        self._logger.setLevel(logging.INFO)
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%H:%M:%S",
        )
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        self._logger.addHandler(sh)

        # 文件 handler 可选 —— 失败时静默
        try:
            log_dir = Path.cwd() / "logs"
            log_dir.mkdir(exist_ok=True)
            fh = logging.FileHandler(
                log_dir / f"{datetime.now():%Y%m%d}.log",
                encoding="utf-8",
            )
            fh.setFormatter(fmt)
            self._logger.addHandler(fh)
        except Exception:
            pass

    def info(self, msg: str, *a, **kw) -> None:
        self._logger.info(msg, *a, **kw)

    def warning(self, msg: str, *a, **kw) -> None:
        self._logger.warning(msg, *a, **kw)

    def error(self, msg: str, *a, **kw) -> None:
        self._logger.error(msg, *a, **kw)

    def debug(self, msg: str, *a, **kw) -> None:
        self._logger.debug(msg, *a, **kw)


logger = _Logger()


# ---------------- 流式回调 ----------------
# LLM_STREAM_QUEUE 让每个请求有自己的流通道；webapp 把 SSE 写入器塞进去，
# 命令行场景塞 stdout writer，单测可塞 list.append。

LLM_STREAM_QUEUE: ContextVar[Optional[asyncio.Queue]] = ContextVar(
    "LLM_STREAM_QUEUE", default=None
)


StreamFunc = Callable[[str], Awaitable[None]]


_stream_log: StreamFunc = None  # type: ignore[assignment]


def set_llm_stream_logfunc(func: Optional[StreamFunc]) -> None:
    """注入"每收到一个 token"的回调；传 None 表示走默认（写 ContextVar 队列）。"""
    global _stream_log
    _stream_log = func


async def llm_stream_log(chunk: str) -> None:
    """LLM provider 在收到流式 token 时调用，分发给所有订阅者。"""
    if _stream_log:
        await _stream_log(chunk)
        return
    q = LLM_STREAM_QUEUE.get()
    if q is not None:
        await q.put(chunk)


__all__ = [
    "logger",
    "LLM_STREAM_QUEUE",
    "set_llm_stream_logfunc",
    "llm_stream_log",
]
