"""SpeakInCharacterAction —— 入戏回话（角色复刻产品的核心 Action）。

升级点（充分利用 jsonl 数据）：
1. **多维上下文**：除了原有"性格/说话风格/100+ 语录"，额外注入：
   - 检索命中的"章节摘要 SCENE"作为时空上下文；
   - 检索命中的"动机 MOTIVATION"提醒角色做事的内在驱动；
   - 检索命中的"对话样本 DIALOGUE_SAMPLE"提供更完整的口吻参照；
   - 关键人物当前态度，避免 OOC（例如对林山要敌视）。
2. **语录池区分**：evidence（原著直接引用）与 sample（章节对话样本）分开列出。
3. **后处理**：动作/神态/旁白描写过滤保持。
4. **流式 / 同步双入口**：与 webapp 已有 SSE 协议无缝衔接。
"""
from __future__ import annotations

import re
from typing import AsyncIterator, Dict, List, Optional

from inkrealm.actions.action import Action
from inkrealm.actions.action_output import ActionOutput
from inkrealm.schema import (
    CharacterProfile,
    DialogueExample,
    MemoryItem,
    Message,
    Relationship,
    WorldSetting,
)


CHAT_SYSTEM_TEMPLATE = """\
你将扮演小说《{book}》中的角色【{name}】。
请用"角色本人的口吻"回应对话方，做到符合原著性格、口语习惯与世界观逻辑。

## 角色档案
- 姓名：{name}
- 别名：{aliases}
- 身份：{profile_desc}
- 性格关键词：{personality}
- 常见情绪：{emotional_states}
- 说话习惯：{speech_style}
- 关键动机：{motivations}

## 重要人物关系（节选）
{relationships}

## 世界观与设定
{world_block}

## 与本轮对话相关的【场景上下文】（来自原著章节）
{scene_block}

## 与本轮对话相关的【内心动机】
{motivation_block}

## 与本轮对话相关的【事件记忆】
{event_block}

## 完整对话样本（学习节奏与口吻，不要照抄字面）
{dialogue_sample_block}

## 原著直接引用的真实语录（≤{quote_top_n} 条，仅作风格参照）
{evidence_block}

## 严格对话规则
1. 始终用第一人称"我"对话；称呼对方时请用对方在对话中体现的身份。
2. 你的语气、措辞、节奏必须吻合"说话习惯"和"性格关键词"。
3. **禁止输出任何动作 / 神态 / 旁白描写**（如"（微笑）""[低声]"），只输出纯对话。
4. 不要解释自己是"AI"或"在扮演"，全程沉浸。
5. 若对话方提到的事件超出你的记忆范围，请按你的性格自然应答，不要编造矛盾原著的事实。
6. 单次回应控制在 1-4 句话，符合本角色的说话节奏。
"""


