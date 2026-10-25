"""
MarketQuest - Automated Tests for Story Campaign Engine
"""

import unittest
from src.story import StoryManager


class DummyGame:
    def __init__(self):
        self.xp = 0
        self.badges = []
        class DummyPortfolio:
            cash = 1000.0
            positions = {}
        class DummyInvestigation:
            unlocked = set()
            def unlock_clue(self, c_id):
                self.unlocked.add(c_id)
        class DummySound:
            def play(self, s): pass
        self.portfolio = DummyPortfolio()
        self.investigation = DummyInvestigation()
        self.sound_mgr = DummySound()

    def add_xp(self, amount, reason=""):
        self.xp += amount


class TestStoryCampaign(unittest.TestCase):
    def setUp(self):
        self.story = StoryManager()
        self.game = DummyGame()

    def test_campaign_loads_all_chapters(self):
        """Verify that all 6 campaign chapters are loaded properly."""
        self.assertEqual(self.story.get_total_chapters(), 6)
        chap1 = self.story.get_current_chapter()
        self.assertIsNotNone(chap1)
        self.assertEqual(chap1["chapter_index"], 1)

    def test_objective_progression_and_rewards(self):
        """Verify talking to target NPC advances objective and awards XP/cash."""
        obj = self.story.get_active_objective()
        self.assertIsNotNone(obj)
        self.assertEqual(obj["id"], "c1_talk_mentor")

        # Talk to wrong NPC -> no advance
        res = self.story.on_talk_npc("random_npc", self.game)
        self.assertIsNone(res)
        self.assertEqual(self.story.current_objective_idx, 0)

        # Talk to correct mentor -> advances
        res = self.story.on_talk_npc("devendra", self.game)
        self.assertIsNotNone(res)
        self.assertEqual(self.story.current_objective_idx, 1)
        self.assertEqual(self.game.xp, 50)
        self.assertEqual(self.game.portfolio.cash, 1100.0)

    def test_save_and_load_persistence(self):
        """Verify story progression state serializes and deserializes cleanly."""
        self.story.on_talk_npc("devendra", self.game)
        state = self.story.to_dict()

        story2 = StoryManager()
        story2.load_state(state)
        self.assertEqual(story2.current_chapter_idx, self.story.current_chapter_idx)
        self.assertEqual(story2.current_objective_idx, self.story.current_objective_idx)
        self.assertIn("c1_talk_mentor", story2.completed_objectives)


if __name__ == "__main__":
    unittest.main()
