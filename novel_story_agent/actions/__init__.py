"""novel_story_agent.actions — 故事续写产品的具体 Action（MetaGPT 风格）。"""
from .analyze_world import AnalyzeWorldSettingAction
from .analyze_style import AnalyzeWritingStyleAction
from .enrich_character import EnrichCharacterAction
from .propose_persona_dimensions import GeneratePersonaDimensionsAction
from .build_user_persona import BuildUserPersonaAction
from .propose_outline import ProposeStoryOutlineAction
from .draft_chapter import DraftChapterAction
from .summarize_chapter import SummarizeChapterAction, ExtractKeyEventsAction
from .generate_choices import GenerateChapterChoicesAction

__all__ = [
    "AnalyzeWorldSettingAction",
    "AnalyzeWritingStyleAction",
    "EnrichCharacterAction",
    "GeneratePersonaDimensionsAction",
    "BuildUserPersonaAction",
    "ProposeStoryOutlineAction",
    "DraftChapterAction",
    "SummarizeChapterAction",
    "ExtractKeyEventsAction",
    "GenerateChapterChoicesAction",
]
