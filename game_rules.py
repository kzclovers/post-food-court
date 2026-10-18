"""Gameplay tuning constants and the Quizlet-style fallacy selector.

Kept free of pygame and rendering concerns so the rules can be unit
tested in isolation (see tests/test_game_rules.py).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# --- Tuning values -----------------------------------------------------

HEALTH_MAX = 6
OPPONENT_HEALTH_MAX = 5  # main levels: each correct answer removes one
MASTERY_TARGET = 3  # correct answers needed to master a fallacy
QUESTION_SECONDS = 10.0
FEEDBACK_HOLD_SECONDS = 2.0

# One correct answer plus this many decoys, per level (grows with each enemy).
WRONG_OPTION_COUNTS = {1: 3, 2: 3, 3: 5, 4: 5, 5: 7, 6: 7}

# Infinite mode: total answer papers start at 4 and grow by one every
# INFINITE_CORRECT_PER_OPTION correct answers, up to INFINITE_MAX_OPTIONS.
INFINITE_START_OPTIONS = 4
INFINITE_MAX_OPTIONS = 8
INFINITE_CORRECT_PER_OPTION = 2

# Infinite mode: each question's timer is multiplied by this factor,
# bottoming out at MIN_INFINITE_SECONDS.
INFINITE_TIME_DECAY = 0.92
MIN_INFINITE_SECONDS = 1.5

UNMASTERED_WEIGHT = 2.0
MASTERED_WEIGHT = 1.0  # exactly half of UNMASTERED_WEIGHT
MISS_WEIGHT_BONUS = 1.5


def wrong_option_count(level: int) -> int:
    return WRONG_OPTION_COUNTS.get(level, WRONG_OPTION_COUNTS[max(WRONG_OPTION_COUNTS)])


def infinite_option_count(correct_answers: int) -> int:
    """Total answer papers (correct + decoys) in infinite mode."""
    grown = INFINITE_START_OPTIONS + correct_answers // INFINITE_CORRECT_PER_OPTION
    return min(INFINITE_MAX_OPTIONS, grown)


@dataclass
class FallacyStats:
    correct: int = 0
    incorrect: int = 0
    mastered: bool = False

    def register(self, was_correct: bool) -> bool:
        """Record an answer. Returns True if this answer caused mastery."""
        if was_correct:
            self.correct += 1
        else:
            self.incorrect += 1
        if not self.mastered and self.correct >= MASTERY_TARGET:
            self.mastered = True
            return True
        return False


@dataclass
class FallacySelector:
    """Chooses which introduced fallacy to quiz next.

    Unmastered fallacies are weighted more heavily than mastered ones
    (mastered fallacies drop to half weight), and fallacies the player has
    missed recently get an extra weight boost so review is biased toward
    trouble spots, similar to a Quizlet learning session.
    """

    stats: dict[int, FallacyStats] = field(default_factory=dict)
    _last_fallacy_id: int | None = field(default=None, repr=False)

    def stats_for(self, fallacy_id: int) -> FallacyStats:
        return self.stats.setdefault(fallacy_id, FallacyStats())

    def is_mastered(self, fallacy_id: int) -> bool:
        return self.stats_for(fallacy_id).mastered

    def all_mastered(self, fallacy_ids: list[int]) -> bool:
        return all(self.is_mastered(fid) for fid in fallacy_ids)

    def weight(self, fallacy_id: int) -> float:
        s = self.stats_for(fallacy_id)
        base = MASTERED_WEIGHT if s.mastered else UNMASTERED_WEIGHT
        return base + MISS_WEIGHT_BONUS * s.incorrect

    def choose(self, available_ids: list[int], rng: random.Random | None = None) -> int:
        if not available_ids:
            raise ValueError("No fallacies available to choose from")
        rng = rng or random
        pool = available_ids
        if len(available_ids) > 1 and self._last_fallacy_id in available_ids:
            # Avoid immediately repeating the same fallacy when another
            # option exists.
            pool = [fid for fid in available_ids if fid != self._last_fallacy_id]
        weights = [self.weight(fid) for fid in pool]
        choice = rng.choices(pool, weights=weights, k=1)[0]
        self._last_fallacy_id = choice
        return choice

    def register_answer(self, fallacy_id: int, was_correct: bool) -> bool:
        return self.stats_for(fallacy_id).register(was_correct)


def infinite_question_seconds(question_index: int) -> float:
    """Timer length for the question_index-th question (0-based) of an
    infinite-mode run."""
    seconds = QUESTION_SECONDS * (INFINITE_TIME_DECAY**question_index)
    return max(MIN_INFINITE_SECONDS, seconds)
