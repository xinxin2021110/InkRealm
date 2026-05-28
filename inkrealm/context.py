"""Context —— 显式依赖注入容器（参考 MetaGPT.context.Context）。

每个 Role / Action 通过 ContextMixin 拿到当前 context，再从 context 取 llm / config /
cost_manager。允许 Role 通过 `private_llm` / `private_config` 覆盖。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from .config import Config


class Context:
    """轻量级、可懒构造的全局上下文。

    与 MetaGPT 一致：把 config / llm / kwargs 三件事统一收纳，
    避免散落的全局变量。
    """

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config: Config = config or Config.default()
        self.kwargs: Dict[str, Any] = {}
        self._llm = None  # 懒构造

    # ---------------- LLM ----------------

    @property
    def llm(self):
        if self._llm is None:
            from .provider import create_llm

            self._llm = create_llm(self.config.llm)
        return self._llm

    def use_llm(self, llm) -> None:
        """测试 / 替换实现时手动注入。"""
        self._llm = llm

    # ---------------- 杂项 ----------------

    def get(self, key: str, default: Any = None) -> Any:
        return self.kwargs.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.kwargs[key] = value


# 单例（可被替换）
_GLOBAL: Optional[Context] = None


def get_context() -> Context:
    global _GLOBAL
    if _GLOBAL is None:
        _GLOBAL = Context()
    return _GLOBAL


def init_context(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    config: Optional[Config] = None,
) -> Context:
    """供 webapp 启动时一次性配置。"""
    global _GLOBAL
    _GLOBAL = Context(config=config or Config.default())
    if api_key or base_url or model:
        _GLOBAL.config.override_llm(api_key=api_key, base_url=base_url, model=model)
    # 失效已有 LLM，便于下次按新配置重建
    _GLOBAL._llm = None
    return _GLOBAL


class ContextMixin:
    """Role / Action 共用的注入入口。

    优先级：private_llm > private_config.llm > global context.llm。
    """

    _private_llm = None  # type: ignore[assignment]

    @property
    def context(self) -> Context:
        return get_context()

    @property
    def llm(self):
        if self._private_llm is not None:
            return self._private_llm
        return self.context.llm

    def use_llm(self, llm) -> None:
        self._private_llm = llm

    @property
    def config(self) -> Config:
        return self.context.config


__all__ = ["Context", "ContextMixin", "get_context", "init_context"]
