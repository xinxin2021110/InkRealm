"""Roles —— 只保留通用基础设施层（Role 基类 + RoleContext + RoleReactMode）。

业务 Role 已迁移到：
- novel_character_agent.roles.CharacterRole
- novel_story_agent.roles.{WorldAnalyst, PersonaDesigner, OutlinePlanner, ChapterWriterRole, PlotDirector}
"""
from .role import Role, RoleContext, RoleReactMode

__all__ = ["Role", "RoleContext", "RoleReactMode"]
