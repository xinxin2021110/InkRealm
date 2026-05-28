"""Environment 基类 —— 消息路由 + 角色容器 + 并发调度。

照搬 MetaGPT.environment.base_env.Environment：
- `add_role` 注册角色并把自己 set_env 到角色；
- `publish_message` 根据 `send_to`/`<all>` 把消息塞进每个角色的 msg_buffer；
- `run(k=1)` 并发跑所有 not-idle 角色的 react；
- `is_idle` 用于 Team 退出循环。
"""
from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Set

from ..const import MESSAGE_ROUTE_TO_ALL
from ..logs import logger
from ..memory import Memory
from ..schema import Message
from ..roles.role import Role


class Environment:
    """通用环境。"""

    def __init__(self, *, desc: str = "") -> None:
        self.desc = desc
        self.roles: Dict[str, Role] = {}
        self.history: Memory = Memory(max_size=500)

    # ---------------- 角色管理 ----------------

    def add_role(self, role: Role) -> None:
        self.roles[role.name] = role
        role.set_env(self)

    def add_roles(self, roles: List[Role]) -> None:
        for r in roles:
            self.add_role(r)

    # ---------------- 消息 ----------------

    def publish_message(self, msg: Message) -> bool:
        self.history.add(msg)
        targets: Set[str] = set(msg.send_to or {MESSAGE_ROUTE_TO_ALL})
        for r_name, role in self.roles.items():
            if MESSAGE_ROUTE_TO_ALL in targets or r_name in targets:
                # 自己发的消息不再投递给自己
                if msg.sent_from and msg.sent_from == r_name:
                    continue
                role.put_message(msg)
        return True

    # ---------------- 调度 ----------------

    async def run(self, k: int = 1) -> None:
        for _ in range(k):
            await asyncio.gather(
                *(r.react() for r in self.roles.values() if not r.is_idle)
            )

    @property
    def is_idle(self) -> bool:
        return all(r.is_idle for r in self.roles.values())

    # ---------------- 工具 ----------------

    def get_role(self, name: str) -> Optional[Role]:
        return self.roles.get(name)
