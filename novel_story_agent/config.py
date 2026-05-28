"""adapter: 旧 config.init_config / get_config 转发到 inkrealm.Context。"""
from __future__ import annotations

from typing import Optional

from inkrealm.context import get_context, init_context


def init_config(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    data_path: Optional[str] = None,
):
    ctx = init_context(api_key=api_key, base_url=base_url, model=model)
    if temperature is not None:
        ctx.config.llm.temperature = temperature
    return ctx


def get_config():
    return get_context().config
