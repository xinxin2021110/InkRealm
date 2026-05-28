"""聊天 API"""
from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    ChatMessageOut,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionOut,
    SendMessageIn,
    SendMessageOut,
)
from ..services import chat_service


router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.get("/sessions", response_model=List[ChatSessionOut])
def list_sessions(db: Session = Depends(get_db)):
    return [ChatSessionOut.model_validate(s) for s in chat_service.list_sessions(db)]


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
def create_session(payload: ChatSessionCreate, db: Session = Depends(get_db)):
    try:
        s = chat_service.create_session(
            db,
            novel_id=payload.novel_id,
            character_id=payload.character_id,
            user_name=payload.user_name,
        )
    except LookupError as e:
        raise HTTPException(404, str(e))
    detail = chat_service.get_session_with_messages(db, s.id)
    return ChatSessionOut.model_validate(detail)


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_session(session_id: int, db: Session = Depends(get_db)):
    detail = chat_service.get_session_with_messages(db, session_id)
    if not detail:
        raise HTTPException(404, "会话不存在")
    return ChatSessionDetail.model_validate(detail)


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    if not chat_service.delete_session(db, session_id):
        raise HTTPException(404, "会话不存在")
    return {"ok": True}


@router.post("/sessions/{session_id}/messages", response_model=SendMessageOut)
async def send_message(
    session_id: int,
    payload: SendMessageIn,
    db: Session = Depends(get_db),
):
    try:
        result = await chat_service.send_message(db, session_id, payload.content)
    except RuntimeError as e:
        raise HTTPException(502, f"角色生成失败: {e}")
    if result is None:
        raise HTTPException(404, "会话不存在")
    return SendMessageOut.model_validate(result)


@router.post("/sessions/{session_id}/messages/stream")
async def send_message_stream(
    session_id: int,
    payload: SendMessageIn,
    db: Session = Depends(get_db),
):
    """SSE 流式聊天接口。
    协议（每个事件以 `data: <json>\\n\\n` 形式输出）：
      - type=user_message
      - type=chunk  delta=...
      - type=done   character_message=...
      - type=error  message=...
    """
    try:
        stream = await chat_service.send_message_stream(db, session_id, payload.content)
    except Exception as e:
        raise HTTPException(502, f"启动流失败: {e}")
    if stream is None:
        raise HTTPException(404, "会话不存在")

    async def event_source():
        try:
            async for event in stream:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            err = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions/{session_id}/export", response_class=PlainTextResponse)
def export_session(session_id: int, db: Session = Depends(get_db)):
    text = chat_service.export_session_text(db, session_id)
    if text is None:
        raise HTTPException(404, "会话不存在")
    return PlainTextResponse(
        text,
        headers={
            "Content-Disposition": f'attachment; filename="chat_{session_id}.txt"'
        },
    )
