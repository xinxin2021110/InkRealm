"""角色聊天引擎封装 — 包装 novel_character_agent.NovelCharacter

为每个 character_id 维护内存级缓存,避免重复加载和重复构建 embedding。
"""
from __future__ import annotations

from threading import Lock
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

# 父包 __init__.py 已在 import 时把仓库根注入 sys.path
# ★ 直接 import 业务包顶层（MetaGPT 风格的 CharacterRole 也可平替）
from novel_character_agent import NovelCharacter

from ..models import Character, Novel
from . import novel_service


_engines: Dict[int, NovelCharacter] = {}
_engines_lock = Lock()


def get_engine(db: Session, character_id: int) -> NovelCharacter:
    """获取或创建一个 NovelCharacter 引擎实例"""
    with _engines_lock:
        if character_id in _engines:
            return _engines[character_id]

        ch = db.get(Character, character_id)
        if ch is None:
            raise LookupError("角色不存在")
        novel = db.get(Novel, ch.novel_id)
        if novel is None:
            raise LookupError("所属小说不存在")

        engine = NovelCharacter.from_data_file(
            data_file=novel.data_file,
            target_character=ch.name,
        )
        _engines[character_id] = engine
        return engine


def reset_engine(character_id: int) -> None:
    with _engines_lock:
        _engines.pop(character_id, None)


def build_character_detail(
    db: Session, character_id: int
) -> Optional[dict]:
    """构造角色详情字典(给 schemas.CharacterDetail 用)"""
    ch = db.get(Character, character_id)
    if ch is None:
        return None
    novel = db.get(Novel, ch.novel_id)

    engine = get_engine(db, character_id)
    profile = engine.profile

    relationships = [
        {
            "name": r.name,
            "relation": r.relation,
            "interaction": r.interaction[:200],
            "attitude": r.attitude,
        }
        for r in profile.relationships[:30]
    ]

    sample_quotes: List[str] = []
    for q in profile.dialogue_examples[:30]:
        if 5 <= len(q.content) <= 80:
            sample_quotes.append(q.content)
        if len(sample_quotes) >= 10:
            break

    return {
        "id": ch.id,
        "novel_id": ch.novel_id,
        "name": ch.name,
        "aliases": novel_service.parse_aliases(ch),
        "is_protagonist": ch.is_protagonist,
        "profile_summary": ch.profile_summary,
        "avatar_emoji": ch.avatar_emoji,
        "memory_count": len(profile.memories),
        "quote_count": len(profile.dialogue_examples),
        "analyzed": True,
        "book_title": novel.title if novel else "",
        "personality_traits": profile.personality_traits[:30],
        "speech_style": profile.speech_style[:20],
        "emotional_states": profile.emotional_states[:20],
        "key_motivations": profile.key_motivations[:15],
        "relationships": relationships,
        "sample_quotes": sample_quotes,
    }
