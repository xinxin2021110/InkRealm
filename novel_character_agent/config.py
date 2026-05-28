"""adapter: 旧 config.init_config / get_config 转发到 inkrealm.Context。"""
from __future__ import annotations

from typing import Optional

from inkrealm.context import get_context, init_context


def init_config(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    data_file: Optional[str] = None,  # 保留参数，但不再有意义；旧 API 兼容
):
    ctx = init_context(api_key=api_key, base_url=base_url, model=model)
    return ctx


def get_config():
    """旧用法：`get_config().llm.api_key` 等仍可工作。"""
    return get_context().config
