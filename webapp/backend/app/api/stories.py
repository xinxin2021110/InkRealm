"""故事共创 API"""
from __future__ import annotations

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    ChapterOut,
    ChooseOptionIn,
    CreateStoryIn,
    GenerateChapterOut,
    PersonaOptionsOut,
    StoryBrief,
    StoryDetail,
)
from ..services import story_service


router = APIRouter(prefix="/api/v1/stories", tags=["stories"])


@router.get("/persona-options/{novel_id}/{character_id}", response_model=PersonaOptionsOut)
async def persona_options(
    novel_id: int, character_id: int, db: Session = Depends(get_db)
):
    try:
        dims = await story_service.get_persona_dimensions(db, novel_id, character_id)
    except LookupError as e:
        raise HTTPException(404, str(e))
    return PersonaOptionsOut.model_validate(dims)


@router.post("", response_model=StoryDetail, status_code=201)
async def create_story(payload: CreateStoryIn, db: Session = Depends(get_db)):
    try:
        story = await story_service.create_story(
            db,
            novel_id=payload.novel_id,
            character_id=payload.character_id,
            user_name=payload.user_name,
            selections=payload.selections.model_dump(),
            total_chapters=payload.total_chapters,
        )
    except LookupError as e:
        raise HTTPException(404, str(e))
    detail = story_service.get_story_detail(db, story.id)
    return StoryDetail.model_validate(detail)


@router.get("", response_model=List[StoryBrief])
def list_stories(db: Session = Depends(get_db)):
    return [StoryBrief.model_validate(s) for s in story_service.list_stories(db)]


@router.get("/{story_id}", response_model=StoryDetail)
def get_story(story_id: int, db: Session = Depends(get_db)):
    detail = story_service.get_story_detail(db, story_id)
    if not detail:
        raise HTTPException(404, "故事不存在")
    return StoryDetail.model_validate(detail)


@router.delete("/{story_id}")
def delete_story(story_id: int, db: Session = Depends(get_db)):
    if not story_service.delete_story(db, story_id):
        raise HTTPException(404, "故事不存在")
    return {"ok": True}


@router.post(
    "/{story_id}/chapters/{chapter_number}/choose",
    response_model=GenerateChapterOut,
)
async def choose_option(
    story_id: int,
    chapter_number: int,
    payload: ChooseOptionIn,
    db: Session = Depends(get_db),
):
    next_chap = await story_service.choose_and_generate_next(
        db, story_id, chapter_number, payload.option_id
    )
    detail = story_service.get_story_detail(db, story_id)
    if next_chap is None:
        # 已是最后一章 — 返回当前章信息(已结束)
        if not detail:
            raise HTTPException(404, "故事不存在")
        last_chapter_data = detail["chapters"][-1] if detail["chapters"] else None
        if not last_chapter_data:
            raise HTTPException(404, "章节不存在")
        return GenerateChapterOut(
            chapter=ChapterOut.model_validate(last_chapter_data),
            relationship_meter=detail["relationship_meter"],
            user_power_level=detail["user_power_level"],
        )

    new_chapter_data = next(
        (c for c in detail["chapters"] if c["chapter_number"] == next_chap.chapter_number),
        None,
    )
    return GenerateChapterOut(
        chapter=ChapterOut.model_validate(new_chapter_data),
        relationship_meter=detail["relationship_meter"],
        user_power_level=detail["user_power_level"],
    )


@router.post(
    "/{story_id}/chapters/{chapter_number}/regenerate",
    response_model=ChapterOut,
)
async def regenerate_chapter(
    story_id: int, chapter_number: int, db: Session = Depends(get_db)
):
    new_chapter = await story_service.regenerate_chapter(db, story_id, chapter_number)
    if new_chapter is None:
        raise HTTPException(404, "章节不存在")
    detail = story_service.get_story_detail(db, story_id)
    chap_data = next(
        (c for c in detail["chapters"] if c["chapter_number"] == new_chapter.chapter_number),
        None,
    )
    return ChapterOut.model_validate(chap_data)


@router.get("/{story_id}/export")
def export_story(story_id: int, db: Session = Depends(get_db)):
    path = story_service.export_story_text(db, story_id)
    if path is None:
        raise HTTPException(404, "故事不存在")
    return FileResponse(
        str(path),
        media_type="text/plain; charset=utf-8",
        filename=path.name,
    )