class SpeakInCharacterAction(Action):
    name = "SpeakInCharacter"
    desc = "基于多维上下文以角色身份回话（支持流式）"

    def __init__(
        self,
        profile: CharacterProfile,
        world: Optional[WorldSetting] = None,
    ) -> None:
        super().__init__()
        self.profile = profile
        self.world = world or WorldSetting()

    # ---------------- 主入口（同步） ----------------

    async def run(
        self,
        user_input: str,
        *,
        retrieved_memories: Optional[List[MemoryItem]] = None,
        retrieved_quotes: Optional[List[DialogueExample]] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> ActionOutput:  # type: ignore[override]
        system = self._build_system(retrieved_memories or [], retrieved_quotes or [])
        messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_input})
        raw = await self.llm.achat(messages, temperature=0.75, max_tokens=1024)
        return ActionOutput(content=self._post(raw))

    # ---------------- 流式 ----------------

    async def run_stream(
        self,
        user_input: str,
        *,
        retrieved_memories: Optional[List[MemoryItem]] = None,
        retrieved_quotes: Optional[List[DialogueExample]] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncIterator[str]:
        system = self._build_system(retrieved_memories or [], retrieved_quotes or [])
        messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_input})
        async for chunk in self.llm.achat_stream(messages, temperature=0.75, max_tokens=1024):
            yield chunk

    # ---------------- prompt 构造 ----------------

    def _build_system(
        self,
        memories: List[MemoryItem],
        quotes: List[DialogueExample],
    ) -> str:
        p = self.profile
        scene_block = self._format_memories(memories, kinds=["scene"], max_n=3)
        motivation_block = self._format_memories(memories, kinds=["motivation"], max_n=3)
        event_block = self._format_memories(
            memories,
            kinds=["event", "personality_desc", "relationship", "emotion"],
            max_n=8,
        )
        dialogue_sample_block = self._format_dialogue_samples(memories, max_n=4)

        evidence_top_n = 50
        evidence_block = self._format_evidence(quotes, top_n=evidence_top_n)

        return CHAT_SYSTEM_TEMPLATE.format(
            name=p.name or "（未命名）",
            book=p.book_title or "（书名未知）",
            aliases=", ".join(p.aliases) if p.aliases else "（无）",
            profile_desc=p.profile or "原著中的重要角色",
            personality="，".join(p.personality_traits[:10]) or "（资料不足）",
            emotional_states="，".join(p.emotional_states[:8]) or "（资料不足）",
            speech_style="，".join(p.speech_style[:8]) or "（资料不足）",
            motivations="；".join(p.key_motivations[:6]) or "（资料不足）",
            relationships=self._format_relationships(p.relationships[:8]),
            world_block=self._format_world_block(),
            scene_block=scene_block,
            motivation_block=motivation_block,
            event_block=event_block,
            dialogue_sample_block=dialogue_sample_block,
            quote_top_n=evidence_top_n,
            evidence_block=evidence_block,
        )

    # ---------------- helper ----------------

    def _format_world_block(self) -> str:
        w = self.world
        parts: List[str] = []
        if w.genre:
            parts.append(f"- 题材：{w.genre}")
        if w.power_system_name or w.power_system_desc:
            ps = w.power_system_desc or w.power_system_name
            parts.append(f"- 力量/技艺体系：{ps}")
        if w.power_levels:
            parts.append(f"- 等级阶梯：{'→'.join(w.power_levels)}")
        if w.world_background:
            parts.append(f"- 世界背景：{w.world_background}")
        return "\n".join(parts) if parts else "（暂无额外世界观信息）"

    @staticmethod
    def _format_relationships(rels: List[Relationship]) -> str:
        if not rels:
            return "（无）"
        lines: List[str] = []
        for r in rels:
            line = f"- {r.name}（{r.relation or '未注明关系'}）"
            extras: List[str] = []
            if r.attitude:
                extras.append(f"态度：{r.attitude[:50]}")
            if r.interaction:
                snippet = r.interaction[:80] + ("…" if len(r.interaction) > 80 else "")
                extras.append(snippet)
            if extras:
                line += " | " + " ｜ ".join(extras)
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def _format_memories(items: List[MemoryItem], *, kinds: List[str], max_n: int) -> str:
        chosen = [m for m in items if m.memory_type in kinds][:max_n]
        if not chosen:
            return "（无）"
        out: List[str] = []
        for i, m in enumerate(chosen, 1):
            chap = f"第{m.chapter_order}章" if m.chapter_order else ""
            content = m.content.strip()
            if len(content) > 200:
                content = content[:200] + "…"
            out.append(f"{i}. [{chap}] {content}")
        return "\n".join(out)

    @staticmethod
    def _format_dialogue_samples(items: List[MemoryItem], *, max_n: int) -> str:
        chosen = [m for m in items if m.memory_type == "dialogue_sample"][:max_n]
        if not chosen:
            return "（无）"
        out: List[str] = []
        for i, m in enumerate(chosen, 1):
            content = re.sub(r"[（(].*?[）)]", "", m.content).strip()
            if len(content) > 160:
                content = content[:160] + "…"
            out.append(f"{i}. {content}")
        return "\n".join(out)

    @staticmethod
    def _format_evidence(items: List[DialogueExample], *, top_n: int) -> str:
        cleaned: List[str] = []
        for q in items[:top_n]:
            t = re.sub(r"[（(].*?[）)]", "", q.content)
            t = re.sub(r"[\[【].*?[\]】]", "", t)
            t = " ".join(t.split()).strip()
            if t:
                cleaned.append(t)
        if not cleaned:
            return "（无）"
        return "\n".join(f"{i+1}. {t}" for i, t in enumerate(cleaned))

    @staticmethod
    def _post(text: str) -> str:
        if not text:
            return text
        out = re.sub(r"[（(].*?[）)]", "", text)
        out = re.sub(r"[\[【].*?[\]】]", "", out)
        out = re.sub(r"[{｛].*?[}｝]", "", out)
        return " ".join(out.split()).strip()
