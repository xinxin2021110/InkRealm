"""故事 schemas"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PersonaOption(BaseModel):
    id: str
    title: str
    description: str
    implications: str = ""


class PersonaDimension(BaseModel):
    description: str
    options: List[PersonaOption]


class PersonaOptionsOut(BaseModel):
    background: PersonaDimension
    personality: PersonaDimension
    relationship: PersonaDimension
    ability: PersonaDimension


class PersonaSelections(BaseModel):
    background: str = "A"
    personality: str = "A"
    relationship: str = "A"
    ability: str = "A"


class CreateStoryIn(BaseModel):
    novel_id: int
    character_id: int
    user_name: str
    selections: PersonaSelections
    total_chapters: int = Field(default=5, ge=3, le=20)


class UserPersonaOut(BaseModel):
    name: str
    background: str = ""
    personality: str = ""
    relationship_to_protagonist: str = ""
    initial_ability: str = ""
    background_detail: str = ""
    personality_detail: str = ""
    relationship_detail: str = ""
    ability_detail: str = ""
    story_goal: str = ""


class ChapterOutlineOut(BaseModel):
    chapter_number: int
    title: str
    core_conflict: str = ""
    scene_setting: str = ""
    character_interaction: str = ""
    plot_function: str = ""
    branch_points: List[str] = []


class StoryOutlineOut(BaseModel):
    total_chapters: int
    title: str
    theme: str = ""
    chapters: List[ChapterOutlineOut] = []


class ChoiceOptionOut(BaseModel):
    option_id: str
    text: str
    description: str = ""
    impact: str = ""
    risk: str = ""
    relationship_change: Dict[str, int] = {}
    flags_set: List[str] = []


class ChapterChoicesOut(BaseModel):
    chapter_number: int
    situation_summary: str = ""
    options: List[ChoiceOptionOut] = []


class ChapterOut(BaseModel):
    chapter_number: int
    title: str
    content: str
    summary: str = ""
    key_events: List[str] = []
    choices: Optional[ChapterChoicesOut] = None
    user_choice: str = ""
    is_last: bool = False


class StoryBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    novel_id: int
    character_id: int
    novel_title: str = ""
    target_character: str = ""
    title: str = ""
    theme: str = ""
    user_persona_name: str
    total_chapters: int
    current_chapter: int
    user_power_level: str
    relationship_meter: Dict[str, int] = {}
    status: str = "ongoing"
    created_at: datetime
    updated_at: datetime


class StoryDetail(StoryBrief):
    user_persona: UserPersonaOut
    outline: StoryOutlineOut
    flags: Dict[str, Any] = {}
    chapters: List[ChapterOut] = []


class ChooseOptionIn(BaseModel):
    option_id: str = Field(..., pattern="^[ABCD]$")


class GenerateChapterOut(BaseModel):
    chapter: ChapterOut
    relationship_meter: Dict[str, int] = {}
    user_power_level: str = ""
