"""AnalyzeWritingStyleAction —— 从原文样本提炼通用写作风格。"""
from __future__ import annotations

import json
from typing import List

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.schema import WritingStyle


PROMPT = """\
请你担任"作家风格分析师"。基于以下原文样本，提炼作者写作风格。

【原文样本】
{samples}

请输出 JSON：
- author_signature: 用一句话概括作者风格（≤30 字）
- narrative_features: 叙事特点要点列表（5-8 条）
- dialogue_features: 对话特点要点列表（4-6 条）
- description_features: 描写（环境/动作/心理）特点要点列表（4-6 条）

不要分析具体情节，只分析"语言层面"。
"""


class AnalyzeWritingStyleAction(Action):
    name = "AnalyzeWritingStyle"
    desc = "提炼作者写作风格的叙事/对话/描写特征"

    async def run(self, sample_texts: List[str]) -> ActionOutput:  # type: ignore[override]
        samples = "\n\n".join([f"样本{i+1}: {s}" for i, s in enumerate(sample_texts[:8])])
        prompt = PROMPT.format(samples=samples)
        data = await self._aask_json(prompt, temperature=0.3)
        style = WritingStyle(
            sample_texts=list(sample_texts),
            author_signature=data.get("author_signature", "") or "",
            narrative_features=list(data.get("narrative_features") or []),
            dialogue_features=list(data.get("dialogue_features") or []),
            description_features=list(data.get("description_features") or []),
        )
        return ActionOutput(content=json.dumps(data, ensure_ascii=False), instruct_content=style)
