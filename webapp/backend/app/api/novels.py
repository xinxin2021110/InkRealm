"""小说 / 角色 API"""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import MAX_UPLOAD_SIZE
from ..database import get_db
from ..schemas import (
    CharacterBrief,
    CharacterDetail,
    NovelDetail,
    NovelOut,
)
from ..services import character_service, novel_service


router = APIRouter(prefix="/api/v1", tags=["novels"])


def _to_brief(c) -> CharacterBrief:
    return CharacterBrief(
        id=c.id,
        novel_id=c.novel_id,
        name=c.name,
        aliases=novel_service.parse_aliases(c),
        is_protagonist=c.is_protagonist,
        profile_summary=c.profile_summary,
        avatar_emoji=c.avatar_emoji,
        memory_count=c.memory_count,
        quote_count=c.quote_count,
        analyzed=c.analyzed,
    )


@router.get("/novels", response_model=List[NovelOut])
def list_novels(db: Session = Depends(get_db)):
    novels = novel_service.list_novels(db)
    out = []
    for n in novels:
        out.append(
            NovelOut.model_validate(
                {
                    "id": n.id,
                    "title": n.title,
                    "author": n.author or "",
                    "cover_emoji": n.cover_emoji,
                    "description": n.description,
                    "characters_count": len(n.characters),
                    "created_at": n.created_at,
                }
            )
        )
    return out


@router.get("/novels/{novel_id}", response_model=NovelDetail)
def get_novel(novel_id: int, db: Session = Depends(get_db)):
    n = novel_service.get_novel(db, novel_id)
    if not n:
        raise HTTPException(404, "小说不存在")
    return NovelDetail(
        id=n.id,
        title=n.title,
        author=n.author or "",
        cover_emoji=n.cover_emoji,
        description=n.description,
        characters_count=len(n.characters),
        created_at=n.created_at,
        characters=[_to_brief(c) for c in n.characters],
    )


@router.get("/novels/{novel_id}/characters", response_model=List[CharacterBrief])
def list_characters(novel_id: int, db: Session = Depends(get_db)):
    n = novel_service.get_novel(db, novel_id)
    if not n:
        raise HTTPException(404, "小说不存在")
    return [_to_brief(c) for c in novel_service.list_characters(db, novel_id)]


@router.post("/novels", response_model=NovelDetail, status_code=201)
async def upload_novel(
    file: UploadFile = File(...),
    title: str = Form(""),
    author: str = Form(""),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".jsonl"):
        raise HTTPException(400, "仅支持 .jsonl 文件")

    # 读取并校验大小
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(400, f"文件大小超过 {MAX_UPLOAD_SIZE // (1024*1024)} MB")

    tmp_dir = tempfile.mkdtemp()
    try:
        tmp_path = Path(tmp_dir) / "upload.jsonl"
        tmp_path.write_bytes(contents)
        try:
            n = novel_service.create_novel_from_file(
                db,
                tmp_path,
                title=title or None,
                author=author or "",
                description=description or "",
            )
        except ValueError as e:
            raise HTTPException(400, str(e))
        return NovelDetail(
            id=n.id,
            title=n.title,
            author=n.author or "",
            cover_emoji=n.cover_emoji,
            description=n.description,
            characters_count=len(n.characters),
            created_at=n.created_at,
            characters=[_to_brief(c) for c in n.characters],
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.delete("/novels/{novel_id}")
def delete_novel(novel_id: int, db: Session = Depends(get_db)):
    if not novel_service.delete_novel(db, novel_id):
        raise HTTPException(404, "小说不存在")
    return {"ok": True}


@router.get("/characters/{character_id}", response_model=CharacterDetail)
def get_character_detail(character_id: int, db: Session = Depends(get_db)):
    detail = character_service.build_character_detail(db, character_id)
    if not detail:
        raise HTTPException(404, "角色不存在")
    return CharacterDetail.model_validate(detail)
