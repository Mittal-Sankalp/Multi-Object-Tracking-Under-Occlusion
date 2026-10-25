"""
MarketQuest - Automated Tests for Stock Return Mathematical Model
Verifies return decomposition, decimal unit consistency, exact reconciliation,
bounds and clamping, non-negative price enforcement, reproducible seeding,
and sample standard deviation historical volatility.
"""

import unittest
import math
from src.market import MarketEngine, Company, ReturnBreakdown, MarketEvent, WEIGHT_FUNDAMENTALS
from config import MIN_STOCK_PRICE, MAX_STOCK_PRICE


class TestStockReturnFormula(unittest.TestCase):
    def setUp(self):
        self.market = MarketEngine(seed=42)

    def test_reconciliation_exact_sum(self):
        """Test that F + N + P + M + H + epsilon == raw_return exactly in decimal units."""
        self.market.tick()
        for comp in self.market.get_all_companies():
            b = comp.latest_breakdown
            self.assertIsNotNone(b)
            calculated_sum = b.fundamental + b.news + b.political + b.market_sector + b.historical_momentum + b.noise_luck
            self.assertAlmostEqual(calculated_sum, b.raw_return, places=7,
                                  msg=f"Breakdown does not reconcile for {comp.symbol}")

    def test_clamping_and_circuit_breakers(self):
        """Test that return is bounded by lower_bound and upper_bound."""
        for comp in self.market.get_all_companies():
            comp.lower_bound = -0.05
            comp.upper_bound = 0.05

        self.market.tick()
        for comp in self.market.get_all_companies():
            b = comp.latest_breakdown
            self.assertGreaterEqual(b.clamped_return, comp.lower_bound - 1e-9)
            self.assertLessEqual(b.clamped_return, comp.upper_bound + 1e-9)
            if b.raw_return > comp.upper_bound or b.raw_return < comp.lower_bound:
                self.assertTrue(b.was_clamped)

    def test_price_remains_positive_and_within_bounds(self):
        """Verify that prices can never fall below MIN_STOCK_PRICE."""
        comp = self.market.get_company("CHAI")
        self.assertIsNotNone(comp)
        comp.price = 1.05
        # Simulate extreme downward shock
        comp.lower_bound = -0.99
        self.market.set_macro_policy("none", -0.5, interest_rate_delta=0.5)

        for _ in range(20):
            self.market.tick()
            self.assertGreaterEqual(comp.price, MIN_STOCK_PRICE)
            self.assertLessEqual(comp.price, MAX_STOCK_PRICE)

    def test_seeded_simulation_is_reproducible(self):
        """Verify that identical seeds produce identical return breakdowns and price sequences."""
        engine_a = MarketEngine(seed=12345)
        engine_b = MarketEngine(seed=12345)

        prices_a = []
        prices_b = []
        for _ in range(10):
            engine_a.tick()
            engine_b.tick()
            prices_a.append({s: c.price for s, c in engine_a.companies.items()})
            prices_b.append({s: c.price for s, c in engine_b.companies.items()})

        self.assertEqual(prices_a, prices_b)

    def test_rendering_and_getters_do_not_advance_prices(self):
        """Verify that inspecting breakdowns or getting companies does not change prices."""
        initial_prices = {s: c.price for s, c in self.market.companies.items()}
        for _ in range(50):
            for s in self.market.companies:
                _ = self.market.get_company(s)
                _ = self.market.get_breakdown(s)
                _ = self.market.get_all_companies()

        current_prices = {s: c.price for s, c in self.market.companies.items()}
        self.assertEqual(initial_prices, current_prices)

    def test_active_event_decay(self):
        """Verify that breaking news decays over subsequent simulation steps."""
        ev = MarketEvent(
            id="TEST_SHOCK",
            headline="Test Surge",
            explanation="Test",
            affected_type="company",
            target="APEX",
            impact=0.10,
            duration_days=3,
            education="Test event"
        )
        self.market.apply_event(ev)
        self.assertEqual(len(self.market.active_events), 1)

        # Step 1 tick
        self.market.tick()
        b1 = self.market.get_breakdown("APEX")
        self.assertIsNotNone(b1)
        news1 = b1.news

        # Step 2 tick
        self.market.tick()
        b2 = self.market.get_breakdown("APEX")
        self.assertIsNotNone(b2)
        news2 = b2.news

        # Due to decay factor (0.70^age), news2 should be smaller in magnitude than news1
        self.assertLess(abs(news2), abs(news1))

    def test_political_macro_policy_targeting(self):
        """Verify clean energy policy benefits AURA while traditional or unaffected companies receive 0."""
        self.market.set_macro_policy("clean_energy", magnitude=0.08)
        self.market.tick()

        b_aura = self.market.get_breakdown("AURA")
        b_titn = self.market.get_breakdown("TITN")

        self.assertIsNotNone(b_aura)
        self.assertIsNotNone(b_titn)
        # AURA has positive policy sensitivity to clean_energy (0.65), TITN has 0.0
        self.assertGreater(b_aura.political, 0.0)
        self.assertEqual(b_titn.political, 0.0)

    def test_sample_standard_deviation_volatility(self):
        """Verify sample standard deviation matches mathematical definition."""
        comp = self.market.get_company("TITN")
        self.assertIsNotNone(comp)
        # Populate controlled price sequence
        comp.price_history = [100.0, 102.0, 101.0, 103.0, 102.0]
        # returns:
        # r1 = (102-100)/100 = 0.02
        # r2 = (101-102)/102 = -0.0098039
        # r3 = (103-101)/101 = 0.01980198
        # r4 = (102-103)/103 = -0.0097087
        returns = [
            (102.0 - 100.0) / 100.0,
            (101.0 - 102.0) / 102.0,
            (103.0 - 101.0) / 101.0,
            (102.0 - 103.0) / 103.0,
        ]
        mean_r = sum(returns) / len(returns)
        expected_std = math.sqrt(sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1))

        self.assertAlmostEqual(comp.step_volatility, expected_std, places=5)
        self.assertGreater(comp.historical_volatility_pct, 0.0)


if __name__ == "__main__":
    unittest.main()
