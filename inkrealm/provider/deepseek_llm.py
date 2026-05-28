"""DeepSeek / OpenAI 兼容 LLM provider 实现。"""
from __future__ import annotations

from typing import AsyncIterator, Dict, List, Optional

from openai import AsyncOpenAI

from ..logs import llm_stream_log, logger
from .base_llm import BaseLLM


class DeepSeekLLM(BaseLLM):
    """走 OpenAI Python SDK 的 chat.completions 协议，可用于 DeepSeek 等兼容服务。"""

    def __init__(self, llm_config) -> None:
        super().__init__(llm_config)
        self._client = AsyncOpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            timeout=llm_config.request_timeout,
        )

    async def achat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str:
        if stream:
            chunks: List[str] = []
            async for c in self.achat_stream(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                chunks.append(c)
            return "".join(chunks)

        try:
            resp = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=False,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"DeepSeekLLM.achat 失败: {e}")
            raise

    async def achat_stream(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        try:
            resp = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature if temperature is not None else self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=True,
            )
        except Exception as e:
            logger.error(f"DeepSeekLLM.achat_stream 失败: {e}")
            raise

        async for chunk in resp:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            piece = getattr(delta, "content", None)
            if piece:
                # 同时推到全局流通道（webapp SSE 会监听）
                try:
                    await llm_stream_log(piece)
                except Exception:
                    pass
                yield piece
