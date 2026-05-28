"""故事 / 章节 ORM"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(primary_key=True)
    novel_id: Mapped[int] = mapped_column(ForeignKey("novels.id", ondelete="CASCADE"))
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), default="")
    theme: Mapped[str] = mapped_column(String(255), default="")
    user_persona_name: Mapped[str] = mapped_column(String(50))
    user_persona_json: Mapped[str] = mapped_column(Text)         # 完整 UserPersona
    outline_json: Mapped[str] = mapped_column(Text)              # StoryOutline
    total_chapters: Mapped[int] = mapped_column(Integer)
    current_chapter: Mapped[int] = mapped_column(Integer, default=0)
    relationship_meter_json: Mapped[str] = mapped_column(Text, default="{}")
    user_power_level: Mapped[str] = mapped_column(String(50), default="淬体第一重")
    flags_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="ongoing")  # ongoing/finished/abandoned
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    chapters: Mapped[list["Chapter"]] = relationship(
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="Chapter.chapter_number",
    )


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"))
    chapter_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text, default="")
    key_events_json: Mapped[str] = mapped_column(Text, default="[]")
    choices_json: Mapped[str] = mapped_column(Text, default="{}")  # ChapterChoices
    user_choice: Mapped[str] = mapped_column(String(8), default="")  # A/B/C/D 或 ""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    story: Mapped["Story"] = relationship(back_populates="chapters")
