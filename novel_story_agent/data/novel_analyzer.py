"""NovelAnalyzer —— webapp 仍在用的入口，内部用 WritingEnvironment.analyze_novel 跑分析。

对外形态保持：返回 NovelAnalysis(world_setting / character_info / writing_style / raw_data)。
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..environment.writing_environment import WritingEnvironment
from ..schema import NovelAnalysis
from .character_loader import CharacterLoader


class NovelAnalyzer:
    def __init__(self, data_file: str) -> None:
        self.loader = CharacterLoader(data_file)
        self._env = WritingEnvironment()

    async def analyze(self) -> NovelAnalysis:
        raw_chapters: List[Dict[str, Any]] = self.loader.load_data()
        basic = self.loader.get_character_info()
        style_samples = self.loader.get_style_samples(count=6)

        novel_profile = await self._env.analyze_novel(
            basic_profile=basic,
            raw_chapters=raw_chapters,
            style_samples=style_samples,
        )

        return NovelAnalysis(
            world_setting=novel_profile.world_setting,
            character_info=novel_profile.target_character,
            writing_style=novel_profile.writing_style,
            raw_data=raw_chapters,
        )

    def get_raw_chapters(self):
        return self.loader.load_data()
