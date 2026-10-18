"""Headless smoke tests that drive main.Game through full play sessions.

Runs pygame with the dummy video/audio drivers so it works in CI and on
machines without a display.
"""

import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


@unittest.skipUnless(PYGAME_AVAILABLE, "pygame-ce is not installed")
class GameSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 720))

    def setUp(self):
        import progress as progress_module

        self._tmpdir = tempfile.TemporaryDirectory()
        self._original_path = progress_module.DESKTOP_SAVE_PATH
        progress_module.DESKTOP_SAVE_PATH = os.path.join(self._tmpdir.name, "save.json")

        import main

        self.main = main
        self.game = main.Game()
        self.canvas = pygame.Surface((1280, 720))

    def tearDown(self):
        import progress as progress_module

        progress_module.DESKTOP_SAVE_PATH = self._original_path
        self._tmpdir.cleanup()

    def _run_until(self, target_state, max_steps, answer_correct, level=1):
        """Warm-up questions are always answered correctly (misses there just
        repeat forever); `answer_correct` applies to the official round."""
        steps = 0
        while self.game.state != target_state and steps < max_steps:
            steps += 1
            state = self.game.state
            if state == "MENU":
                self.game._open_level_select()
            elif state == "LEVEL_SELECT":
                self.game._select_level(level)
            elif state == "TEACHING":
                self.game.on_add_to_dictionary()
            elif state == "GAMEPLAY":
                warmup = self.game.phase == "WARMUP" and not self.game.infinite
                self.game.resolve_answer(True if warmup else answer_correct, timeout=False)
            elif state == "FEEDBACK":
                if self.game.review_fallacy_id is not None:
                    self.game.handle_click((640, 400))
                else:
                    self.game.update(game_rules_hold())
            elif state == "GAVEL":
                self.game.update(2.0)
            self.game.layout_buttons()
            self.game.draw(self.canvas)
        return steps

    def _start_level_one_round(self):
        """Select Level 1, collect its three cards, and stop at the first question."""
        self.game._open_level_select()
        self.game._select_level(1)
        for _ in range(3):
            self.game.on_add_to_dictionary()

    def _reveal_papers(self):
        self.game.update(self.main.DIALOGUE_CENTER_SECONDS + 0.01)
        self.game.update(self.main.DIALOGUE_MOVE_SECONDS + 0.01)
        if self.game.dialogue_phase == "WAIT_CLICK":
            self.game.handle_click((640, 560))
            self.game.handle_click((640, 560))

    def _finish_feedback(self):
        if self.game.review_fallacy_id is not None:
            self.game.layout_buttons()
            self.game.handle_click((640, 400))
            self.game.layout_buttons()
            self.game.handle_click((640, 400))
        else:
            self.game.update(game_rules_hold())

    # -- level structure ---------------------------------------------------

    def test_answering_correctly_completes_the_level(self):
        steps = self._run_until("LEVEL_COMPLETE", max_steps=500, answer_correct=True)
        self.assertEqual(self.game.state, "LEVEL_COMPLETE")
        self.assertLess(steps, 500)
        self.assertEqual(self.game.progress.dictionary_ids, {1, 2, 3})
        self.assertEqual(self.game.enemy_health, 0)
        self.assertEqual(self.game.health, 6)
        self.assertIn(1, self.game.progress.completed_levels)

    def test_answering_incorrectly_fails_the_level(self):
        steps = self._run_until("LEVEL_FAILED", max_steps=500, answer_correct=False)
        self.assertEqual(self.game.state, "LEVEL_FAILED")
        self.assertLess(steps, 500)
        self.assertEqual(self.game.health, 0)
        self.assertEqual(self.game.enemy_health, 2)

    def test_all_three_cards_are_introduced_together(self):
        self.game._open_level_select()
        self.game._select_level(1)
        self.assertEqual(self.game.state, "TEACHING")
        self.assertEqual(self.game.teaching_ids, [1, 2, 3])
        self.game.layout_buttons()
        self.game.draw(self.canvas)

        self.game.on_add_to_dictionary(2)
        self.assertEqual(self.game.state, "TEACHING")
        self.assertEqual(self.game.progress.dictionary_ids, {2})
        self.game.draw(self.canvas)

        self.game.on_add_to_dictionary(1)
        self.game.on_add_to_dictionary(3)
        self.assertEqual(self.game.state, "GAMEPLAY")
        self.assertEqual(self.game.phase, "WARMUP")
        self.assertEqual(sorted(self.game.warmup_queue), [1, 2, 3])

    def test_warmup_misses_are_free_and_repeat_the_same_fallacy(self):
        self._start_level_one_round()
        self._reveal_papers()
        first = self.game.current_fallacy_id

        self.game.resolve_answer(False, timeout=False)
        self.assertEqual(self.game.health, 6)
        self._finish_feedback()
        self.assertEqual(self.game.current_fallacy_id, first)
        self.assertEqual(self.game.phase, "WARMUP")

        asked = [first]
        self.game.resolve_answer(True, timeout=False)
        self._finish_feedback()
        for _ in range(2):
            asked.append(self.game.current_fallacy_id)
            self.game.resolve_answer(True, timeout=False)
            self._finish_feedback()
        self.assertEqual(sorted(asked), [1, 2, 3])
        self.assertEqual(self.game.phase, "ROUND")
        self.assertEqual(self.game.enemy_health, 2)

    def test_official_round_damages_both_sides_without_healing(self):
        self._start_level_one_round()
        for _ in range(3):
            self.game.resolve_answer(True, timeout=False)
            self._finish_feedback()
        self.assertEqual(self.game.phase, "ROUND")

        self.game.resolve_answer(False, timeout=False)
        self._finish_feedback()
        self.assertEqual(self.game.health, 5)

        self.game.resolve_answer(True, timeout=False)
        self._finish_feedback()
        self.assertEqual(self.game.health, 5)
        self.assertEqual(self.game.enemy_health, 1)

    def test_official_round_only_asks_unlocked_fallacies(self):
        self.game.progress.completed_levels.add(1)
        self.game.progress.dictionary_ids.update({1, 2, 3, 4, 5, 6, 7})
        self.game._open_level_select()
        self.game._select_level(2)
        for _ in range(3):
            self.game.on_add_to_dictionary()
        self.game.phase = "ROUND"
        self.assertEqual(self.game._quizzable_ids(), [1, 2, 3, 4, 5, 6])

    def test_levels_unlock_in_order(self):
        self.game._open_level_select()
        self.game._select_level(2)
        self.assertEqual(self.game.state, "LEVEL_SELECT")
        self._run_until("LEVEL_COMPLETE", max_steps=500, answer_correct=True)
        self.game._next_level()
        self.assertEqual(self.game.state, "TEACHING")
        self.assertEqual(self.game.level, 2)
        self.assertEqual(self.game.enemy_name, "Vegetable Peeler")

    def test_later_levels_use_their_own_enemy(self):
        self.game.progress.completed_levels.update({1, 2, 3, 4})
        self.game._open_level_select()
        self.game._select_level(5)
        self.assertEqual(self.game.enemy_name, "Boiling Pot")
        self.assertEqual(self.game.teaching_ids, [13, 14, 15])
        for _ in range(3):
            self.game.on_add_to_dictionary()
        self._reveal_papers()
        self.assertEqual(len(self.game.papers), 8)
        self.game.draw(self.canvas)

    # -- pause ---------------------------------------------------

    def test_pause_freezes_the_question_timer(self):
        self._start_level_one_round()
        self._reveal_papers()
        self.game.layout_buttons()
        self.game.handle_click(self.main.PAUSE_BUTTON_RECT.center)
        self.assertTrue(self.game.paused)
        before = self.game.timer
        self.game.update(5.0)
        self.assertEqual(self.game.timer, before)
        self.game.draw(self.canvas)

        self.game.layout_buttons()
        continue_button = next(b for b in self.game.buttons if b.label == "Continue")
        self.game.handle_click(continue_button.rect.center)
        self.assertFalse(self.game.paused)

    def test_warmup_has_no_time_limit(self):
        self._start_level_one_round()
        self._reveal_papers()
        self.game.update(60.0)
        self.assertEqual(self.game.state, "GAMEPLAY")
        self.assertFalse(self.game.answered)

    def test_replaying_a_known_level_skips_cards_and_warmup(self):
        self.game.progress.dictionary_ids.update({1, 2, 3})
        self.game._open_level_select()
        self.game._select_level(1)
        self.assertEqual(self.game.state, "GAMEPLAY")
        self.assertEqual(self.game.phase, "ROUND")

    def test_dev_mode_unlocks_everything_without_saving(self):
        self.game.dev_input = "wrong"
        self.game.submit_dev_password()
        self.assertFalse(self.game.dev_unlocked)
        self.game.dev_input = "dev67"
        self.game.submit_dev_password()
        self.assertTrue(self.game.dev_unlocked)
        self.game._toggle_dev_mode()
        self.assertTrue(self.game._level_unlocked(6))
        self.assertEqual(len(self.game._dictionary_entries()), 18)
        self.assertTrue(self.game._infinite_available())
        self.assertEqual(self.game.progress.dictionary_ids, set())
        self.game._toggle_dev_mode()
        self.assertFalse(self.game._level_unlocked(6))
        self.assertEqual(self.game._dictionary_entries(), [])

    def test_settings_page_lays_out_and_draws(self):
        self.game._open_settings()
        self.game.layout_buttons()
        self.game.draw(self.canvas)

    def test_exiting_a_main_level_returns_to_level_select(self):
        self._start_level_one_round()
        self.game._pause()
        self.game._exit_level()
        self.assertEqual(self.game.state, "LEVEL_SELECT")
        self.assertNotIn(1, self.game.progress.completed_levels)
        self.game.layout_buttons()
        self.game.draw(self.canvas)

    def test_exiting_infinite_mode_skips_the_popup(self):
        self._run_until("LEVEL_COMPLETE", max_steps=500, answer_correct=True)
        self.game.start_infinite()
        self.game._pause()
        self.game._exit_level()
        self.assertEqual(self.game.state, "LEVEL_SELECT")

    # -- infinite mode ---------------------------------------------------

    def test_infinite_mode_is_locked_until_a_level_is_completed(self):
        self.game._open_level_select()
        self.game.layout_buttons()
        infinite = next(b for b in self.game.buttons if b.label == "Infinite Mode")
        self.assertFalse(infinite.enabled)
        self._run_until("LEVEL_COMPLETE", max_steps=500, answer_correct=True)
        self.game._open_level_select()
        self.game.layout_buttons()
        infinite = next(b for b in self.game.buttons if b.label == "Infinite Mode")
        self.assertTrue(infinite.enabled)

    def test_infinite_mode_ends_and_records_best_time(self):
        self._run_until("LEVEL_COMPLETE", max_steps=500, answer_correct=True)
        self.game._replay_infinite()
        steps = self._run_until("INFINITE_RESULTS", max_steps=2000, answer_correct=False)
        self.assertEqual(self.game.state, "INFINITE_RESULTS")
        self.assertLess(steps, 2000)
        self.assertIn(self.main.INFINITE_SAVE_KEY, self.game.progress.infinite_best_seconds)

    def test_infinite_mode_heals_and_grows_the_paper_count(self):
        self._run_until("LEVEL_COMPLETE", max_steps=500, answer_correct=True)
        self.game.start_infinite()
        self.assertEqual(self.game.state, "GAMEPLAY")
        self._reveal_papers()
        self.assertEqual(len(self.game.papers), 4)
        self.assertTrue(set(self.game.fallacy_ids) <= {1, 2, 3})

        self.game.resolve_answer(False, timeout=False)
        self._finish_feedback()
        self.assertEqual(self.game.health, 5)
        for _ in range(2):
            self.game.resolve_answer(True, timeout=False)
            self._finish_feedback()
        self.assertEqual(self.game.health, 6)
        self._reveal_papers()
        self.assertEqual(len(self.game.papers), 5)

    # -- menus and screens ---------------------------------------------------

    def test_dictionary_and_settings_overlays_do_not_crash(self):
        self._run_until("LEVEL_COMPLETE", max_steps=500, answer_correct=True)
        self.game._open_dictionary()
        self.game.layout_buttons()
        self.game.draw(self.canvas)
        self.game._next_page()
        self.game.draw(self.canvas)
        self.game._close_dictionary()

        self.game._open_settings()
        self.game.layout_buttons()
        self.game.draw(self.canvas)
        self.game._ask_reset()
        self.game.layout_buttons()
        self.game.draw(self.canvas)
        self.game._confirm_reset()
        self.assertEqual(self.game.progress.dictionary_ids, set())
        self.assertEqual(self.game.state, "MENU")

    def test_window_to_virtual_maps_center_to_center(self):
        vx, vy = self.main.window_to_virtual((640, 360), (1280, 720))
        self.assertAlmostEqual(vx, 640)
        self.assertAlmostEqual(vy, 360)

    def test_game_starts_at_the_main_menu(self):
        self.assertEqual(self.game.state, "MENU")

    def test_menu_navigation_round_trip(self):
        self.game._open_how_to_play()
        self.assertEqual(self.game.state, "HOW_TO_PLAY")
        self.game.draw(self.canvas)
        self.game._go_menu()
        self.assertEqual(self.game.state, "MENU")

        self.game._open_settings()
        self.assertEqual(self.game.state, "SETTINGS")
        self.game.draw(self.canvas)
        self.game._close_settings()
        self.assertEqual(self.game.state, "MENU")

    def test_dialogue_centers_then_moves_before_papers_appear(self):
        self._start_level_one_round()

        self.assertEqual(self.game.state, "GAMEPLAY")
        self.assertEqual(self.game.dialogue_phase, "CENTER")
        self.assertEqual(self.game.papers, [])
        self.game.draw(self.canvas)

        self.game.update(self.main.DIALOGUE_CENTER_SECONDS + 0.01)
        self.assertEqual(self.game.dialogue_phase, "MOVING")
        self.assertEqual(self.game.papers, [])

        self.game.update(self.main.DIALOGUE_MOVE_SECONDS + 0.01)
        self.assertEqual(self.game.dialogue_phase, "WAIT_CLICK")
        self.assertEqual(self.game.papers, [])
        # Dismiss judge dialogue to advance to gameplay
        self.game.handle_click((640, 560))
        self.game.handle_click((640, 560))
        self.assertEqual(self.game.dialogue_phase, "DONE")
        self.assertGreater(len(self.game.papers), 0)
        self.assertAlmostEqual(self.game.timer, self.game.timer_max)

    def test_wrong_answer_pops_the_correct_flashcard(self):
        self._start_level_one_round()
        self._reveal_papers()
        fid = self.game.current_fallacy_id
        before = set(self.game.progress.dictionary_ids)
        self.game.resolve_answer(False, timeout=False)
        self.assertEqual(self.game.review_fallacy_id, fid)
        self.assertEqual(self.game.progress.dictionary_ids, before)
        self.game.draw(self.canvas)
        self.game.layout_buttons()
        self.game.handle_click((640, 400))
        self.game.update(5)
        self.assertEqual(self.game.state, "FEEDBACK")
        self.assertEqual(self.game.review_fallacy_id, fid)
        self.game.layout_buttons()
        self.game.handle_click((640, 400))
        self.assertIsNone(self.game.review_fallacy_id)
        self.assertEqual(self.game.progress.dictionary_ids, before)

    def test_leftover_dictionary_cards_sit_on_both_pages(self):
        self.game.progress.dictionary_ids.update({1, 2, 3, 4, 5, 6})
        self.game._open_dictionary()
        self.assertEqual(self.game._spread_count(), 2)
        self.assertEqual(self.game._spread_ids(0), (1, 3, 2, 4))
        self.assertEqual(self.game._spread_ids(1), (3, 5, 4, 6))
        self.game.dictionary_page = 1
        self.game.layout_buttons()
        self.game.draw(self.canvas)

    def test_clicking_a_dictionary_card_enlarges_it(self):
        self.game.progress.dictionary_ids.update({1, 2})
        self.game._open_dictionary()
        self.game.layout_buttons()
        self.game._open_card(1)
        self.assertEqual(self.game.zoomed_card, 1)
        self.game.update(0.2)
        self.game.layout_buttons()
        self.game.draw(self.canvas)
        self.game._close_zoom()
        self.assertIsNone(self.game.zoomed_card)
        self.game.draw(self.canvas)

    def test_dictionary_page_turn_advances_a_spread(self):
        self.game.progress.dictionary_ids.update({1, 2, 3, 4, 5})
        self.game._open_dictionary()
        self.game.layout_buttons()
        self.game.draw(self.canvas)
        self.game._next_page()
        self.assertEqual(self.game.dictionary_page, 0)
        self.assertIsNotNone(self.game.page_anim)
        self.game.draw(self.canvas)
        self.game.update(self.main.PAGE_TURN_SECONDS * 0.5)
        self.game.draw(self.canvas)
        self.game.update(self.main.PAGE_TURN_SECONDS)
        self.assertIsNone(self.game.page_anim)
        self.assertEqual(self.game.dictionary_page, 1)
        self.game.layout_buttons()
        self.game.draw(self.canvas)

    def test_clicking_during_dialogue_phase_is_ignored(self):
        self._start_level_one_round()
        self.assertEqual(self.game.dialogue_phase, "CENTER")

        self.game.handle_click((640, 300))
        self.assertEqual(self.game.state, "GAMEPLAY")
        self.assertFalse(self.game.answered)


def game_rules_hold():
    import game_rules

    return game_rules.FEEDBACK_HOLD_SECONDS + 0.1


if __name__ == "__main__":
    unittest.main()
