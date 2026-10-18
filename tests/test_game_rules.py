import random
import unittest

import game_rules
from game_rules import FallacySelector


class MasteryTests(unittest.TestCase):
    def test_mastery_requires_three_correct(self):
        selector = FallacySelector()
        self.assertFalse(selector.register_answer(1, True))
        self.assertFalse(selector.register_answer(1, True))
        self.assertTrue(selector.register_answer(1, True))
        self.assertTrue(selector.is_mastered(1))

    def test_mastery_only_reported_once(self):
        selector = FallacySelector()
        for _ in range(3):
            selector.register_answer(1, True)
        self.assertFalse(selector.register_answer(1, True))

    def test_incorrect_does_not_count_toward_mastery(self):
        selector = FallacySelector()
        selector.register_answer(1, False)
        selector.register_answer(1, False)
        selector.register_answer(1, True)
        selector.register_answer(1, True)
        self.assertFalse(selector.is_mastered(1))


class WeightingTests(unittest.TestCase):
    def test_mastered_fallacy_weighs_half_of_unmastered(self):
        selector = FallacySelector()
        for _ in range(3):
            selector.register_answer(1, True)
        unmastered_weight = selector.weight(2)
        mastered_weight = selector.weight(1)
        self.assertAlmostEqual(mastered_weight, unmastered_weight / 2)

    def test_missed_fallacy_gets_weight_bonus(self):
        selector = FallacySelector()
        selector.register_answer(1, False)
        baseline = FallacySelector().weight(1)
        self.assertGreater(selector.weight(1), baseline)

    def test_choose_avoids_immediate_repeat_when_alternatives_exist(self):
        selector = FallacySelector()
        rng = random.Random(0)
        previous = selector.choose([1, 2, 3], rng)
        for _ in range(20):
            current = selector.choose([1, 2, 3], rng)
            self.assertNotEqual(current, previous)
            previous = current

    def test_choose_can_repeat_when_only_one_option(self):
        selector = FallacySelector()
        rng = random.Random(0)
        selector.choose([1], rng)
        # Should not raise even though the only option repeats.
        self.assertEqual(selector.choose([1], rng), 1)

    def test_choose_raises_on_empty_pool(self):
        selector = FallacySelector()
        with self.assertRaises(ValueError):
            selector.choose([], random.Random(0))


class WrongOptionCountTests(unittest.TestCase):
    def test_level_option_counts_match_spec(self):
        self.assertEqual(game_rules.wrong_option_count(1), 3)
        self.assertEqual(game_rules.wrong_option_count(2), 3)
        self.assertEqual(game_rules.wrong_option_count(3), 5)
        self.assertEqual(game_rules.wrong_option_count(4), 5)
        self.assertEqual(game_rules.wrong_option_count(5), 7)
        self.assertEqual(game_rules.wrong_option_count(6), 7)

    def test_infinite_papers_grow_every_two_correct_up_to_eight(self):
        self.assertEqual(game_rules.infinite_option_count(0), 4)
        self.assertEqual(game_rules.infinite_option_count(1), 4)
        self.assertEqual(game_rules.infinite_option_count(2), 5)
        self.assertEqual(game_rules.infinite_option_count(7), 7)
        self.assertEqual(game_rules.infinite_option_count(8), 8)
        self.assertEqual(game_rules.infinite_option_count(100), 8)


class InfiniteTimingTests(unittest.TestCase):
    def test_timer_shrinks_but_has_a_floor(self):
        first = game_rules.infinite_question_seconds(0)
        later = game_rules.infinite_question_seconds(50)
        self.assertEqual(first, game_rules.QUESTION_SECONDS)
        self.assertGreaterEqual(later, game_rules.MIN_INFINITE_SECONDS)
        self.assertLess(later, first)


if __name__ == "__main__":
    unittest.main()
