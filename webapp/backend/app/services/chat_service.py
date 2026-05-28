"""聊天会话业务逻辑"""
from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Character, ChatMessage, ChatSession, Novel
from . import character_service


def list_sessions(db: Session, limit: int = 30) -> List[dict]:
    """返回会话列表(含角色名/小说名/最后消息预览)"""
    sessions = list(
        db.scalars(
            select(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit)
        )
    )

    out: List[dict] = []
    for s in sessions:
        ch = db.get(Character, s.character_id)
        nv = db.get(Novel, s.novel_id)
        last_msg = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == s.id)
            .order_by(ChatMessage.id.desc())
            .first()
        )
        out.append(
            {
                "id": s.id,
                "novel_id": s.novel_id,
                "character_id": s.character_id,
                "character_name": ch.name if ch else "",
                "novel_title": nv.title if nv else "",
                "user_name": s.user_name,
                "title": s.title,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": db.query(ChatMessage)
                .filter(ChatMessage.session_id == s.id)
                .count(),
                "last_message_preview": (last_msg.content[:60] + "…") if last_msg and len(last_msg.content) > 60 else (last_msg.content if last_msg else ""),
            }
        )
    return out


def get_session_with_messages(db: Session, session_id: int) -> Optional[dict]:
    s = db.get(ChatSession, session_id)
    if not s:
        return None
    ch = db.get(Character, s.character_id)
    nv = db.get(Novel, s.novel_id)
    return {
        "id": s.id,
        "novel_id": s.novel_id,
        "character_id": s.character_id,
        "character_name": ch.name if ch else "",
        "novel_title": nv.title if nv else "",
        "user_name": s.user_name,
        "title": s.title,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
        "message_count": len(s.messages),
        "last_message_preview": (s.messages[-1].content[:60] if s.messages else ""),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "retrieved_memories": m.retrieved_memories,
                "retrieved_quotes": m.retrieved_quotes,
                "created_at": m.created_at,
            }
            for m in s.messages
        ],
    }


def create_session(
    db: Session,
    novel_id: int,
    character_id: int,
    user_name: str = "少侠",
) -> ChatSession:
    novel = db.get(Novel, novel_id)
    ch = db.get(Character, character_id)
    if not novel or not ch:
        raise LookupError("小说或角色不存在")

    s = ChatSession(
        novel_id=novel_id,
        character_id=character_id,
        user_name=user_name or "少侠",
        title=f"与「{ch.name}」的墨笺对谈",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def delete_session(db: Session, session_id: int) -> bool:
    s = db.get(ChatSession, session_id)
    if not s:
        return False
    db.delete(s)
    db.commit()
    return True


async def send_message(
    db: Session, session_id: int, content: str
) -> Optional[dict]:
    """发送一条用户消息,得到角色回复。"""
    s = db.get(ChatSession, session_id)
    if not s:
        return None

    engine = character_service.get_engine(db, s.character_id)

    # 用 engine 自带的对话历史(同一会话内引擎复用,但跨会话需要重置历史)
    # 这里采取保守做法:把数据库里现有的对话回灌到 engine,以避免越界。
    engine.clear_dialogue_history()
    for m in s.messages:
        if m.role == "user":
            engine.dialogue_history.add_user_message(m.content)
        else:
            engine.dialogue_history.add_assistant_message(m.content)

    # 调用引擎 (异步)
    reply_text = await engine.respond(content)

    # 取最后一次检索到的统计
    retrieved_memories = len(engine.memory_retrieve_action.get_retrieved_memories())
    retrieved_quotes = len(engine.quote_retrieve_action.get_retrieved_quotes())

    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=content,
    )
    char_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=reply_text,
        retrieved_memories=retrieved_memories,
        retrieved_quotes=retrieved_quotes,
    )
    db.add(user_msg)
    db.add(char_msg)
    s.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user_msg)
    db.refresh(char_msg)

    return {
        "user_message": {
            "id": user_msg.id,
            "role": user_msg.role,
            "content": user_msg.content,
            "retrieved_memories": 0,
            "retrieved_quotes": 0,
            "created_at": user_msg.created_at,
        },
        "character_message": {
            "id": char_msg.id,
            "role": char_msg.role,
            "content": char_msg.content,
            "retrieved_memories": char_msg.retrieved_memories,
            "retrieved_quotes": char_msg.retrieved_quotes,
            "created_at": char_msg.created_at,
        },
    }


