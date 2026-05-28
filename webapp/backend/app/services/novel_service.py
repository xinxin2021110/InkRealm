"""小说 / 角色 业务逻辑"""
from __future__ import annotations

import json
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from ..config import (
    NOVELS_DIR,
    SEED_NOVEL_AUTHOR,
    SEED_NOVEL_PATH,
    SEED_NOVEL_TITLE,
)
from ..models import Novel, Character


# 角色头像 emoji 池(按角色名 hash 选择,保证可视化丰富)
_AVATAR_POOL = ["🪶", "⚔️", "🌸", "🐉", "🦊", "🦅", "🌙", "🔥", "❄️", "🌿", "🪷", "🌟", "🗡️", "🏹", "📿"]
_COVER_POOL = ["📜", "📕", "📗", "📘", "📙", "🏯", "🌄", "🪔"]


def _pick(pool: List[str], key: str) -> str:
    if not key:
        return pool[0]
    return pool[hash(key) % len(pool)]


def _parse_jsonl(path: Path) -> List[dict]:
    out: List[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _aggregate_characters(rows: List[dict]) -> Dict[str, dict]:
    """按 target_character 分组,返回 {name: {aliases, memory_count, quote_count, summary}}"""
    grouped: Dict[str, dict] = defaultdict(
        lambda: {
            "aliases": set(),
            "memory_count": 0,
            "quote_count": 0,
            "first_summary": "",
        }
    )
    for row in rows:
        name = (row.get("target_character") or "").strip()
        if not name:
            continue
        g = grouped[name]
        for a in row.get("aliases", []) or []:
            if isinstance(a, str) and a.strip():
                g["aliases"].add(a.strip())
        g["memory_count"] += len(row.get("memory_points") or [])
        g["quote_count"] += len(row.get("evidence_quotes") or [])
        if not g["first_summary"]:
            g["first_summary"] = (row.get("summary") or "")[:160]

    return {n: {**v, "aliases": sorted(v["aliases"])} for n, v in grouped.items()}


def list_novels(db: Session) -> List[Novel]:
    return list(db.scalars(select(Novel).order_by(Novel.created_at.desc())))


def get_novel(db: Session, novel_id: int) -> Optional[Novel]:
    return db.get(Novel, novel_id)


def get_character(db: Session, character_id: int) -> Optional[Character]:
    return db.get(Character, character_id)


def list_characters(db: Session, novel_id: int) -> List[Character]:
    return list(
        db.scalars(
            select(Character).where(Character.novel_id == novel_id).order_by(
                Character.is_protagonist.desc(), Character.quote_count.desc()
            )
        )
    )


def parse_aliases(c: Character) -> List[str]:
    try:
        return json.loads(c.aliases or "[]")
    except Exception:
        return []


def create_novel_from_file(
    db: Session,
    src_file: Path,
    title: Optional[str] = None,
    author: Optional[str] = None,
    description: Optional[str] = None,
) -> Novel:
    """从 JSONL 文件创建小说和角色"""
    rows = _parse_jsonl(src_file)
    if not rows:
        raise ValueError("数据文件为空或格式错误")

    book_title = (title or rows[0].get("book_title") or src_file.stem).strip()
    grouped = _aggregate_characters(rows)
    if not grouped:
        raise ValueError("数据文件中未发现任何角色 (target_character)")

    # 如果已有同名小说,则拒绝
    existed = db.scalar(select(Novel).where(Novel.title == book_title))
    if existed is not None:
        raise ValueError(f"小说《{book_title}》已存在")

    # 拷贝文件到 novels 目录(保留中文名)
    safe_name = f"{book_title}_{int(datetime.utcnow().timestamp())}.jsonl"
    dst_path = NOVELS_DIR / safe_name
    shutil.copyfile(src_file, dst_path)

    novel = Novel(
        title=book_title,
        author=(author or "").strip(),
        cover_emoji=_pick(_COVER_POOL, book_title),
        description=(description or "").strip()
        or f"《{book_title}》中的角色与你共绘传奇——共 {len(grouped)} 位可对话角色,{len(rows)} 个章节素材。",
        data_file=str(dst_path),
    )
    db.add(novel)
    db.flush()

    # 主角 = 出场最多的那位 (按 quote_count 排序)
    sorted_names = sorted(
        grouped.items(),
        key=lambda kv: (kv[1]["quote_count"], kv[1]["memory_count"]),
        reverse=True,
    )
    protagonist_name = sorted_names[0][0] if sorted_names else None

    for name, info in grouped.items():
        c = Character(
            novel_id=novel.id,
            name=name,
            aliases=json.dumps(info["aliases"], ensure_ascii=False),
            is_protagonist=(name == protagonist_name),
            profile_summary=info["first_summary"],
            avatar_emoji=_pick(_AVATAR_POOL, name),
            memory_count=info["memory_count"],
            quote_count=info["quote_count"],
        )
        db.add(c)

    db.commit()
    db.refresh(novel)
    return novel


def delete_novel(db: Session, novel_id: int) -> bool:
    novel = db.get(Novel, novel_id)
    if not novel:
        return False
    # 删源文件(忽略失败)
    try:
        p = Path(novel.data_file)
        if p.exists():
            p.unlink()
    except Exception:
        pass
    db.delete(novel)
    db.commit()
    return True


def ensure_seed_novel(db: Session) -> None:
    """如果数据库里没有《武动乾坤》且文件存在,则自动注册"""
    if db.scalar(select(Novel).where(Novel.title == SEED_NOVEL_TITLE)) is not None:
        return
    if not SEED_NOVEL_PATH.exists():
        return
    try:
        create_novel_from_file(
            db,
            SEED_NOVEL_PATH,
            title=SEED_NOVEL_TITLE,
            author=SEED_NOVEL_AUTHOR,
            description="天蚕土豆代表作。少年林动以淬体之身踏入修炼界,以坚毅与赤诚共谱玄幻长歌。",
        )
    except Exception as e:
        print(f"[seed] 注册示例小说失败: {e}")
