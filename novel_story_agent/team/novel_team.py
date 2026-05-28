"""NovelTeam —— 把 5 个 Role 编排成一个"创业公司式"故事工坊。

设计理由：
- WritingEnvironment 暴露的是"高阶函数式 API"（一行调用一个步骤）；
- NovelTeam 暴露"产品式 API"（hire/run/run_until_finished），便于离线脚本一键跑全流程。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from inkrealm.team import Team

from ..environment.writing_environment import WritingEnvironment


class NovelTeam(Team):
    """专门用于"小说同人故事共创"的 Team。"""

    def __init__(self) -> None:
        env = WritingEnvironment()
        super().__init__(env=env)
        self.writing_env: WritingEnvironment = env

    # 直接对外暴露 writing_env 的高阶 API（避免 webapp 多绕一层）
    @property
    def world_analyst(self):
        return self.writing_env.world_analyst

    @property
    def persona_designer(self):
        return self.writing_env.persona_designer

    @property
    def outline_planner(self):
        return self.writing_env.outline_planner

    @property
    def chapter_writer(self):
        return self.writing_env.chapter_writer

    @property
    def plot_director(self):
        return self.writing_env.plot_director
