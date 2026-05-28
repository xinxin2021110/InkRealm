"""故事共创业务逻辑 — 包装 novel_story_agent"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

# 父包 __init__.py 已在 import 时把仓库根注入 sys.path
from novel_story_agent.data import NovelAnalyzer
from novel_story_agent.persona import UserPersonaBuilder
from novel_story_agent.generation import (
    ChapterWriter,
    ChoiceGenerator,
    OutlineGenerator,
)
from novel_story_agent.schema import (
    ChapterContent,
    ChapterOutline,
    NovelAnalysis,
    StoryOutline,
    UserPersona,
)

from ..config import CACHE_DIR, EXPORTS_DIR
from ..models import Character, Chapter, Novel, Story


_analysis_cache: Dict[int, NovelAnalysis] = {}
_dimensions_cache: Dict[int, Dict[str, Any]] = {}
_analysis_lock = Lock()


# ---------- 小说分析 (含世界观 / 风格 / 角色深度) ----------

def _cache_path(novel_id: int, character_id: int) -> Path:
    return CACHE_DIR / f"novel_{novel_id}_char_{character_id}.json"


async def get_or_build_analysis(
    db: Session, novel_id: int, character_id: int
) -> NovelAnalysis:
    """获取或构建小说分析(世界观/风格/角色)。带磁盘+内存缓存。"""
    cache_key = character_id
    with _analysis_lock:
        if cache_key in _analysis_cache:
            return _analysis_cache[cache_key]

    cf = _cache_path(novel_id, character_id)
    if cf.exists():
        try:
            data = json.loads(cf.read_text(encoding="utf-8"))
            analysis = NovelAnalysis.model_validate(data)
            # ★ 旧缓存可能没有新字段（如 genre/power_system_name），但 model_validate
            #   能正常工作；若字段命名彻底不兼容（如 cultivation_system → power_system_desc），
            #   旧缓存会读出空字段，触发 power_system 提示信息缺失。此时直接当作过期缓存。
            if not analysis.world_setting.world_background and not analysis.world_setting.power_system_desc:
                raise ValueError("旧缓存字段不兼容，重新分析")
            with _analysis_lock:
                _analysis_cache[cache_key] = analysis
            return analysis
        except Exception as e:
            print(f"[analysis] 读取缓存失败,将重新分析: {e}")

    novel = db.get(Novel, novel_id)
    ch = db.get(Character, character_id)
    if not novel or not ch:
        raise LookupError("小说或角色不存在")

    analyzer = NovelAnalyzer(novel.data_file)
    # NovelAnalyzer 默认从 jsonl 第一个角色构建。我们这里用全部数据,
    # 但要让 character_info 是当前角色 — 通过手动覆盖角色名(若与文件中第一个不同)
    analysis = await analyzer.analyze()
    if analysis.character_info.name != ch.name:
        # 简化处理:用文件第一个主角的分析当世界观,但 name 改成请求的角色名
        analysis.character_info.name = ch.name

    try:
        cf.write_text(
            json.dumps(analysis.model_dump(mode="json"), ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        print(f"[analysis] 写缓存失败: {e}")

    with _analysis_lock:
        _analysis_cache[cache_key] = analysis
    return analysis


# ---------- 人设维度 ----------

async def get_persona_dimensions(
    db: Session, novel_id: int, character_id: int
) -> Dict[str, Any]:
    if character_id in _dimensions_cache:
        return _dimensions_cache[character_id]

    analysis = await get_or_build_analysis(db, novel_id, character_id)
    builder = UserPersonaBuilder()
    dims = await builder.generate_persona_dimensions(
        analysis.world_setting, analysis.character_info
    )
    # 保险:确保结构齐全
    fallback = builder._get_default_dimensions(analysis.character_info.book_title)
    for key in ("background", "personality", "relationship", "ability"):
        if key not in dims:
            dims[key] = fallback[key]

    _dimensions_cache[character_id] = dims
    return dims


def _builder_with_cached_dims(dims: Dict[str, Any]) -> UserPersonaBuilder:
    """避免 build_persona 内部又调一次 generate_persona_dimensions(浪费 ~10 秒)"""
    builder = UserPersonaBuilder()

    async def _cached(*_args, **_kwargs):
        return dims

    builder.generate_persona_dimensions = _cached  # type: ignore[assignment]
    return builder


# ---------- 创建故事 (生成大纲 + 第一章) ----------

async def create_story(
    db: Session,
    novel_id: int,
    character_id: int,
    user_name: str,
    selections: Dict[str, str],
    total_chapters: int,
) -> Story:
    analysis = await get_or_build_analysis(db, novel_id, character_id)
    dims = await get_persona_dimensions(db, novel_id, character_id)

    builder = _builder_with_cached_dims(dims)
    persona = await builder.build_persona(
        user_name=user_name,
        selections=selections,
        world_setting=analysis.world_setting,
        character_info=analysis.character_info,
    )

    outline_gen = OutlineGenerator()
    outline = await outline_gen.generate_outline(
        user_persona=persona,
        world_setting=analysis.world_setting,
        character_info=analysis.character_info,
        total_chapters=total_chapters,
    )

    novel = db.get(Novel, novel_id)
    ch = db.get(Character, character_id)

    story = Story(
        novel_id=novel_id,
        character_id=character_id,
        title=outline.title or f"与{ch.name}的故事",
        theme=outline.theme,
        user_persona_name=user_name,
        user_persona_json=persona.model_dump_json(),
        outline_json=outline.model_dump_json(),
        total_chapters=total_chapters,
        current_chapter=0,
        relationship_meter_json=json.dumps({ch.name: 10}, ensure_ascii=False),
        user_power_level="淬体第一重",
        flags_json="{}",
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    # 立刻生成第 1 章 + 选项
    await _write_chapter(db, story, analysis, persona, outline, chapter_index=0)
    return story


# ---------- 章节写作 ----------

async def _write_chapter(
    db: Session,
    story: Story,
    analysis: NovelAnalysis,
    persona: UserPersona,
    outline: StoryOutline,
    chapter_index: int,
) -> Chapter:
    if chapter_index >= len(outline.chapters):
        raise ValueError("章节超出大纲范围")
    chapter_outline = outline.chapters[chapter_index]
    chapter_outline.chapter_number = chapter_index + 1  # 强制对齐

    previous_chapters: List[ChapterContent] = []
    for c in story.chapters:
        previous_chapters.append(
            ChapterContent(
                chapter_number=c.chapter_number,
                title=c.title,
                content=c.content,
                summary=c.summary,
                key_events=json.loads(c.key_events_json or "[]"),
                characters_present=[],
            )
        )

    relationship_state = json.loads(story.relationship_meter_json or "{}")
    flags = json.loads(story.flags_json or "{}")

    writer = ChapterWriter()
    chapter_content = await writer.write_chapter(
        chapter_outline=chapter_outline,
        user_persona=persona,
        character_info=analysis.character_info,
        world_setting=analysis.world_setting,
        writing_style=analysis.writing_style,
        previous_chapters=previous_chapters,
        relationship_state=relationship_state,
        user_power_level=story.user_power_level,
        flags=flags,
    )

    # 生成选项(仅当不是最后一章)
    is_last = (chapter_index + 1) >= story.total_chapters
    choices_json_str = "{}"
    if not is_last:
        choice_gen = ChoiceGenerator()
        choices = await choice_gen.generate_choices(
            chapter_content=chapter_content,
            user_persona=persona,
            character_info=analysis.character_info,
            relationship_state=relationship_state,
            user_power_level=story.user_power_level,
            flags=flags,
        )
        choices_json_str = choices.model_dump_json()

    db_chapter = Chapter(
        story_id=story.id,
        chapter_number=chapter_outline.chapter_number,
        title=chapter_content.title or chapter_outline.title,
        content=chapter_content.content,
        summary=chapter_content.summary,
        key_events_json=json.dumps(chapter_content.key_events, ensure_ascii=False),
        choices_json=choices_json_str,
        user_choice="",
    )
    db.add(db_chapter)
    story.current_chapter = chapter_outline.chapter_number
    if is_last:
        story.status = "finished"
    db.commit()
    db.refresh(db_chapter)
    return db_chapter


# ---------- 章节选项落地 + 触发下一章 ----------

async def choose_and_generate_next(
    db: Session, story_id: int, chapter_number: int, option_id: str
) -> Optional[Chapter]:
    story = db.get(Story, story_id)
    if not story:
        return None
    chapter = next(
        (c for c in story.chapters if c.chapter_number == chapter_number), None
    )
    if not chapter:
        return None

    choices = json.loads(chapter.choices_json or "{}")
    selected = None
    for opt in choices.get("options", []):
        if opt.get("option_id", "").upper() == option_id.upper():
            selected = opt
            break

    chapter.user_choice = option_id.upper()

    # 应用关系值变化
    if selected:
        rel = json.loads(story.relationship_meter_json or "{}")
        for k, delta in (selected.get("relationship_change") or {}).items():
            rel[k] = rel.get(k, 0) + int(delta)
        story.relationship_meter_json = json.dumps(rel, ensure_ascii=False)

        # 应用 flag
        flags = json.loads(story.flags_json or "{}")
        for f in selected.get("flags_set") or []:
            flags[f] = True
        story.flags_json = json.dumps(flags, ensure_ascii=False)

    db.commit()
    db.refresh(story)

    # 已是最后一章 — 不再生成
    if chapter_number >= story.total_chapters:
        story.status = "finished"
        db.commit()
        return None

    persona = UserPersona.model_validate_json(story.user_persona_json)
    outline = StoryOutline.model_validate_json(story.outline_json)
    analysis = await get_or_build_analysis(db, story.novel_id, story.character_id)

    # 实力等级随机渐进式提升 (简单规则:每两章提升一档)
    POWER_LADDER = [
        "淬体第一重", "淬体第三重", "淬体第六重", "淬体第九重",
        "地元境初期", "地元境中期", "地元境后期", "天元境",
    ]
    next_idx = min(chapter_number // 2, len(POWER_LADDER) - 1)
    story.user_power_level = POWER_LADDER[next_idx]
    db.commit()

    return await _write_chapter(
        db, story, analysis, persona, outline, chapter_index=chapter_number
    )


# ---------- 重新生成当前章节 ----------

async def regenerate_chapter(
    db: Session, story_id: int, chapter_number: int
) -> Optional[Chapter]:
    story = db.get(Story, story_id)
    if not story:
        return None
    chapter = next(
        (c for c in story.chapters if c.chapter_number == chapter_number), None
    )
    if not chapter:
        return None

    db.delete(chapter)
    db.commit()
    db.refresh(story)

    persona = UserPersona.model_validate_json(story.user_persona_json)
    outline = StoryOutline.model_validate_json(story.outline_json)
    analysis = await get_or_build_analysis(db, story.novel_id, story.character_id)

    return await _write_chapter(
        db, story, analysis, persona, outline,
        chapter_index=chapter_number - 1,
    )


# ---------- 查询 / 列表 / 删除 / 导出 ----------

def _serialize_chapter(c: Chapter, include_choices: bool, is_last: bool) -> Dict[str, Any]:
    choices_dict = None
    if include_choices and not is_last:
        try:
            raw = json.loads(c.choices_json or "{}")
            if raw:
                choices_dict = raw
        except Exception:
            pass
    return {
        "chapter_number": c.chapter_number,
        "title": c.title,
        "content": c.content,
        "summary": c.summary,
        "key_events": json.loads(c.key_events_json or "[]"),
        "choices": choices_dict,
        "user_choice": c.user_choice,
        "is_last": is_last,
    }


def get_story_detail(db: Session, story_id: int) -> Optional[dict]:
    s = db.get(Story, story_id)
    if not s:
        return None
    novel = db.get(Novel, s.novel_id)
    ch = db.get(Character, s.character_id)
    persona = json.loads(s.user_persona_json)
    outline = json.loads(s.outline_json)
    chapters_data = []
    for c in s.chapters:
        is_last = c.chapter_number >= s.total_chapters
        chapters_data.append(_serialize_chapter(c, include_choices=True, is_last=is_last))

    return {
        "id": s.id,
        "novel_id": s.novel_id,
        "character_id": s.character_id,
        "novel_title": novel.title if novel else "",
        "target_character": ch.name if ch else "",
        "title": s.title,
        "theme": s.theme,
        "user_persona_name": s.user_persona_name,
        "total_chapters": s.total_chapters,
        "current_chapter": s.current_chapter,
        "user_power_level": s.user_power_level,
        "relationship_meter": json.loads(s.relationship_meter_json or "{}"),
        "flags": json.loads(s.flags_json or "{}"),
        "status": s.status,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
        "user_persona": persona,
        "outline": outline,
        "chapters": chapters_data,
    }


def list_stories(db: Session) -> List[dict]:
    out = []
    for s in db.scalars(select(Story).order_by(Story.updated_at.desc())):
        novel = db.get(Novel, s.novel_id)
        ch = db.get(Character, s.character_id)
        out.append(
            {
                "id": s.id,
                "novel_id": s.novel_id,
                "character_id": s.character_id,
                "novel_title": novel.title if novel else "",
                "target_character": ch.name if ch else "",
                "title": s.title,
                "user_persona_name": s.user_persona_name,
                "total_chapters": s.total_chapters,
                "current_chapter": s.current_chapter,
                "user_power_level": s.user_power_level,
                "relationship_meter": json.loads(s.relationship_meter_json or "{}"),
                "status": s.status,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
        )
    return out


def delete_story(db: Session, story_id: int) -> bool:
    s = db.get(Story, story_id)
    if not s:
        return False
    db.delete(s)
    db.commit()
    return True


def export_story_text(db: Session, story_id: int) -> Optional[Path]:
    s = db.get(Story, story_id)
    if not s:
        return None
    novel = db.get(Novel, s.novel_id)
    ch = db.get(Character, s.character_id)
    persona = json.loads(s.user_persona_json)

    lines: List[str] = [
        f"《{s.title}》",
        f"原著: {novel.title if novel else ''} (主角: {ch.name if ch else ''})",
        f"主题: {s.theme}",
        f"我的角色: {s.user_persona_name}  ({persona.get('background','')} | {persona.get('personality','')})",
        f"实力: {s.user_power_level}",
        f"完成章节: {s.current_chapter}/{s.total_chapters}",
        f"生成时间: {s.created_at.strftime('%Y-%m-%d %H:%M')}",
        "",
        "═" * 30,
        "",
    ]
    for c in s.chapters:
        lines.append(f"第{c.chapter_number}章  {c.title}")
        lines.append("─" * 30)
        lines.append(c.content)
        lines.append("")
        if c.user_choice:
            lines.append(f"  [本章你的选择: {c.user_choice}]")
        lines.append("")
        lines.append("═" * 30)
        lines.append("")

    out_path = EXPORTS_DIR / f"story_{s.id}_{datetime.utcnow().strftime('%Y%m%d')}.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
