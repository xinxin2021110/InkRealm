"""Environment 基类。

具体业务环境已迁移到：
- novel_character_agent.environment.ChatEnvironment
- novel_story_agent.environment.WritingEnvironment
"""
from .base_env import Environment

__all__ = ["Environment"]
