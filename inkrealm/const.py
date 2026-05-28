"""项目常量。"""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 通用流式 sentinel
STREAM_END = "[[STREAM_END]]"

# Action 路由前缀
MESSAGE_ROUTE_TO_ALL = "<all>"
MESSAGE_ROUTE_TO_NONE = "<none>"
MESSAGE_ROUTE_TO_SELF = "<self>"

# 默认角色身份字符串（可被 Role.profile 覆盖）
PROFILE_DEFAULT = "通用智能体"
