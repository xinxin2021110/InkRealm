"""AnalyzeWorldSettingAction —— 从样本章节中提炼通用世界观（题材无关）。"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.schema import WorldSetting


PROMPT = """\
请你担任"作品世界观提取助理"。基于以下章节样本，提炼这本小说所属的世界观信息。

【作品名】{book}
【主要分析角色】{character}
【章节样本（最多 6 章）】
{samples}

请输出 JSON：
- genre: 一个简短类型标签（如：玄幻、武侠、仙侠、都市、言情、科幻、历史、悬疑、推理、奇幻、武术 …）；若不属于以上常见类型可自由命名
- power_system_name: 该书"力量/能力体系"的名字。若该书是现实题材没有特殊能力体系，输出空字符串
- power_system_desc: 力量体系/特殊技艺的详细介绍（≤200 字）
- power_levels: 实力 / 等级 / 段位的有序阶梯（从低到高），若无可给空数组
- major_forces: 主要派系 / 组织，每项 {{name, description}}
- world_background: 世界 / 时空背景概括（≤200 字）
- current_timeline: 当前故事所处时间点（≤60 字）
- key_locations: 重要地点列表，最多 8 项
"""


class AnalyzeWorldSettingAction(Action):
    name = "AnalyzeWorldSetting"
    desc = "从样本章节提炼通用世界观（不假设题材）"

    async def run(
        self,
        book_title: str,
        target_character_name: str,
        sample_chapters: List[Dict[str, Any]],
    ) -> ActionOutput:  # type: ignore[override]
        samples_txt = json.dumps(sample_chapters[:6], ensure_ascii=False, indent=2)
        prompt = PROMPT.format(
            book=book_title, character=target_character_name, samples=samples_txt
        )
        data = await self._aask_json(prompt, temperature=0.3)
        try:
            world = WorldSetting(
                genre=data.get("genre", "") or "",
                power_system_name=data.get("power_system_name", "") or "",
                power_system_desc=data.get("power_system_desc", "") or "",
                power_levels=list(data.get("power_levels") or []),
                major_forces=list(data.get("major_forces") or []),
                world_background=data.get("world_background", "") or "",
                current_timeline=data.get("current_timeline", "") or "",
                key_locations=list(data.get("key_locations") or []),
            )
        except Exception:
            world = WorldSetting()
        return ActionOutput(content=json.dumps(data, ensure_ascii=False), instruct_content=world)
