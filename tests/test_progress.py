import os
import tempfile
import unittest

import progress as progress_module
from progress import Progress


class ProgressPersistenceTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._original_path = progress_module.DESKTOP_SAVE_PATH
        progress_module.DESKTOP_SAVE_PATH = os.path.join(self._tmpdir.name, "save.json")

    def tearDown(self):
        progress_module.DESKTOP_SAVE_PATH = self._original_path
        self._tmpdir.cleanup()

    def test_fresh_progress_is_empty(self):
        p = Progress()
        self.assertEqual(p.dictionary_ids, set())
        self.assertEqual(p.mastered_ids, set())
        self.assertEqual(p.completed_levels, set())

    def test_add_to_dictionary_persists_across_instances(self):
        p = Progress()
        p.add_to_dictionary(1)
        p.add_to_dictionary(2)

        reloaded = Progress()
        self.assertEqual(reloaded.dictionary_ids, {1, 2})

    def test_record_mastery_sets_mastered_at_three(self):
        p = Progress()
        p.record_mastery(1, 2)
        self.assertNotIn(1, Progress().mastered_ids)
        p.record_mastery(1, 3)
        self.assertIn(1, Progress().mastered_ids)

    def test_complete_level_persists(self):
        p = Progress()
        p.complete_level(1)
        self.assertIn(1, Progress().completed_levels)

    def test_infinite_best_only_updates_on_improvement(self):
        p = Progress()
        self.assertTrue(p.record_infinite_result(1, 12))
        self.assertFalse(p.record_infinite_result(1, 5))
        self.assertTrue(p.record_infinite_result(1, 20))
        self.assertEqual(Progress().infinite_best_correct[1], 20)

    def test_reset_clears_everything_and_persists(self):
        p = Progress()
        p.add_to_dictionary(1)
        p.record_mastery(1, 3)
        p.complete_level(1)
        p.reset()

        reloaded = Progress()
        self.assertEqual(reloaded.dictionary_ids, set())
        self.assertEqual(reloaded.mastered_ids, set())
        self.assertEqual(reloaded.completed_levels, set())

    def test_corrupt_save_file_falls_back_to_defaults(self):
        with open(progress_module.DESKTOP_SAVE_PATH, "w", encoding="utf-8") as fh:
            fh.write("not json")
        p = Progress()
        self.assertEqual(p.dictionary_ids, set())


if __name__ == "__main__":
    unittest.main()
