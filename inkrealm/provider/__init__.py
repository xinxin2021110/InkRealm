"""LLM provider 工厂。"""
from __future__ import annotations

from .base_llm import BaseLLM
from .deepseek_llm import DeepSeekLLM


def create_llm(llm_config) -> BaseLLM:
    """根据 LLMConfig 选择实现。当前只有 DeepSeek / 兼容 OpenAI 协议的入口。"""
    return DeepSeekLLM(llm_config)


__all__ = ["BaseLLM", "DeepSeekLLM", "create_llm"]
