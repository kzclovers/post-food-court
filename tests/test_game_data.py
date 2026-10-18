import unittest

import game_data
from game_data import FALLACIES, FALLACIES_BY_ID, LEVELS, claims_for, enemy_for_fallacy


class FallacyDataTests(unittest.TestCase):
    def test_eighteen_fallacies_defined_with_unique_sequential_ids(self):
        ids = [f.id for f in FALLACIES]
        self.assertEqual(ids, list(range(1, 19)))

    def test_every_fallacy_has_name_and_definition(self):
        for fallacy in FALLACIES:
            self.assertTrue(fallacy.name.strip())
            self.assertTrue(fallacy.definition.strip())
            self.assertIsInstance(fallacy.alt_name, str)

    def test_fallacies_by_id_matches_list(self):
        for fallacy in FALLACIES:
            self.assertIs(FALLACIES_BY_ID[fallacy.id], fallacy)


class LevelDataTests(unittest.TestCase):
    def test_six_levels_with_three_fallacies_each(self):
        self.assertEqual(set(LEVELS.keys()), {1, 2, 3, 4, 5, 6})
        for level, info in LEVELS.items():
            self.assertEqual(len(info["fallacy_ids"]), 3)

    def test_each_enemy_hosts_two_consecutive_levels(self):
        self.assertEqual([LEVELS[lvl]["enemy"] for lvl in range(1, 7)], [
            "Vegetable Peeler", "Vegetable Peeler", "Knife", "Knife", "Boiling Pot", "Boiling Pot",
        ])

    def test_levels_cover_all_eighteen_fallacies_without_overlap(self):
        seen: set[int] = set()
        for info in LEVELS.values():
            ids = set(info["fallacy_ids"])
            self.assertFalse(ids & seen, "fallacy id reused across levels")
            seen |= ids
        self.assertEqual(seen, {f.id for f in FALLACIES})

    def test_level_order_matches_spec_progression(self):
        for level in range(1, 7):
            self.assertEqual(LEVELS[level]["fallacy_ids"], list(range(level * 3 - 2, level * 3 + 1)))


class ClaimBankTests(unittest.TestCase):
    def test_every_enemy_has_claims_for_everything_unlocked_by_its_levels(self):
        """Official rounds quiz all unlocked fallacies, so each enemy needs
        claims for its own fallacies and every earlier one."""
        for level, info in LEVELS.items():
            for fallacy_id in range(1, max(info["fallacy_ids"]) + 1):
                claims = claims_for(info["enemy"], fallacy_id)
                self.assertGreaterEqual(len(claims), 2, (info["enemy"], fallacy_id))

    def test_claims_for_unknown_enemy_returns_empty_list(self):
        self.assertEqual(claims_for("Spoon", 1), [])

    def test_claims_for_unknown_fallacy_returns_empty_list(self):
        self.assertEqual(claims_for("Vegetable Peeler", 999), [])


class EnemyForFallacyTests(unittest.TestCase):
    def test_looks_up_the_owning_enemy(self):
        self.assertEqual(enemy_for_fallacy(1), "Vegetable Peeler")
        self.assertEqual(enemy_for_fallacy(7), "Knife")
        self.assertEqual(enemy_for_fallacy(18), "Boiling Pot")

    def test_unknown_id_returns_empty_string(self):
        self.assertEqual(enemy_for_fallacy(999), "")


if __name__ == "__main__":
    unittest.main()
