"""Embedder —— 可插拔的文本向量化与轻量打分器。

包含：
- Embedder（抽象基类）
- TfidfEmbedder（字符级 unigram+bigram + IDF + hash 桶）
- BM25Scorer（更适合短语级匹配的稀疏打分器，作为 TF-IDF 的补强通道）
- KeywordMatcher（jaccard 风格关键词匹配）
"""
from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from typing import Dict, List, Sequence, Tuple


# ---------------- 公共分词 ----------------

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


_PUNCT_RE = re.compile(
    r"[、。，！？；：“”‘’\"'.,!?;:()（）【】\[\]<>《》—…/\\\-]"
)


def char_tokens(text: str, use_bigrams: bool = True) -> List[str]:
    text = _normalize(text)
    if not text:
        return []
    clean = _PUNCT_RE.sub(" ", text)
    tokens: List[str] = []
    for piece in clean.split():
        tokens.extend(list(piece))
        if use_bigrams:
            for i in range(len(piece) - 1):
                tokens.append(piece[i : i + 2])
    return tokens


# ---------------- Embedder ----------------

class Embedder(ABC):
    """Embedder 抽象基类。"""

    @abstractmethod
    def fit(self, docs: Sequence[str]) -> None: ...

    @abstractmethod
    def embed(self, text: str) -> List[float]: ...

    def embed_many(self, texts: Sequence[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]

    @staticmethod
    def cosine(v1: Sequence[float], v2: Sequence[float]) -> float:
        if len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        if n1 == 0 or n2 == 0:
            return 0.0
        return dot / (n1 * n2)


class TfidfEmbedder(Embedder):
    """字符级 TF-IDF（hash 桶）。"""

    def __init__(self, vector_size: int = 256, use_bigrams: bool = True) -> None:
        self.vector_size = vector_size
        self.use_bigrams = use_bigrams
        self.idf: Dict[str, float] = {}
        self._n_docs = 0

    def _hash(self, token: str) -> int:
        return int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.vector_size

    def fit(self, docs: Sequence[str]) -> None:
        self._n_docs = len(docs)
        df: Counter = Counter()
        for d in docs:
            for tok in set(char_tokens(d, self.use_bigrams)):
                df[tok] += 1
        self.idf = {
            tok: math.log((self._n_docs + 1) / (n + 1)) + 1.0 for tok, n in df.items()
        }

    def embed(self, text: str) -> List[float]:
        tokens = char_tokens(text, self.use_bigrams)
        if not tokens:
            return [0.0] * self.vector_size
        tf = Counter(tokens)
        total = sum(tf.values()) or 1
        vec = [0.0] * self.vector_size
        for tok, c in tf.items():
            idx = self._hash(tok)
            w = (c / total) * self.idf.get(tok, 1.0)
            vec[idx] += w
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec


# ---------------- BM25 ----------------

class BM25Scorer:
    """轻量 BM25 打分器。

    比 TF-IDF 更稳健地处理"短 query 在长文档中的命中"——这恰好是
    "用户问一句话 / 角色记忆几十字"的常见情况。
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75, use_bigrams: bool = True) -> None:
        self.k1 = k1
        self.b = b
        self.use_bigrams = use_bigrams
        self._idf: Dict[str, float] = {}
        self._doc_lens: List[int] = []
        self._avgdl: float = 0.0
        self._docs_tokens: List[Counter] = []
        self._n_docs: int = 0

    def fit(self, docs: Sequence[str]) -> None:
        self._docs_tokens = [Counter(char_tokens(d, self.use_bigrams)) for d in docs]
        self._doc_lens = [sum(c.values()) for c in self._docs_tokens]
        self._n_docs = len(docs) or 1
        self._avgdl = (sum(self._doc_lens) / self._n_docs) if self._doc_lens else 1.0

        df: Counter = Counter()
        for c in self._docs_tokens:
            for tok in c.keys():
                df[tok] += 1
        # BM25+ IDF（避免负值）
        self._idf = {
            t: math.log((self._n_docs - n + 0.5) / (n + 0.5) + 1.0)
            for t, n in df.items()
        }

    def score(self, query: str, doc_idx: int) -> float:
        if doc_idx >= len(self._docs_tokens):
            return 0.0
        q_tokens = set(char_tokens(query, self.use_bigrams))
        if not q_tokens:
            return 0.0
        c = self._docs_tokens[doc_idx]
        dl = self._doc_lens[doc_idx] or 1
        avgdl = self._avgdl or 1
        s = 0.0
        for t in q_tokens:
            if t not in c:
                continue
            tf = c[t]
            idf = self._idf.get(t, 0.0)
            denom = tf + self.k1 * (1 - self.b + self.b * (dl / avgdl))
            s += idf * (tf * (self.k1 + 1)) / max(denom, 1e-6)
        return s

    def score_all(self, query: str) -> List[float]:
        return [self.score(query, i) for i in range(len(self._docs_tokens))]


# ---------------- KeywordMatcher ----------------

class KeywordMatcher:
    """Jaccard 风格关键词匹配。"""

    _STOP = set(
        "的 了 在 是 我 有 和 就 不 人 都 一 上 也 很 到 说 要 去 你 会 着 自己 这 那 个 啊 呢 吧".split()
    )

    def extract(self, text: str) -> List[str]:
        text = text or ""
        clean = _PUNCT_RE.sub(" ", text)
        out: List[str] = []
        for piece in clean.split():
            for ch in piece:
                if ch and ch not in self._STOP:
                    out.append(ch)
            for i in range(len(piece) - 1):
                out.append(piece[i : i + 2])
        return list(set(out))

    def jaccard(self, q: str, d: str) -> float:
        qs, ds = set(self.extract(q)), set(self.extract(d))
        if not qs or not ds:
            return 0.0
        return len(qs & ds) / max(len(qs), 1)
