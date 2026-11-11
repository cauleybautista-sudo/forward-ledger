"""Unit tests for Calico Football Tracker calibration, sanity gate, and modeling math."""

import unittest

from src.calibration import (
    apply_shrinkage,
    calculate_rps,
    empirical_bayes_mean,
    multiplicative_devig,
    neg_binom_over_prob,
    sanity_gate,
)
from src.intl_data import american_to_decimal, normalize_team_name
from src.sync_live_odds import evaluate_dixon_coles_grid, invert_market_lambdas


class TestInternationalModel(unittest.TestCase):
    def test_multiplicative_devig_sums_to_one(self):
        probs = multiplicative_devig([1.95, 3.40, 4.10])
        self.assertAlmostEqual(sum(probs), 1.0, places=6)
        self.assertGreater(probs[0], probs[1])

    def test_rps_scoring(self):
        self.assertEqual(calculate_rps((1.0, 0.0, 0.0), 0), 0.0)
        self.assertLess(calculate_rps((0.70, 0.20, 0.10), 0), calculate_rps((0.20, 0.30, 0.50), 0))

    def test_negative_binomial_overdispersion(self):
        p_low_var = neg_binom_over_prob(10.0, variance=10.5, line=9.5)
        p_high_var = neg_binom_over_prob(10.0, variance=22.0, line=9.5)
        self.assertTrue(0.01 <= p_low_var <= 0.99)
        self.assertTrue(0.01 <= p_high_var <= 0.99)
        self.assertNotAlmostEqual(p_low_var, p_high_var, places=3)

    def test_sanity_gate_rejects_flat_slate_and_unmapped_teams(self):
        flat_slate = [
            {
                "id": str(i),
                "fixture": f"Team{i} vs Opp{i}",
                "p_h": 0.50,
                "p_d": 0.25,
                "p_a": 0.25,
                "unmapped_team": (i == 0),
                "result_pick": {"prob": 0.50, "is_pass": False},
                "goal_total_pick": {"prob": 0.60, "is_pass": False},
                "btts_pick": {"prob": 0.55, "is_pass": False},
                "corner_pick": {"prob": 0.58, "is_pass": False},
            }
            for i in range(4)
        ]
        issues = sanity_gate(flat_slate, strict_teams=True)
        self.assertTrue(any("flat/constant" in msg for msg in issues))
        self.assertTrue(any("Unmapped international teams" in msg for msg in issues))

    def test_team_normalization_and_american_odds(self):
        self.assertEqual(normalize_team_name("Czechia"), "Czech Republic")
        self.assertEqual(normalize_team_name("Türkiye"), "Turkey")
        self.assertEqual(normalize_team_name("Bosnia & Herzegovina"), "Bosnia and Herzegovina")
        self.assertEqual(normalize_team_name("Korea Republic"), "South Korea")
        self.assertEqual(american_to_decimal("+135"), 2.35)
        self.assertAlmostEqual(american_to_decimal("-200"), 1.5, places=3)
        self.assertEqual(american_to_decimal("EVEN"), 2.0)

    def test_market_lambda_inversion_consistency(self):
        dc_target = evaluate_dixon_coles_grid(2.10, 0.85)
        lam, mu = invert_market_lambdas(
            dc_target["p_h"],
            dc_target["p_d"],
            dc_target["p_a"],
            dc_target["p_over"],
            total_line=2.5,
        )
        self.assertAlmostEqual(lam, 2.10, delta=0.15)
        self.assertAlmostEqual(mu, 0.85, delta=0.15)

    def test_empirical_bayes_and_shrinkage(self):
        self.assertLess(empirical_bayes_mean(8.0, 1, 4.75, 4.0), 6.0)
        self.assertLess(apply_shrinkage(0.90, 0.50, 0.90), 0.90)


if __name__ == "__main__":
    unittest.main()
