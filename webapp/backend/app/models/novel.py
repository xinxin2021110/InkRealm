"""小说 / 角色 ORM"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Novel(Base):
    __tablename__ = "novels"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), default="")
    cover_emoji: Mapped[str] = mapped_column(String(8), default="📜")
    description: Mapped[str] = mapped_column(Text, default="")
    data_file: Mapped[str] = mapped_column(String(500))  # JSONL 路径
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    characters: Mapped[list["Character"]] = relationship(
        back_populates="novel",
        cascade="all, delete-orphan",
    )


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), index=True)
    aliases: Mapped[str] = mapped_column(Text, default="[]")  # JSON 字符串
    is_protagonist: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_summary: Mapped[str] = mapped_column(Text, default="")
    avatar_emoji: Mapped[str] = mapped_column(String(8), default="🪶")
    memory_count: Mapped[int] = mapped_column(Integer, default=0)
    quote_count: Mapped[int] = mapped_column(Integer, default=0)
    analyzed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    novel: Mapped["Novel"] = relationship(back_populates="characters")