async def send_message_stream(
    db: Session, session_id: int, content: str
) -> Optional[AsyncIterator[dict]]:
    """流式发送：yield 多个 dict 事件，最后一个事件 type=done 含完整消息 id。

    事件协议（每个 dict 一个 SSE event）：
    - {"type": "user_message", "message": {...}}   会话已落库的用户消息
    - {"type": "chunk", "delta": "..."}            一段角色回复 token
    - {"type": "done", "character_message": {...}} 角色消息已落库
    """
    s = db.get(ChatSession, session_id)
    if not s:
        return None

    engine = character_service.get_engine(db, s.character_id)

    # 把历史回灌到引擎，保持一致语境
    engine.clear_dialogue_history()
    for m in s.messages:
        if m.role == "user":
            engine.dialogue_history.add_user_message(m.content)
        else:
            engine.dialogue_history.add_assistant_message(m.content)

    # 先落库用户消息（这样前端能立刻拿到 id）
    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    async def _iter() -> AsyncIterator[dict]:
        yield {
            "type": "user_message",
            "message": {
                "id": user_msg.id,
                "role": "user",
                "content": user_msg.content,
                "retrieved_memories": 0,
                "retrieved_quotes": 0,
                "created_at": user_msg.created_at.isoformat(),
            },
        }
        chunks: List[str] = []
        async for chunk in engine.respond_stream(content):
            chunks.append(chunk)
            yield {"type": "chunk", "delta": chunk}

        # 取最后一次检索到的统计
        retrieved_memories = len(engine.memory_retrieve_action.get_retrieved_memories())
        retrieved_quotes = len(engine.quote_retrieve_action.get_retrieved_quotes())

        # 后处理 = 移除括号/动作描写
        import re
        final_text = re.sub(r"[（(].*?[）)]", "", "".join(chunks))
        final_text = re.sub(r"[\[【].*?[\]】]", "", final_text)
        final_text = " ".join(final_text.split()).strip()

        char_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=final_text,
            retrieved_memories=retrieved_memories,
            retrieved_quotes=retrieved_quotes,
        )
        db.add(char_msg)
        s.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(char_msg)

        yield {
            "type": "done",
            "character_message": {
                "id": char_msg.id,
                "role": "assistant",
                "content": char_msg.content,
                "retrieved_memories": char_msg.retrieved_memories,
                "retrieved_quotes": char_msg.retrieved_quotes,
                "created_at": char_msg.created_at.isoformat(),
            },
        }

    return _iter()


def export_session_text(db: Session, session_id: int) -> Optional[str]:
    s = db.get(ChatSession, session_id)
    if not s:
        return None
    ch = db.get(Character, s.character_id)
    nv = db.get(Novel, s.novel_id)

    lines = [
        f"# 墨笺对谈 - {ch.name if ch else '?'}",
        f"## 小说: 《{nv.title if nv else '?'}》",
        f"## 用户: {s.user_name}",
        f"## 时间: {s.created_at.strftime('%Y-%m-%d %H:%M')} → {s.updated_at.strftime('%Y-%m-%d %H:%M')}",
        "",
        "─" * 30,
        "",
    ]
    for m in s.messages:
        who = s.user_name if m.role == "user" else (ch.name if ch else "角色")
        lines.append(f"【{who}】{m.content}")
        lines.append("")
    return "\n".join(lines)
