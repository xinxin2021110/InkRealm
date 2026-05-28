"""GeneratePersonaDimensionsAction —— 4 维度 × 4 选项的人设菜单。"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.schema import (
    CharacterProfile,
    PersonaDimension,
    PersonaDimensions,
    PersonaOption,
    WorldSetting,
)


PROMPT = """\
请为同人小说"用户角色"设计四维度选项，目标是与原著主角{character_name}产生丰富的化学反应。

【作品】《{book}》  题材：{genre}
【世界观摘要】
{world_background}

【力量/能力体系】（若该题材无超能力体系，请基于角色身份背景设计相应选项）
{power_system}

【主角核心档案】
- 性格：{personality}
- 关键动机：{motivations}

请输出以下 JSON：
{{
  "background":  {{ "description": "出身/家世/起点说明", "options": [4 个 PersonaOption] }},
  "personality": {{ "description": "性格倾向说明",      "options": [4 个 PersonaOption] }},
  "relationship":{{ "description": "与主角初始关系说明", "options": [4 个 PersonaOption] }},
  "ability":     {{ "description": "立足之本（能力 / 才艺 / 资源）说明", "options": [4 个 PersonaOption] }}
}}

每个 PersonaOption 字段：
- id: "A" / "B" / "C" / "D"
- title: 8-12 字
- description: 60-100 字
- implications: 30-50 字，说明对剧情走向的影响

⚠️ 选项必须紧扣"题材 / 世界观 / 力量体系"。
不要硬塞"修炼 / 元力 / 武功"等术语，除非世界观确实属于该范畴。
"""


class GeneratePersonaDimensionsAction(Action):
    name = "GeneratePersonaDimensions"
    desc = "根据世界观与主角生成 4 维度 × 4 选项的人设菜单"

    async def run(
        self,
        world: WorldSetting,
        protagonist: CharacterProfile,
    ) -> ActionOutput:  # type: ignore[override]
        prompt = PROMPT.format(
            character_name=protagonist.name,
            book=protagonist.book_title,
            genre=world.genre or "（未明确）",
            world_background=world.world_background or "（资料较少）",
            power_system=(world.power_system_desc or "（该题材未显式力量体系）"),
            personality="，".join(protagonist.personality_traits[:6]) or "（资料不足）",
            motivations="；".join(protagonist.key_motivations[:4]) or "（资料不足）",
        )
        data = await self._aask_json(prompt, temperature=0.6)
        fallback = self._fallback(protagonist.name)
        dims_dict: Dict[str, PersonaDimension] = {}
        title_map = {
            "background": "出身",
            "personality": "性格",
            "relationship": "羁绊",
            "ability": "能力",
        }
        for k in ("background", "personality", "relationship", "ability"):
            raw = data.get(k) or fallback[k]
            opts: List[PersonaOption] = []
            for opt in (raw.get("options") or [])[:4]:
                opts.append(
                    PersonaOption(
                        id=str(opt.get("id", "")).upper() or "A",
                        title=opt.get("title", ""),
                        description=opt.get("description", ""),
                        implications=opt.get("implications", "") or "",
                    )
                )
            while len(opts) < 4:
                placeholder = chr(ord("A") + len(opts))
                opts.append(PersonaOption(id=placeholder, title=f"待补{placeholder}", description="（占位选项）"))
            dims_dict[k] = PersonaDimension(
                key=k,
                title=title_map[k],
                description=raw.get("description", ""),
                options=opts,
            )
        dimensions = PersonaDimensions(**dims_dict)
        return ActionOutput(content=json.dumps(data, ensure_ascii=False), instruct_content=dimensions)

    # 题材无关的兜底 ----------------
    @staticmethod
    def _fallback(name: str) -> Dict[str, Any]:
        def opt(letter: str, title: str, desc: str, imp: str) -> Dict[str, Any]:
            return {"id": letter, "title": title, "description": desc, "implications": imp}

        return {
            "background": {
                "description": "选择你的出身/起点，决定故事开局的资源和限制。",
                "options": [
                    opt("A", "亲近世家", f"出身与{name}所在阵营有渊源的家族子弟，能较快靠近他。", "起点近，但资源平庸"),
                    opt("B", "市井之人", "城内/坊间普通人家出身，自由度高，缺乏背景。", "需自力更生"),
                    opt("C", "漂泊孤客", "无依无靠的外来者，身世神秘。", "戏剧性高，易触发奇遇"),
                    opt("D", "对立营垒", f"出身与{name}有过节的势力，立场对立。", "矛盾感强，情感张力大"),
                ],
            },
            "personality": {
                "description": "选择你的性格底色，决定与主角的互动模式。",
                "options": [
                    opt("A", "热血直爽", "重情重义、果决勇敢。", "适合并肩作战"),
                    opt("B", "机谋深沉", "心思缜密、长于谋略。", "适合智斗与协调"),
                    opt("C", "温和细腻", "善解人意、长于共情。", "适合情感戏与治愈"),
                    opt("D", "孤高冷峻", "寡言克制、藏锋于内。", "悬念感强、关系成长慢"),
                ],
            },
            "relationship": {
                "description": "你与主角的初始关系。",
                "options": [
                    opt("A", "旧识发小", f"与{name}相识已久，了解他/她过去。", "信任基础牢"),
                    opt("B", "针锋初遇", "首次见面便有冲突或竞争。", "从对手到伙伴"),
                    opt("C", "施救之恩", "曾在关键时刻救过对方。", "关系自带恩义"),
                    opt("D", "隐秘引路", "你似乎知道一些与他相关的秘密。", "好奇与警惕并存"),
                ],
            },
            "ability": {
                "description": "选择你的立足之本：能力、才艺或资源。",
                "options": [
                    opt("A", "本职出众", "在该世界主流能力体系内天赋不俗。", "正面战力可用"),
                    opt("B", "稀缺专精", "拥有一种相对稀有的专业能力或独门技艺。", "在特定场景独挑大梁"),
                    opt("C", "信息渠道", "掌握情报/网络/人脉资源。", "推动情节"),
                    opt("D", "奇巧工具", "擅长机关、器物或独门工具。", "解谜与探险"),
                ],
            },
        }
