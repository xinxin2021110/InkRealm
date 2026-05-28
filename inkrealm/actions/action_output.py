"""ActionOutput —— 沿用 MetaGPT 的"原始 content + 结构化 instruct_content"二元契约。"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ActionOutput:
    """所有 Action.run() 的统一返回类型。"""

    content: str
    instruct_content: Optional[BaseModel]

    def __init__(self, content: str = "", instruct_content: Optional[BaseModel] = None) -> None:
        self.content = content
        self.instruct_content = instruct_content

    def __repr__(self) -> str:
        head = self.content[:60].replace("\n", " ")
        return f"ActionOutput(content={head!r}, instruct={type(self.instruct_content).__name__ if self.instruct_content else 'None'})"
