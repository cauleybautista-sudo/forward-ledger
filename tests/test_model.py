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
from src.sync_live_odds import (
    evaluate_dixon_coles_grid,
    invert_corners_mu,
    invert_market_lambdas,
    resolve_cross_market_contradictions,
    select_coherent_scores,
)
from src.v2_ledger import _grade_pick


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

    def test_invert_corners_mu_consistency(self):
        for target_p in (0.35, 0.50, 0.65):
            mu = invert_corners_mu(target_p, line=9.5)
            recovered = neg_binom_over_prob(mu, 2.0 * mu, 9.5)
            self.assertAlmostEqual(recovered, target_p, delta=0.01)

    def test_v2_ledger_grade_pick(self):
        # Result market
        self.assertEqual(
            _grade_pick({"selection": "Home Win"}, True, "result")["status"], "HIT"
        )
        self.assertEqual(
            _grade_pick({"selection": "Away Win"}, False, "result")["status"], "MISS"
        )
        # Goals Over/Under market
        self.assertEqual(
            _grade_pick({"selection": "Over 2.5 Goals"}, True, "goals")["status"], "HIT"
        )
        self.assertEqual(
            _grade_pick({"selection": "Under 2.5 Goals"}, True, "goals")["status"], "MISS"
        )
        # BTTS market
        self.assertEqual(
            _grade_pick({"selection": "BTTS Yes"}, True, "btts")["status"], "HIT"
        )
        self.assertEqual(
            _grade_pick({"selection": "BTTS No"}, True, "btts")["status"], "MISS"
        )
        # Corners market
        self.assertEqual(
            _grade_pick({"selection": "Over 9.5 Corners"}, True, "corners")["status"],
            "HIT",
        )
        self.assertEqual(
            _grade_pick({"selection": "Under 9.5 Corners"}, False, "corners")["status"],
            "HIT",
        )
        # VOID cases: is_pass=True or NO PICK
        self.assertEqual(
            _grade_pick({"selection": "Over 9.5 Corners", "is_pass": True}, True, "corners")["status"],
            "VOID",
        )
        self.assertEqual(
            _grade_pick({"pick": "NO PICK"}, False, "btts")["status"],
            "VOID",
        )

    def test_coherent_score_selection_matches_active_picks(self):
        # Case where global mode (2-0 or 1-1) disagrees with Over 2.5 + Home Win + BTTS Yes
        model = evaluate_dixon_coles_grid(2.05, 1.05, rho=-0.08)
        rp = {"selection": "Home Win", "prob": 0.60, "is_pass": False}
        gp = {"selection": "Over 2.5", "prob": 0.62, "is_pass": False}
        bp = {"selection": "BTTS Yes", "prob": 0.56, "is_pass": False}
        top_sc, _, sec_sc, _ = select_coherent_scores(model["scores"], rp, gp, bp)
        self.assertGreater(top_sc[0], top_sc[1])
        self.assertGreaterEqual(top_sc[0] + top_sc[1], 3)
        self.assertTrue(top_sc[0] > 0 and top_sc[1] > 0)
        self.assertNotEqual(top_sc, sec_sc)

    def test_cross_market_contradiction_resolver_passes_weakest_leg(self):
        model = evaluate_dixon_coles_grid(1.35, 0.90, rho=-0.08)
        # Impossible trio: Home Win (0.58) + Under 2.5 (0.57) + BTTS Yes (0.53)
        rp = {"selection": "Home Win", "prob": 0.58, "is_pass": False}
        gp = {"selection": "Under 2.5", "prob": 0.57, "is_pass": False}
        bp = {"selection": "BTTS Yes", "prob": 0.53, "is_pass": False}
        resolve_cross_market_contradictions(model["scores"], rp, gp, bp)
        self.assertFalse(rp["is_pass"])
        self.assertFalse(gp["is_pass"])
        self.assertTrue(bp["is_pass"])
        self.assertEqual(bp["selection"], "NO PICK (PASS)")

    def test_sanity_gate_rejects_pick_contradictions(self):
        bad_slate = [
            {
                "id": "bad-1",
                "fixture": "England vs Croatia",
                "p_h": 0.76,
                "p_d": 0.15,
                "p_a": 0.09,
                "pred_score": "2-0",
                "result_pick": {"selection": "Home Win", "prob": 0.76, "is_pass": False},
                "goal_total_pick": {"selection": "Over 2.5", "prob": 0.65, "is_pass": False},
                "btts_pick": {"selection": "NO PICK (PASS)", "prob": 0.50, "is_pass": True},
                "corner_pick": {"selection": "Corners Under 9.5", "prob": 0.54, "is_pass": False},
                "real_goal_stats": {"expectedXg": 2.9},
                "real_corner_stats": {"expectedCorners": 9.8},
            }
        ]
        issues = sanity_gate(bad_slate)
        self.assertTrue(any("pred_score 2-0 contradicts Over 2.5" in msg for msg in issues))
        self.assertTrue(any("expectedCorners 9.8 contradicts Corners Under 9.5" in msg for msg in issues))


if __name__ == "__main__":
    unittest.main()
