"""Action 体系入口。

只保留通用基础设施层（Action / ActionNode / ActionOutput）。
业务相关的 Action 已迁移到：
- novel_character_agent.actions.*
- novel_story_agent.actions.*

旧路径 `inkrealm.actions.chat_actions` 等仍可用，会重新导出业务包同名类。
"""
from .action import Action
from .action_node import ActionNode
from .action_output import ActionOutput

__all__ = ["Action", "ActionNode", "ActionOutput"]
