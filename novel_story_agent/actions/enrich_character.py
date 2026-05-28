"""EnrichCharacterAction —— LLM 二次提取强化角色画像。"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.schema import CharacterProfile


PROMPT = """\
基于章节样本，对角色 {character} 做更完整的人物画像。已有基础信息如下：

【已有性格关键词】{personality}
【已有说话风格】{speech_style}
【章节样本】
{samples}

请输出 JSON：
- profile: 角色身份与背景介绍（≤180 字）
- personality_traits: 完整性格特点列表（去重，≤15 条）
- speech_style: 说话风格关键词（≤8 条）
- emotional_states: 常见情绪状态（≤8 条）
- key_motivations: 关键动机（≤6 条）

请确保推断不与样本冲突。
"""


class EnrichCharacterAction(Action):
    name = "EnrichCharacter"
    desc = "在已有 CharacterProfile 上做 LLM 二次提取强化"

    async def run(
        self,
        basic: CharacterProfile,
        sample_chapters: List[Dict[str, Any]],
    ) -> ActionOutput:  # type: ignore[override]
        prompt = PROMPT.format(
            character=basic.name,
            personality=", ".join(basic.personality_traits[:10]),
            speech_style=", ".join(basic.speech_style[:6]),
            samples=json.dumps(sample_chapters[:5], ensure_ascii=False, indent=2),
        )
        data = await self._aask_json(prompt, temperature=0.4)

        def merge(a: List[str], b: List[str]) -> List[str]:
            seen, out = set(), []
            for x in list(a) + list(b):
                if x and x not in seen:
                    seen.add(x)
                    out.append(x)
            return out

        enriched = basic.model_copy(update={
            "profile": data.get("profile", basic.profile) or basic.profile,
            "personality_traits": merge(basic.personality_traits, data.get("personality_traits") or []),
            "speech_style": merge(basic.speech_style, data.get("speech_style") or []),
            "emotional_states": merge(basic.emotional_states, data.get("emotional_states") or []),
            "key_motivations": merge(basic.key_motivations, data.get("key_motivations") or []),
        })
        return ActionOutput(content=json.dumps(data, ensure_ascii=False), instruct_content=enriched)
