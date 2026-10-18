"""Save-game persistence.

In the browser (Pygbag/emscripten) progress is stored in localStorage.
On desktop it falls back to a small JSON file next to the project so the
prototype can be tested with `python main.py`.
"""

from __future__ import annotations

import json
import sys

SAVE_KEY = "food_court_save"
DESKTOP_SAVE_PATH = ".food_court_save.json"

_DEFAULT_STATE = {
    "dictionary_ids": [],  # fallacy ids added to the dictionary
    "mastery_counts": {},  # fallacy id (str) -> correct count
    "mastered_ids": [],  # fallacy ids mastered
    "completed_levels": [],  # level numbers completed at least once
    "infinite_best_seconds": {},  # level (str) -> best survival seconds
    "music_volume": 0.7,
    "sfx_volume": 0.7,
}


def _is_browser() -> bool:
    return sys.platform == "emscripten"


class Progress:
    def __init__(self) -> None:
        self.dictionary_ids: set[int] = set()
        self.mastery_counts: dict[int, int] = {}
        self.mastered_ids: set[int] = set()
        self.completed_levels: set[int] = set()
        self.infinite_best_seconds: dict[int, float] = {}
        self.music_volume = 0.7
        self.sfx_volume = 0.7
        self.load()

    # -- serialization ---------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "dictionary_ids": sorted(self.dictionary_ids),
            "mastery_counts": {str(k): v for k, v in self.mastery_counts.items()},
            "mastered_ids": sorted(self.mastered_ids),
            "completed_levels": sorted(self.completed_levels),
            "infinite_best_seconds": {
                str(k): v for k, v in self.infinite_best_seconds.items()
            },
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
        }

    def _apply(self, state: dict) -> None:
        self.dictionary_ids = set(state.get("dictionary_ids", []))
        self.mastery_counts = {
            int(k): v for k, v in state.get("mastery_counts", {}).items()
        }
        self.mastered_ids = set(state.get("mastered_ids", []))
        self.completed_levels = set(state.get("completed_levels", []))
        self.infinite_best_seconds = {
            int(k): v for k, v in state.get("infinite_best_seconds", {}).items()
        }
        self.music_volume = float(state.get("music_volume", _DEFAULT_STATE["music_volume"]))
        self.sfx_volume = float(state.get("sfx_volume", _DEFAULT_STATE["sfx_volume"]))

    # -- load/save ---------------------------------------------------

    def load(self) -> None:
        raw = None
        if _is_browser():
            try:
                from js import localStorage  # type: ignore

                raw = localStorage.getItem(SAVE_KEY)
            except Exception:
                raw = None
        else:
            try:
                with open(DESKTOP_SAVE_PATH, "r", encoding="utf-8") as fh:
                    raw = fh.read()
            except OSError:
                raw = None

        if not raw:
            self._apply(dict(_DEFAULT_STATE))
            return

        try:
            state = json.loads(raw)
        except (ValueError, TypeError):
            state = dict(_DEFAULT_STATE)
        self._apply(state)

    def save(self) -> None:
        raw = json.dumps(self.to_dict())
        if _is_browser():
            try:
                from js import localStorage  # type: ignore

                localStorage.setItem(SAVE_KEY, raw)
            except Exception:
                pass
        else:
            try:
                with open(DESKTOP_SAVE_PATH, "w", encoding="utf-8") as fh:
                    fh.write(raw)
            except OSError:
                pass

    def reset(self) -> None:
        # Volume is a preference, not progress, so it survives a reset.
        volumes = (self.music_volume, self.sfx_volume)
        self._apply(dict(_DEFAULT_STATE))
        self.music_volume, self.sfx_volume = volumes
        self.save()

    # -- mutators ---------------------------------------------------

    def add_to_dictionary(self, fallacy_id: int) -> None:
        self.dictionary_ids.add(fallacy_id)
        self.save()

    def record_mastery(self, fallacy_id: int, correct_count: int) -> None:
        self.mastery_counts[fallacy_id] = correct_count
        if correct_count >= 3:
            self.mastered_ids.add(fallacy_id)
        self.save()

    def complete_level(self, level: int) -> None:
        self.completed_levels.add(level)
        self.save()

    def record_infinite_result(self, level: int, survived_seconds: float) -> bool:
        """Update the saved best time. Returns True if it's a new best."""
        best = self.infinite_best_seconds.get(level, 0.0)
        if survived_seconds > best:
            self.infinite_best_seconds[level] = survived_seconds
            self.save()
            return True
        return False
