"""novel_character_agent.actions — 角色复刻产品的具体 Action。

这些 Action 都基于 inkrealm.Action 基类，是 MetaGPT 风格的"原子 LLM/检索任务"。
"""
from .retrieve_memory import RetrieveMemoryAction
from .retrieve_quotes import RetrieveQuotesAction
from .speak_in_character import SpeakInCharacterAction

__all__ = [
    "RetrieveMemoryAction",
    "RetrieveQuotesAction",
    "SpeakInCharacterAction",
]
