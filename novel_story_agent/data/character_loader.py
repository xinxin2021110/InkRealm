"""CharacterLoader —— webapp 仍在用的入口，内部委托 inkrealm.JsonlLoader。"""
from __future__ import annotations

from typing import Any, Dict, List

from inkrealm.data.jsonl_loader import JsonlLoader
from inkrealm.data.profile_builder import ProfileBuilder

from ..schema import CharacterInfo


class CharacterLoader:
    def __init__(self, data_file: str) -> None:
        self._loader = JsonlLoader(data_file)
        self._info: CharacterInfo | None = None

    def load_data(self) -> List[Dict[str, Any]]:
        return self._loader.load_raw()

    def get_character_info(self) -> CharacterInfo:
        if self._info is None:
            profile = self._loader.build_profile()
            profile = ProfileBuilder(profile).build()
            self._info = profile
        return self._info

    def get_style_samples(self, count: int = 5) -> List[str]:
        rows = self.load_data()
        samples: List[str] = []
        for chapter in rows[: count * 2]:
            for q in (chapter.get("evidence_quotes") or [])[:2]:
                if len(q) > 50:
                    samples.append(q)
            for d in (chapter.get("dialogue_examples") or [])[:2]:
                if len(d) > 20:
                    samples.append(d)
            if len(samples) >= count * 3:
                break
        good = [s for s in samples if 50 <= len(s) <= 300]
        return good[:count]

    def get_world_info(self) -> Dict[str, Any]:
        rows = self.load_data()
        if not rows:
            return {}
        first = rows[0]
        return {
            "book_title": first.get("book_title", ""),
            "target_character": first.get("target_character", ""),
            "total_chapters": len(rows),
            "first_chapter_summary": first.get("summary", ""),
            "last_chapter_summary": rows[-1].get("summary", ""),
        }
