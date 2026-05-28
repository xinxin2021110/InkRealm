"""Team —— 多 Agent 编排入口（创业公司隐喻）。"""
from __future__ import annotations

from typing import Iterable, Optional

from .environment.base_env import Environment
from .logs import logger
from .roles.role import Role


class Team:
    """轻量 Team：hire / run。"""

    def __init__(self, env: Optional[Environment] = None) -> None:
        self.env = env or Environment()
        self.idea: str = ""

    def hire(self, roles: Iterable[Role]) -> "Team":
        for r in roles:
            self.env.add_role(r)
        return self

    def assign(self, idea: str) -> "Team":
        self.idea = idea
        return self

    async def run(self, n_round: int = 5) -> None:
        for _ in range(n_round):
            if self.env.is_idle:
                logger.info("Team: 环境空闲，结束。")
                break
            await self.env.run(k=1)
