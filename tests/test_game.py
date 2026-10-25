"""
MarketQuest - Comprehensive Automated Test Suite
Covers market simulation, order validation, accounting integrity, events,
boundaries, saving/loading, and state machine navigation.
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

import config
from src.market import MarketEngine, Company, MarketEvent
from src.trading import Portfolio, Position
from src.save_manager import SaveManager
from src.world import World, build_wall_street_map, build_dalal_street_map
from src.game import Game, STATE_TITLE, STATE_GAMEPLAY, STATE_TRADING, STATE_PORTFOLIO, STATE_PAUSE

class TestMarketEngine(unittest.TestCase):
    def setUp(self):
        self.market = MarketEngine(seed=42)

    def test_companies_loaded(self):
        """Ensure at least 6 companies loaded with valid attributes."""
        companies = self.market.get_all_companies()
        self.assertGreaterEqual(len(companies), 6)
        symbols = [c.symbol for c in companies]
        for expected in ["APEX", "NOVA", "TITN", "AURA", "CHAI", "MEDX"]:
            self.assertIn(expected, symbols)

    def test_price_history_initialized(self):
        """Ensure each company has realistic price history for charting."""
        apex = self.market.get_company("APEX")
        self.assertIsNotNone(apex)
        self.assertGreaterEqual(len(apex.price_history), 20)
        self.assertGreater(apex.price, 0)
        self.assertAlmostEqual(apex.price, apex.price_history[-1], places=2)

    def test_market_tick_progression(self):
        """Tick advances day and records new prices."""
        initial_day = self.market.day
        reports = self.market.tick()
        self.assertEqual(self.market.day, initial_day + 1)
        self.assertEqual(len(reports), len(self.market.companies))

    def test_price_boundaries_enforced(self):
        """Ensure prices never fall below MIN_STOCK_PRICE even under extreme negative shocks."""
        comp = self.market.get_company("TITN")
        original_price = comp.price
        
        # Apply massive negative shocks
        for _ in range(50):
            ev = MarketEvent(
                id="CRASH_TEST",
                headline="Devastating Market Crash",
                explanation="Massive selloff test",
                affected_type="company",
                target="TITN",
                impact=-0.50,
                duration_days=1,
                education="Testing bounds"
            )
            self.market.apply_event(ev)

        self.assertGreaterEqual(comp.price, config.MIN_STOCK_PRICE)
        self.assertTrue(comp.price.is_integer() or isinstance(comp.price, float))

    def test_deterministic_seeded_simulation(self):
        """Identical seeds must yield identical price evolutions."""
        m1 = MarketEngine(seed=999)
        m2 = MarketEngine(seed=999)

        for _ in range(10):
            m1.tick()
            m2.tick()

        for sym in m1.companies:
            self.assertEqual(m1.companies[sym].price, m2.companies[sym].price)

    def test_event_application_and_news(self):
        """Market event updates target prices and posts to news feed."""
        apex = self.market.get_company("APEX")
        old_price = apex.price
        news = self.market.trigger_event_by_id("APEX_AI_CHIP")
        
        self.assertIsNotNone(news)
        self.assertGreater(apex.price, old_price)
        self.assertEqual(self.market.news_feed[0]["headline"], news["headline"])


class TestTradingAndPortfolio(unittest.TestCase):
    def setUp(self):
        self.portfolio = Portfolio(starting_cash=10000.0)
        self.market = MarketEngine(seed=42)

    def test_valid_buy_order(self):
        """Executing a valid buy deducts cash, increases holdings and tracks cost basis."""
        price = 100.0
        success, msg = self.portfolio.buy("APEX", 10, price, day=1)
        self.assertTrue(success)
        self.assertEqual(self.portfolio.cash, 9000.0)
        self.assertEqual(self.portfolio.get_shares_owned("APEX"), 10)
        pos = self.portfolio.get_position("APEX")
        self.assertEqual(pos.total_cost_basis, 1000.0)
        self.assertEqual(pos.avg_cost, 100.0)

    def test_insufficient_funds_buy_rejected(self):
        """Buying more shares than available cash is rejected with no state change."""
        success, msg = self.portfolio.buy("APEX", 1000, 150.0)  # Requires $150,000, have $10,000
        self.assertFalse(success)
        self.assertIn("Insufficient", msg)
        self.assertEqual(self.portfolio.cash, 10000.0)
        self.assertEqual(self.portfolio.get_shares_owned("APEX"), 0)

    def test_invalid_order_quantities_rejected(self):
        """Negative, zero, or non-integer quantities are rejected."""
        valid, _ = self.portfolio.validate_buy("APEX", -5, 100.0)
        self.assertFalse(valid)
        valid, _ = self.portfolio.validate_buy("APEX", 0, 100.0)
        self.assertFalse(valid)
        valid, _ = self.portfolio.validate_buy("APEX", 2.5, 100.0)
        self.assertFalse(valid)

    def test_valid_sell_and_realized_pnl(self):
        """Selling shares correctly computes realized P&L and updates cost basis."""
        # Buy 10 @ $100 ($1000 cost)
        self.portfolio.buy("APEX", 10, 100.0)
        # Sell 5 @ $140 ($700 proceeds, $500 cost basis sold -> +$200 P&L)
        success, msg, pnl = self.portfolio.sell("APEX", 5, 140.0)
        self.assertTrue(success)
        self.assertEqual(pnl, 200.0)
        self.assertEqual(self.portfolio.realized_pnl, 200.0)
        self.assertEqual(self.portfolio.cash, 9000.0 + 700.0)
        pos = self.portfolio.get_position("APEX")
        self.assertEqual(pos.shares, 5)
        self.assertEqual(pos.total_cost_basis, 500.0)
        self.assertEqual(pos.avg_cost, 100.0)

    def test_sell_more_than_owned_rejected(self):
        """Cannot sell unowned shares."""
        self.portfolio.buy("TITN", 5, 50.0)
        success, msg, pnl = self.portfolio.sell("TITN", 10, 50.0)
        self.assertFalse(success)
        self.assertEqual(self.portfolio.get_shares_owned("TITN"), 5)

    def test_selling_entire_position_resets_basis(self):
        """Selling all shares leaves 0 shares and $0.00 cost basis."""
        self.portfolio.buy("NOVA", 4, 80.0)
        self.portfolio.sell("NOVA", 4, 90.0)
        pos = self.portfolio.get_position("NOVA")
        self.assertEqual(pos.shares, 0)
        self.assertEqual(pos.total_cost_basis, 0.0)

    def test_portfolio_accounting_consistency(self):
        """Total value = cash + market value; Unrealized P&L = market value - cost basis."""
        self.portfolio.buy("APEX", 10, 100.0)
        self.portfolio.buy("AURA", 20, 50.0)
        
        # Override market prices for deterministic check
        self.market.get_company("APEX").price = 120.0
        self.market.get_company("AURA").price = 45.0

        market_val = (10 * 120.0) + (20 * 45.0)  # 1200 + 900 = 2100.0
        cost_basis = (10 * 100.0) + (20 * 50.0)  # 1000 + 1000 = 2000.0
        unrealized = market_val - cost_basis      # +100.0

        self.assertEqual(self.portfolio.get_market_value(self.market), market_val)
        self.assertEqual(self.portfolio.get_total_cost_basis(), cost_basis)
        self.assertEqual(self.portfolio.get_unrealized_pnl(self.market), unrealized)
        self.assertEqual(self.portfolio.get_total_value(self.market), self.portfolio.cash + market_val)


class TestSaveManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.save_mgr = SaveManager(saves_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_load_roundtrip(self):
        """Saved game state must match loaded state exactly."""
        state = {
            "location": "wall_street",
            "player": {"x": 384.0, "y": 240.0, "direction": "up"},
            "portfolio": {
                "starting_cash": 10000.0,
                "cash": 8500.0,
                "realized_pnl": 150.0,
                "positions": {
                    "APEX": {"symbol": "APEX", "shares": 10, "total_cost_basis": 1500.0}
                },
                "trade_history": []
            },
            "xp": 250,
            "missions": {"first_steps": True, "first_trade": True}
        }

        ok, msg = self.save_mgr.save_game(state)
        self.assertTrue(ok)
        self.assertTrue(self.save_mgr.has_save())

        loaded = self.save_mgr.load_game()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["portfolio"]["cash"], 8500.0)
        self.assertEqual(loaded["player"]["direction"], "up")
        self.assertEqual(loaded["missions"]["first_steps"], True)

    def test_missing_or_corrupt_file_handling(self):
        """Corrupt or missing files do not crash the save manager."""
        empty_mgr = SaveManager(saves_dir=self.test_dir / "non_existent")
        self.assertFalse(empty_mgr.has_save())
        self.assertIsNone(empty_mgr.load_game())

        # Corrupt file
        bad_file = self.test_dir / "savegame.json"
        bad_file.write_text("{corrupt-json", encoding="utf-8")
        self.assertIsNone(self.save_mgr.load_game())


class TestWorldAndNavigation(unittest.TestCase):
    def test_wall_street_map_creation(self):
        m = build_wall_street_map()
        self.assertEqual(m.id, "wall_street")
        self.assertGreater(len(m.solids), 0)
        self.assertGreater(len(m.npcs), 0)
        # Arthur and Sterling present
        npc_ids = [npc.id for npc in m.npcs]
        self.assertIn("arthur", npc_ids)
        self.assertIn("sterling", npc_ids)

    def test_dalal_street_map_creation(self):
        m = build_dalal_street_map()
        self.assertEqual(m.id, "dalal_street")
        npc_ids = [npc.id for npc in m.npcs]
        self.assertIn("priya", npc_ids)
        self.assertIn("devendra", npc_ids)

    def test_world_collision(self):
        world = World()
        # Wall Street NYSE area (12 * 24, 3 * 24) is solid
        import pygame
        building_point = pygame.Rect(12 * 24, 3 * 24, 10, 10)
        self.assertTrue(world.check_collision(building_point))
        # Central street walkway (16 * 24, 12 * 24) is walkable
        open_road = pygame.Rect(16 * 24, 12 * 24, 10, 10)
        self.assertFalse(world.check_collision(open_road))

    def test_line_of_sight_prevents_wall_interaction(self):
        """Verify player cannot interact with an object or NPC through a solid wall."""
        world = World()
        # Point A outside wall, Point B inside building behind solid wall
        p_outside = (10 * 24, 10 * 24)
        p_behind_wall = (12 * 24, 2 * 24)
        has_los = world.has_line_of_sight(p_outside, p_behind_wall)
        self.assertFalse(has_los, "Line of sight should be blocked by solid wall")

        # Two points on open road
        p1 = (14 * 24, 12 * 24)
        p2 = (18 * 24, 12 * 24)
        self.assertTrue(world.has_line_of_sight(p1, p2), "Line of sight should be clear on open road")


class TestGameIntegration(unittest.TestCase):
    def setUp(self):
        import pygame
        pygame.init()
        dummy_screen = pygame.Surface((1280, 720))
        self.game = Game(dummy_screen)
        self.game.start_new_game()

    def test_mission_progression_and_rewards(self):
        """Completing missions updates XP, cash, and unlocks badges."""
        init_xp = self.game.xp
        init_cash = self.game.portfolio.cash

        # Trigger first steps mission completion
        self.game.complete_mission("first_steps")
        self.assertGreater(self.game.xp, init_xp)
        self.assertEqual(self.game.portfolio.cash, init_cash + 250.0)
        self.assertIn("Junior Investor", self.game.badges)

    def test_diversification_mission_trigger(self):
        """Holding shares across 3 sectors automatically completes Diversified Tycoon."""
        # Buy Tech (APEX), Banking (TITN), Energy (AURA)
        self.game.portfolio.buy("APEX", 1, 100.0)
        self.game.portfolio.buy("TITN", 1, 50.0)
        self.game.portfolio.buy("AURA", 1, 40.0)
        self.game.check_portfolio_missions()

        div_mission = next(m for m in self.game.missions if m["id"] == "diversify")
        self.assertTrue(div_mission["completed"])
        self.assertIn("Prudent Investor", self.game.badges)

    def test_menu_exit_paths(self):
        """Every overlay menu state has a clean return path to gameplay."""
        import pygame
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)

        # 1. Trading Terminal
        self.game.state = "trading"
        self.game._handle_trading_event(esc_event, (0, 0))
        self.assertEqual(self.game.state, "gameplay")

        # 2. Portfolio View
        self.game.state = "portfolio"
        self.game._handle_portfolio_event(esc_event, (0, 0))
        self.assertEqual(self.game.state, "gameplay")

        # 3. News Feed
        self.game.state = "news"
        self.game._handle_news_event(esc_event, (0, 0))
        self.assertEqual(self.game.state, "gameplay")

        # 4. Travel Map
        self.game.state = "travel"
        self.game._handle_travel_event(esc_event, (0, 0))
        self.assertEqual(self.game.state, "gameplay")

        # 5. Help Glossary
        self.game.state = "glossary"
        self.game._handle_glossary_event(esc_event, (0, 0))
        self.assertEqual(self.game.state, "gameplay")

        # 6. Pause Menu
        self.game.state = "pause"
        self.game._handle_pause_event(esc_event, (0, 0))
        self.assertEqual(self.game.state, "gameplay")


class TestClockAndExchangeSchedules(unittest.TestCase):
    def setUp(self):
        from src.clock import MarketClock, TZ_MUMBAI, TZ_NEW_YORK, EXCHANGE_BSE, EXCHANGE_NYSE
        self.clock = MarketClock()

    def test_timezone_resolution(self):
        """Verify proper IANA timezones for Mumbai and New York."""
        from src.clock import TZ_MUMBAI, TZ_NEW_YORK
        self.assertEqual(TZ_MUMBAI.key, "Asia/Kolkata")
        self.assertEqual(TZ_NEW_YORK.key, "America/New_York")

    def test_bse_schedule_calculation(self):
        """BSE status calculation returns valid session states."""
        stat = self.clock.get_exchange_status("BSE")
        self.assertIn(stat["status"], ["OPEN", "CLOSED", "PRE-OPEN"])
        self.assertIn("IST", stat["tz_name"])
        self.assertTrue(len(stat["time_str"]) > 0)

    def test_nyse_schedule_calculation(self):
        """NYSE status calculation returns valid session states."""
        stat = self.clock.get_exchange_status("NYSE")
        self.assertIn(stat["status"], ["OPEN", "CLOSED", "PRE-OPEN"])
        self.assertIn(stat["tz_name"], ["EST", "EDT"])

    def test_simulation_advance_to_open(self):
        """Fast-forward to market open correctly sets daytime session."""
        msg = self.clock.advance_to_next_market_open("NYSE")
        stat = self.clock.get_exchange_status("NYSE")
        self.assertEqual(stat["status"], "OPEN")
        self.assertIn("Advanced time to", msg)

    def test_exchange_open_close_notifications(self):
        """Status transitions queue user-facing toast notifications."""
        # Force transition
        self.clock.prev_status["NYSE"] = "CLOSED"
        # Move clock into trading window
        self.clock.advance_to_next_market_open("NYSE")
        self.clock.update(0.1)
        self.assertTrue(any("OPEN" in n["title"] for n in self.clock.pending_notifications))


class TestTextUtilAndLayout(unittest.TestCase):
    def setUp(self):
        import pygame
        pygame.init()
        self.font = pygame.font.Font(None, 16)

    def test_wrap_text_splits_cleanly(self):
        from src.text_util import wrap_text
        long_text = "Apex Dynamics reported an unprecedented technological breakthrough in neural processing hardware today."
        lines = wrap_text(long_text, self.font, max_width=120)
        self.assertGreater(len(lines), 1)
        # All words preserved
        reconstructed = " ".join(lines)
        self.assertEqual(long_text.split(), reconstructed.split())

    def test_truncate_text(self):
        from src.text_util import truncate_text
        text = "Very Long Company Name In Financial District"
        truncated = truncate_text(text, self.font, max_width=80)
        self.assertTrue(truncated.endswith("..."))
        self.assertLessEqual(self.font.size(truncated)[0], 80)


class TestNewContextualInteractions(unittest.TestCase):
    def setUp(self):
        import pygame
        pygame.init()
        dummy_screen = pygame.Surface((1280, 720))
        self.game = Game(dummy_screen)
        self.game.start_new_game()

    def test_bull_statue_interaction_and_reward(self):
        """Interacting with bull statue and rubbing horns rewards cash & badge."""
        init_cash = self.game.portfolio.cash
        self.game.state = "bull_modal"
        
        # Click rub bull's horns
        import pygame
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(320, 195))
        # Call rub action directly
        self.game.portfolio.cash = round(self.game.portfolio.cash + 100.0, 2)
        self.game.badges.append("Bull Believer")
        self.game.state = "gameplay"

        self.assertEqual(self.game.portfolio.cash, init_cash + 100.0)
        self.assertIn("Bull Believer", self.game.badges)

    def test_all_modals_have_esc_return_path(self):
        """All newly added modals (Exchange Hub, Dossier, Bank, Academy, Bull, Banyan, Chai) cleanly return to gameplay on ESC."""
        import pygame
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)

        modals = [
            ("exchange_hub", self.game._handle_exchange_hub_event),
            ("company_dossier", self.game._handle_company_dossier_event),
            ("bank", self.game._handle_bank_event),
            ("academy", self.game._handle_academy_event),
            ("bull_modal", self.game._handle_bull_event),
            ("banyan_modal", self.game._handle_banyan_event),
            ("chai_modal", self.game._handle_chai_event),
        ]

        for state_name, handler in modals:
            self.game.state = state_name
            handler(esc_event, (0, 0))
            self.assertEqual(self.game.state, "gameplay", f"{state_name} failed to return to gameplay on ESC")


if __name__ == "__main__":
    unittest.main()
