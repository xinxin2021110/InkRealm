"""Role 基类 —— MetaGPT 风格的 ReAct 状态机。

精髓：
- `RoleContext` 持有 env / msg_buffer / memory / working_memory / state / todo / watch / react_mode；
- `RoleReactMode = REACT | BY_ORDER | PLAN_AND_ACT`；
- 公共入口 `react()`：先 `_observe`，再循环 `_think → _act`，直到完成或溢出。
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

from pydantic import BaseModel, Field

from ..context import ContextMixin
from ..logs import logger
from ..memory import Memory
from ..schema import (
    AIMessage,
    Message,
    MessageQueue,
    UserMessage,
    any_to_str,
    any_to_str_set,
)
from ..const import (
    MESSAGE_ROUTE_TO_ALL,
    MESSAGE_ROUTE_TO_NONE,
    MESSAGE_ROUTE_TO_SELF,
    PROFILE_DEFAULT,
)

if TYPE_CHECKING:
    from ..environment.base_env import Environment
    from ..actions.action import Action


class RoleReactMode(str, Enum):
    REACT = "react"          # 自由 think/act 循环
    BY_ORDER = "by_order"    # 按 actions 列表顺序逐个执行
    PLAN_AND_ACT = "plan_and_act"  # 先规划再执行（简化）


class RoleContext(BaseModel):
    """运行态容器。"""

    env: Optional[Any] = None  # 避免循环依赖
    msg_buffer: MessageQueue = Field(default_factory=MessageQueue)
    memory: Memory = Field(default_factory=Memory)
    working_memory: Memory = Field(default_factory=Memory)
    state: int = -1
    todo: Optional[Any] = None  # Action
    watch: Set[str] = Field(default_factory=set)
    react_mode: RoleReactMode = RoleReactMode.REACT
    max_react_loop: int = 1

    model_config = {"arbitrary_types_allowed": True}


class Role(ContextMixin):
    """通用 Role 基类（继承 ContextMixin，自带 llm / config / context）。"""

    name: str = ""
    profile: str = PROFILE_DEFAULT
    goal: str = ""
    constraints: str = ""
    desc: str = ""

    def __init__(
        self,
        *,
        name: Optional[str] = None,
        profile: Optional[str] = None,
        goal: Optional[str] = None,
        constraints: Optional[str] = None,
        desc: Optional[str] = None,
    ) -> None:
        if name:
            self.name = name
        elif not self.name:
            self.name = self.__class__.__name__
        if profile:
            self.profile = profile
        if goal:
            self.goal = goal
        if constraints:
            self.constraints = constraints
        if desc:
            self.desc = desc

        self.rc = RoleContext()
        self._actions: List["Action"] = []
        self._setup_actions()

    # ---------------- 用户可覆盖 ----------------

    def _setup_actions(self) -> None:
        """子类用 set_actions / set_watch 注册自己的能力。"""

    def set_actions(self, actions: List["Action"]) -> None:
        self._actions = list(actions)
        if self.rc.state == -1 and self._actions:
            self.rc.state = 0
            self.rc.todo = self._actions[0]

    def set_watch(self, watched) -> None:
        self.rc.watch = any_to_str_set(watched)

    def set_react_mode(self, mode: RoleReactMode, max_loop: int = 1) -> None:
        self.rc.react_mode = mode
        self.rc.max_react_loop = max_loop

    # ---------------- env ----------------

    def set_env(self, env: "Environment") -> None:
        self.rc.env = env

    # ---------------- 消息总线 ----------------

    def put_message(self, msg: Message) -> None:
        self.rc.msg_buffer.push(msg)

    def publish_message(self, msg: Message) -> None:
        """把消息发到环境。"""
        if self.rc.env is None:
            return
        self.rc.env.publish_message(msg)

    # ---------------- 心智循环 ----------------

    def _observe(self) -> List[Message]:
        """从 msg_buffer 取消息，并按 watch 过滤后落入 memory。"""
        news = self.rc.msg_buffer.pop_all()
        if not news:
            return []
        kept: List[Message] = []
        for m in news:
            if self.rc.watch and m.cause_by and m.cause_by not in self.rc.watch:
                # 用户消息可豁免 watch（保留 user → role 的入口）
                if m.role != "user":
                    continue
            kept.append(m)
        new_news = self.rc.memory.find_news(kept)
        self.rc.memory.add_batch(new_news)
        return new_news

    async def _think(self) -> Optional["Action"]:
        """选择下一个 Action。默认实现：用 BY_ORDER 推进。"""
        if not self._actions:
            return None
        if self.rc.react_mode == RoleReactMode.BY_ORDER:
            idx = max(0, self.rc.state)
            if idx >= len(self._actions):
                return None
            self.rc.state = idx
            self.rc.todo = self._actions[idx]
            return self.rc.todo
        # REACT / PLAN_AND_ACT：默认行为是停留在 actions[0]
        self.rc.todo = self._actions[0]
        return self.rc.todo

    async def _act(self) -> Optional[Message]:
        """执行 self.rc.todo —— 子类通常覆盖。"""
        todo = self.rc.todo
        if not todo:
            return None
        try:
            out = await todo.run()
        except Exception as e:
            logger.error(f"{self.name} 执行 {todo.name} 失败: {e}")
            return None
        msg = AIMessage(
            content=getattr(out, "content", str(out)),
            sent_from=self.name,
            cause_by=any_to_str(todo),
            instruct_content=getattr(out, "instruct_content", None),
        )
        self.rc.memory.add(msg)
        self.publish_message(msg)
        # 推进 state
        if self.rc.react_mode == RoleReactMode.BY_ORDER:
            self.rc.state += 1
        return msg

    async def react(self) -> Optional[Message]:
        """公共入口：observe → 循环 think/act。"""
        self._observe()
        last: Optional[Message] = None
        loops = 0
        # 上限：BY_ORDER 时一次跑完整条；REACT 时按 max_react_loop
        if self.rc.react_mode == RoleReactMode.BY_ORDER:
            while True:
                todo = await self._think()
                if todo is None:
                    break
                last = await self._act() or last
        else:
            while loops < max(1, self.rc.max_react_loop):
                todo = await self._think()
                if todo is None:
                    break
                last = await self._act() or last
                loops += 1
        return last

    @property
    def is_idle(self) -> bool:
        return self.rc.msg_buffer.empty()
