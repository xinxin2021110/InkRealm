"""统一配置。所有子系统都从这里取。

设计上参考 MetaGPT.config2.Config：用 pydantic BaseModel 描述每一组配置，
顶层 Config 持有它们。`Config.default()` 从 env 与默认值构造单例，
但也可以在测试 / webapp 启动时手动 override。
"""
from __future__ import annotations

import os
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------- 子配置 ----------------

class LLMConfig(BaseModel):
    api_key: str = "sk-66a329fb2054471a9a44e8cadbca9df5"
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"  # ★ 修正：原来 "deepseek-v4-flash" 不存在
    temperature: float = 0.7
    max_tokens: int = 4096
    stream_buffer_size: int = 0  # 0 表示来一个 token 推一次

    request_timeout: int = 180


class EmbeddingConfig(BaseModel):
    """Embedding：默认走内置 TF-IDF，可切到外部 API。"""

    provider: str = "tfidf"  # tfidf | api
    vector_size: int = 256
    use_bigrams: bool = True

    # API 模式时使用
    api_model: str = "text-embedding-3-small"


class MemoryConfig(BaseModel):
    max_short_term: int = 20
    max_relevant_memories: int = 10
    max_quotes_per_turn: int = 100


class GenerationConfig(BaseModel):
    chapter_min_length: int = 2000
    chapter_max_length: int = 5000
    min_outline_chapters: int = 3
    max_outline_chapters: int = 20
    choices_per_chapter: int = 4
    style_samples_count: int = 6


class ChatConfig:
    """聊天后处理"""
    forbid_action_description: bool = True


# ---------------- 顶层 Config ----------------

class Config(BaseModel):
    """全局配置容器。"""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)

    # 通用偏好
    forbid_action_description: bool = True

    @classmethod
    def default(cls) -> "Config":
        cfg = cls()
        # 允许 env 覆盖
        cfg.llm.api_key = os.getenv("INKREALM_LLM_API_KEY", cfg.llm.api_key)
        cfg.llm.base_url = os.getenv("INKREALM_LLM_BASE_URL", cfg.llm.base_url)
        cfg.llm.model = os.getenv("INKREALM_LLM_MODEL", cfg.llm.model)
        return cfg

    # ----- 简便 setter（供 webapp 在启动时调用） -----

    def override_llm(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> "Config":
        if api_key:
            self.llm.api_key = api_key
        if base_url:
            self.llm.base_url = base_url
        if model:
            self.llm.model = model
        if temperature is not None:
            self.llm.temperature = temperature
        return self


__all__ = [
    "Config",
    "LLMConfig",
    "EmbeddingConfig",
    "MemoryConfig",
    "GenerationConfig",
]
