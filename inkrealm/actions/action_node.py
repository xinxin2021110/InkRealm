"""ActionNode —— 最具 MetaGPT 特色的结构化 Prompt 节点。

精简版思路：
- 一个 ActionNode 描述"一段结构化输出"：key/desc/expected_type/instruction/example。
- 多个节点组合 → children，运行时把 children 编译成"JSON schema 块" + "example 块"
  注入到 prompt 模板，让 LLM 直接产出 JSON。
- 拿到 LLM 输出后用 `create_model()` 动态生成 pydantic 校验类，保证类型安全。

只支持 JSON Fill 模式（够用且最稳）。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError, create_model

from ..logs import logger


# ---------------- 通用模板 ----------------

ACTION_NODE_TEMPLATE = """\
你将完成一个结构化任务。请严格按下述【字段定义】产出 JSON，且只能输出 JSON 本体。

【任务说明】
{role_desc}

【输入上下文】
{context}

【字段定义】
{fields}

【输出格式示例（仅作格式参考，不要照抄字面内容）】
```json
{example_json}
```

请直接输出最终 JSON。
"""


# ---------------- ActionNode ----------------

class ActionNode:
    """一个结构化输出节点（可嵌套）。"""

    def __init__(
        self,
        key: str,
        expected_type: Type,
        instruction: str,
        example: Any = "",
        *,
        children: Optional[List["ActionNode"]] = None,
        required: bool = True,
    ) -> None:
        self.key = key
        self.expected_type = expected_type
        self.instruction = instruction
        self.example = example
        self.children: List[ActionNode] = list(children or [])
        self.required = required

        # 运行结果
        self.content: str = ""
        self.instruct_content: Optional[BaseModel] = None

    # ---------------- 组合 ----------------

    def add_child(self, node: "ActionNode") -> None:
        self.children.append(node)

    def add_children(self, nodes: List["ActionNode"]) -> None:
        self.children.extend(nodes)

    # ---------------- 编译 ----------------

    def _compile_fields_block(self) -> str:
        """把当前节点的 children 编译成给 LLM 看的字段说明列表。"""
        if not self.children:
            type_name = self._type_to_str(self.expected_type)
            return f"- {self.key} ({type_name})：{self.instruction}"
        lines: List[str] = []
        for c in self.children:
            type_name = self._type_to_str(c.expected_type)
            lines.append(f"- {c.key} ({type_name}, {'必填' if c.required else '可选'})：{c.instruction}")
        return "\n".join(lines)

    def _compile_example_json(self) -> str:
        """组装 example JSON。"""
        if not self.children:
            return json.dumps({self.key: self.example}, ensure_ascii=False, indent=2)
        example_obj: Dict[str, Any] = {}
        for c in self.children:
            example_obj[c.key] = c.example
        return json.dumps(example_obj, ensure_ascii=False, indent=2)

    def compile_prompt(self, role_desc: str, context: str) -> str:
        return ACTION_NODE_TEMPLATE.format(
            role_desc=role_desc.strip() or "请按下述字段产出 JSON。",
            context=context.strip() or "（无额外上下文）",
            fields=self._compile_fields_block(),
            example_json=self._compile_example_json(),
        )

    # ---------------- 动态 pydantic ----------------

    def _make_model_class(self) -> Type[BaseModel]:
        """根据 children 生成 pydantic 模型类。"""
        if not self.children:
            fields = {self.key: (self.expected_type, ...)}
            return create_model("DynamicSingle", **fields)  # type: ignore[arg-type]
        fields: Dict[str, Any] = {}
        for c in self.children:
            default = ... if c.required else None
            fields[c.key] = (c.expected_type, default)
        return create_model("DynamicComposite", **fields)  # type: ignore[arg-type]

    # ---------------- 运行 ----------------

    async def fill(
        self,
        *,
        llm,
        role_desc: str = "",
        context: str = "",
        temperature: Optional[float] = 0.3,
    ) -> "ActionNode":
        """调 LLM 拿 JSON，写入 self.content 与 self.instruct_content。"""
        prompt = self.compile_prompt(role_desc, context)
        raw = await llm.aask(prompt, temperature=temperature)
        self.content = raw
        data = llm._safe_parse_json(raw) if hasattr(llm, "_safe_parse_json") else self._fallback_parse(raw)
        if not isinstance(data, dict):
            logger.warning(f"ActionNode {self.key} 收到非 dict 解析结果，使用空对象。")
            data = {}
        model_cls = self._make_model_class()
        try:
            self.instruct_content = model_cls(**data)
        except ValidationError as e:
            logger.warning(f"ActionNode {self.key} 校验失败: {e}；降级用空字段。")
            try:
                # 用每个字段默认值兜底
                cleaned = self._coerce(data)
                self.instruct_content = model_cls(**cleaned)
            except Exception:
                self.instruct_content = None
        return self

    def _coerce(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """把字段类型简单 cast 一下，缺失字段用空值。"""
        out: Dict[str, Any] = {}
        children = self.children or [self]
        for c in children:
            v = data.get(c.key)
            if v is None:
                if c.expected_type is str:
                    v = ""
                elif c.expected_type is int:
                    v = 0
                elif get_origin(c.expected_type) is list:
                    v = []
                elif get_origin(c.expected_type) is dict:
                    v = {}
                else:
                    v = None
            out[c.key] = v
        return out

    @staticmethod
    def _fallback_parse(raw: str) -> Any:
        try:
            return json.loads(raw)
        except Exception:
            return {}

    # ---------------- 工具 ----------------

    @staticmethod
    def _type_to_str(t: Type) -> str:
        if get_origin(t) is list:
            inner = get_args(t)
            return f"List[{ActionNode._type_to_str(inner[0])}]" if inner else "List"
        if get_origin(t) is dict:
            return "Dict"
        if hasattr(t, "__name__"):
            return t.__name__
        return str(t)
