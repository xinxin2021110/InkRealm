"""检索器 —— 多通道、多 hop、分层、时序加权的"叙事记忆检索"。

打分公式（每条候选）：
    score = w_emb * cosine
          + w_bm25 * bm25_norm
          + w_jacc * jaccard
          + w_ent  * entity_hit
          + w_emo  * emotion_match
          + w_recency * recency
          + w_static * static_weight   (来自 mention_count + confidence)

各权重默认值见 ScoreWeights；可在构造器覆盖。

返回顺序：score 降序；同时通过"分层取 k"避免单一 type 霸榜。
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from ..logs import logger
from ..schema import (
    CharacterProfile,
    DialogueExample,
    MemoryItem,
    MemoryType,
)
from .embedder import BM25Scorer, Embedder, KeywordMatcher, TfidfEmbedder
from .entity_index import EntityIndex


# ---------------- 评分配置 ----------------

@dataclass
class ScoreWeights:
    """各通道权重。可按场景调（聊天/写章/选项）。"""

    embed: float = 0.45
    bm25: float = 0.15
    jaccard: float = 0.10
    entity: float = 0.18
    emotion: float = 0.06
    recency: float = 0.03
    static_weight: float = 0.10  # mention_count + confidence


# ---------------- 通用情感词典 ----------------

_EMOTION_LEX: Dict[str, List[str]] = {
    "喜悦": ["笑", "乐", "高兴", "开心", "哈哈", "愉快", "满意", "喜欢"],
    "悲伤": ["哭", "泪", "伤心", "难过", "悲伤", "痛苦", "失落"],
    "愤怒": ["怒", "怒火", "可恶", "混蛋", "讨厌", "气", "愤怒"],
    "关切": ["关心", "担心", "怎么样", "还好吗", "注意", "保重"],
    "感激": ["谢谢", "多谢", "感激", "感动"],
    "尴尬": ["尴尬", "不好意思", "难为情"],
}


def detect_emotion(query: str) -> str:
    if not query:
        return "中性"
    score: Dict[str, int] = defaultdict(int)
    for e, kws in _EMOTION_LEX.items():
        for k in kws:
            if k in query:
                score[e] += 1
    return max(score, key=score.get) if score else "中性"


# ---------------- MemoryRetriever ----------------

class MemoryRetriever:
    """对 CharacterProfile.memories 做"多通道融合 + 分层 + 时序"检索。"""

    def __init__(
        self,
        profile: CharacterProfile,
        embedder: Optional[Embedder] = None,
        weights: Optional[ScoreWeights] = None,
    ) -> None:
        self.profile = profile
        self.weights = weights or ScoreWeights()
        self.embedder = embedder or TfidfEmbedder()
        self.bm25 = BM25Scorer()
        self.keyword = KeywordMatcher()
        self.entity = EntityIndex()

        self.memories: List[MemoryItem] = list(profile.memories)
        if not self.memories:
            self._memo_vecs: List[List[float]] = []
            self._max_chap_order: int = 1
            return

        # 拟合
        texts = [m.content for m in self.memories]
        self.embedder.fit(texts)
        self.bm25.fit(texts)
        self._memo_vecs = self.embedder.embed_many(texts)

        # 实体池：所有关系人名 + 别名
        self.entity.add_entities([r.name for r in profile.relationships if r.name])
        self.entity.add_entities(profile.aliases)
        # 索引：优先用记忆自己声明的 related_people（精准），缺则文本扫描
        for i, m in enumerate(self.memories):
            if m.related_people:
                self.entity.index_explicit(i, m.related_people)
            else:
                self.entity.index(i, m.content)

        self._max_chap_order = max((m.chapter_order for m in self.memories), default=1) or 1

    # ---------------- 主检索（带分层）----------------

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        memory_type: Optional[str] = None,
        layered: bool = True,
    ) -> List[MemoryItem]:
        if not self.memories:
            return []
        q_emo = detect_emotion(query)
        q_entities = self.entity.find_entities_in(query)

        # 候选池
        if memory_type:
            cand_idx = [i for i, m in enumerate(self.memories) if m.memory_type == memory_type]
        else:
            cand_idx = list(range(len(self.memories)))
        if not cand_idx:
            return []

        # 计算每条得分
        bm25_all = self.bm25.score_all(query)
        bm25_max = max(bm25_all) if bm25_all else 1.0
        qv = self.embedder.embed(query)

        scored: List[Tuple[int, float]] = []
        for i in cand_idx:
            m = self.memories[i]
            cos = self.embedder.cosine(qv, self._memo_vecs[i])
            bm = (bm25_all[i] / bm25_max) if bm25_max > 0 else 0.0
            jac = self.keyword.jaccard(query, m.content)
            ent_hit = (
                1.0
                if q_entities and any(e in (m.related_people or []) for e in q_entities)
                else (0.5 if any(e in m.content for e in q_entities) else 0.0)
            )
            emo = 1.0 if (q_emo and m.emotion and q_emo == m.emotion) else 0.0
            rec = (m.chapter_order / self._max_chap_order) if self._max_chap_order else 0.0
            static = max(0.0, min(1.0, m.weight))

            w = self.weights
            s = (
                w.embed * cos
                + w.bm25 * bm
                + w.jaccard * jac
                + w.entity * ent_hit
                + w.emotion * emo
                + w.recency * rec
                + w.static_weight * static
            )
            scored.append((i, s))
        scored.sort(key=lambda x: x[1], reverse=True)

        if not layered:
            return [self.memories[i] for i, _ in scored[:top_k]]

        # 分层取 k：在 SCENE / EVENT / DIALOGUE_SAMPLE / RELATIONSHIP 等之间平衡
        return self._layered_pick(scored, top_k)

    # ---------------- 多 hop ----------------

    def retrieve_with_hops(self, query: str, top_k: int = 10) -> List[MemoryItem]:
        """先精确人名命中 → 再做 embedding 二次过滤。"""
        if not self.memories:
            return []
        q_entities = self.entity.find_entities_in(query)
        if not q_entities:
            return self.retrieve(query, top_k=top_k)

        first_hop = set(self.entity.docs_for_entities(q_entities))
        if not first_hop:
            return self.retrieve(query, top_k=top_k)

        # 在 first_hop 子集上跑一遍打分
        qv = self.embedder.embed(query)
        bm25_all = self.bm25.score_all(query)
        bm25_max = max(bm25_all) if bm25_all else 1.0
        q_emo = detect_emotion(query)

        scored: List[Tuple[int, float]] = []
        for i in first_hop:
            m = self.memories[i]
            cos = self.embedder.cosine(qv, self._memo_vecs[i])
            bm = (bm25_all[i] / bm25_max) if bm25_max > 0 else 0.0
            jac = self.keyword.jaccard(query, m.content)
            emo = 1.0 if (q_emo and m.emotion and q_emo == m.emotion) else 0.0
            rec = (m.chapter_order / self._max_chap_order) if self._max_chap_order else 0.0
            static = max(0.0, min(1.0, m.weight))

            w = self.weights
            s = (
                (w.embed + 0.10) * cos      # 精确命中后 embedding 权重略提
                + w.bm25 * bm
                + w.jaccard * jac
                + 0.20                      # entity-hit 已显式
                + w.emotion * emo
                + w.recency * rec
                + w.static_weight * static
            )
            scored.append((i, s))
        scored.sort(key=lambda x: x[1], reverse=True)
        return self._layered_pick(scored, top_k)

    # ---------------- 分层 ----------------

    @staticmethod
    def _layered_pick(scored: List[Tuple[int, float]], top_k: int) -> List[MemoryItem]:
        """按 memory_type 分层从 scored 列表里采样，避免 SCENE/EVENT 任一霸榜。

        策略：
        - 把候选按 type 分桶
        - round-robin 取，每桶最多 ⌈top_k/桶数⌉
        - 不足时再用全局 top 补齐
        """
        # 这里 scored 是 (idx, score)，但我们要按 type 分；通过 closure 传入 memory list 不优雅，
        # 这里依赖外层 memories 不可用 → 改成静态方法时退化。我们在 retrieve 里直接做 layered。
        # 实际：因为 _memories 是外部状态，这里返回 scored 的 top_k 即可，分层逻辑放回到外面。
        raise NotImplementedError

    # ↑ 上面静态方法被改写成下面的实例方法（更优雅）
    # 但为不破坏接口，重新实现 _layered_pick 为实例方法：
    def _layered_pick(self, scored, top_k):  # type: ignore[override]
        buckets: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
        for i, s in scored:
            buckets[self.memories[i].memory_type].append((i, s))
        # 每桶按分降序
        for k in buckets:
            buckets[k].sort(key=lambda x: x[1], reverse=True)
        # 期望分布（可调）
        order = [
            MemoryType.SCENE.value,
            MemoryType.EVENT.value,
            MemoryType.MOTIVATION.value,
            MemoryType.RELATIONSHIP.value,
            MemoryType.DIALOGUE_SAMPLE.value,
            MemoryType.PERSONALITY_DESC.value,
            MemoryType.EMOTION.value,
            MemoryType.DIALOGUE.value,
            MemoryType.PERSONALITY.value,
        ]
        per_bucket = max(1, (top_k + len(order) - 1) // max(1, sum(1 for k in order if buckets.get(k))))
        chosen_idx: List[int] = []
        chosen_set: set = set()

        # round 1：按 order 取每桶头部
        for k in order:
            for i, _s in buckets.get(k, [])[:per_bucket]:
                if i not in chosen_set:
                    chosen_idx.append(i)
                    chosen_set.add(i)
                if len(chosen_idx) >= top_k:
                    return [self.memories[i] for i in chosen_idx]

        # round 2：用全局 top 补齐
        for i, _s in scored:
            if len(chosen_idx) >= top_k:
                break
            if i not in chosen_set:
                chosen_idx.append(i)
                chosen_set.add(i)
        return [self.memories[i] for i in chosen_idx[:top_k]]


# ---------------- QuoteRetriever ----------------

class QuoteRetriever:
    """语录检索：保证 ≥min_quotes，并融合实体 + 情感 + evidence 优先 + 时序加权。"""

    def __init__(
        self,
        profile: CharacterProfile,
        embedder: Optional[Embedder] = None,
    ) -> None:
        self.profile = profile
        self.quotes: List[DialogueExample] = list(profile.dialogue_examples)
        self.embedder = embedder or TfidfEmbedder()
        self.bm25 = BM25Scorer()
        self.keyword = KeywordMatcher()
        self.entity = EntityIndex()

        self._emotion_index: Dict[str, List[int]] = defaultdict(list)
        for i, q in enumerate(self.quotes):
            self._emotion_index[(q.emotion or "中性")].append(i)

        if self.quotes:
            texts = [q.content for q in self.quotes]
            self.embedder.fit(texts)
            self.bm25.fit(texts)
            self._vecs = self.embedder.embed_many(texts)
            self._max_chap_order = max((q.chapter_order for q in self.quotes), default=1) or 1
        else:
            self._vecs = []
            self._max_chap_order = 1

        # 实体池
        self.entity.add_entities([r.name for r in profile.relationships if r.name])
        self.entity.add_entities(profile.aliases)
        for i, q in enumerate(self.quotes):
            if q.related_people:
                self.entity.index_explicit(i, q.related_people)
            else:
                self.entity.index(i, q.content)

    def detect_emotion(self, query: str) -> str:
        return detect_emotion(query)

    def retrieve(
        self,
        query: str,
        min_quotes: int = 100,
    ) -> List[DialogueExample]:
        if not self.quotes:
            return []
        emo = detect_emotion(query)
        q_entities = self.entity.find_entities_in(query)
        qv = self.embedder.embed(query)
        bm25_all = self.bm25.score_all(query)
        bm25_max = max(bm25_all) if bm25_all else 1.0

        scored: List[Tuple[int, float]] = []
        for i, q in enumerate(self.quotes):
            cos = self.embedder.cosine(qv, self._vecs[i])
            bm = (bm25_all[i] / bm25_max) if bm25_max > 0 else 0.0
            jac = self.keyword.jaccard(query, q.content)
            ent_hit = (
                1.0
                if q_entities and any(e in (q.related_people or []) for e in q_entities)
                else (0.5 if any(e in q.content for e in q_entities) else 0.0)
            )
            emo_match = 1.0 if (q.emotion and q.emotion == emo) else 0.0
            rec = (q.chapter_order / self._max_chap_order) if self._max_chap_order else 0.0
            evidence_boost = 0.10 if q.is_evidence else 0.0
            confidence = max(0.5, min(1.0, q.confidence))

            s = (
                0.40 * cos
                + 0.15 * bm
                + 0.10 * jac
                + 0.18 * ent_hit
                + 0.10 * emo_match
                + 0.04 * rec
                + evidence_boost
            ) * confidence
            scored.append((i, s))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [self.quotes[i] for i, _ in scored[:min_quotes]]

        # 不足时补：同情感 → 全量
        if len(top) < min_quotes:
            seen = {q.content for q in top}
            for i in self._emotion_index.get(emo, []):
                if self.quotes[i].content not in seen:
                    top.append(self.quotes[i])
                    seen.add(self.quotes[i].content)
                    if len(top) >= min_quotes:
                        break
        if len(top) < min_quotes:
            seen = {q.content for q in top}
            for q in self.quotes:
                if q.content not in seen:
                    top.append(q)
                    seen.add(q.content)
                    if len(top) >= min_quotes:
                        break
        return top[:min_quotes]
