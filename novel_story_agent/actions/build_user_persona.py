"""BuildUserPersonaAction —— 根据用户选择生成完整 UserPersona。"""
from __future__ import annotations

import json
from typing import Any, Dict

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.schema import (
    CharacterProfile,
    PersonaDimension,
    PersonaDimensions,
    UserPersona,
    WorldSetting,
)


PROMPT = """\
你将为用户在《{book}》同人故事里设计一个完整、可落地的角色人设。

【用户输入】
- 我的名字：{user_name}
- 出身（{bg_id}）：{bg_title} — {bg_desc}
- 性格（{p_id}）：{p_title} — {p_desc}
- 与主角关系（{r_id}）：{r_title} — {r_desc}
- 立足之本（{a_id}）：{a_title} — {a_desc}

【作品世界观】
{world}

【主角档案】
- 姓名：{protagonist}
- 性格：{personality}
- 动机：{motivations}

请输出 JSON：
- background_detail: 出身详细设定，包括家庭 / 成长 / 当前处境（180-260 字）
- personality_detail: 性格深描，包括外在表现与内心动机（180-260 字）
- relationship_detail: 与主角关系详述，包括相识与互动模式（180-260 字）
- ability_detail: 能力详细设定，包括当前水平与与主角的互补性（180-260 字）
- story_goal: 角色核心目标 / 追求（60-100 字）

⚠️ 严禁出现与世界观矛盾的术语。若世界观未提及"修炼""丹田""灵气"等概念，请勿擅自加入。
"""


class BuildUserPersonaAction(Action):
    name = "BuildUserPersona"
    desc = "把维度选择 + 名字落地为完整 UserPersona"

    async def run(
        self,
        user_name: str,
        selections: Dict[str, str],
        dimensions: PersonaDimensions,
        protagonist: CharacterProfile,
        world: WorldSetting,
    ) -> ActionOutput:  # type: ignore[override]

        def pick(key: str) -> Any:
            dim: PersonaDimension = getattr(dimensions, key)
            target_id = (selections.get(key) or "A").upper()
            for o in dim.options:
                if o.id.upper() == target_id:
                    return o
            return dim.options[0]

        bg = pick("background")
        pe = pick("personality")
        re_ = pick("relationship")
        ab = pick("ability")

        prompt = PROMPT.format(
            book=protagonist.book_title,
            user_name=user_name,
            bg_id=bg.id, bg_title=bg.title, bg_desc=bg.description,
            p_id=pe.id, p_title=pe.title, p_desc=pe.description,
            r_id=re_.id, r_title=re_.title, r_desc=re_.description,
            a_id=ab.id, a_title=ab.title, a_desc=ab.description,
            world=(world.world_background or "（世界观资料不足）"),
            protagonist=protagonist.name,
            personality="，".join(protagonist.personality_traits[:6]) or "（资料不足）",
            motivations="；".join(protagonist.key_motivations[:4]) or "（资料不足）",
        )
        data = await self._aask_json(prompt, temperature=0.7)
        persona = UserPersona(
            name=user_name,
            background=bg.title,
            personality=pe.title,
            relationship_to_protagonist=re_.title,
            initial_ability=ab.title,
            story_goal=data.get("story_goal", "") or "",
            background_detail=data.get("background_detail", bg.description) or bg.description,
            personality_detail=data.get("personality_detail", pe.description) or pe.description,
            relationship_detail=data.get("relationship_detail", re_.description) or re_.description,
            ability_detail=data.get("ability_detail", ab.description) or ab.description,
        )
        return ActionOutput(content=json.dumps(data, ensure_ascii=False), instruct_content=persona)
