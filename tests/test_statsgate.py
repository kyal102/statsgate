import unittest

from statsgate import check_grim, check_sd_range, check_t_pvalue, CONSISTENT, IMPOSSIBLE, NOT_RULED_OUT
from statsgate.gate import t_two_tailed_pvalue


class TestGrim(unittest.TestCase):
    def test_consistent_exact(self):
        self.assertEqual(check_grim("3.00", 10).status, CONSISTENT)

    def test_consistent_repeating_decimal(self):
        # 10 / 3 = 3.3333... rounds to 3.33
        self.assertEqual(check_grim("3.33", 3).status, CONSISTENT)

    def test_impossible(self):
        # no integer sum over 3 items rounds to 3.35 at 2dp
        self.assertEqual(check_grim("3.35", 3).status, IMPOSSIBLE)

    def test_impossible_classic_style(self):
        self.assertEqual(check_grim("5.94", 25).status, IMPOSSIBLE)

    def test_malformed_n(self):
        self.assertEqual(check_grim("3.00", 0).status, "MALFORMED_INPUT")

    def test_malformed_mean(self):
        self.assertEqual(check_grim("not-a-number", 10).status, "MALFORMED_INPUT")


class TestSdRange(unittest.TestCase):
    def test_equal_split_is_the_true_minimum(self):
        # n=4, sum=10 -> [3,3,2,2], mean 2.5, sd = sqrt(0.25) = 0.5 exactly
        r = check_sd_range("2.50", "0.50", 4, 1, 4)
        self.assertEqual(r.detail["sd_min"], 0.5)
        self.assertEqual(r.status, NOT_RULED_OUT)

    def test_sd_too_large_is_impossible(self):
        r = check_sd_range("2.50", "5.00", 4, 1, 4)
        self.assertEqual(r.status, IMPOSSIBLE)

    def test_sd_zero_impossible_when_mean_needs_variation(self):
        # mean 2.5 with 4 integers in [1,4] cannot be a constant sequence
        r = check_sd_range("2.50", "0.00", 4, 1, 4)
        self.assertEqual(r.status, IMPOSSIBLE)

    def test_sd_zero_possible_when_mean_is_integer(self):
        # mean 3 with 4 items in [1,4]: [3,3,3,3] has sd=0
        r = check_sd_range("3.00", "0.00", 4, 1, 4)
        self.assertEqual(r.status, NOT_RULED_OUT)

    def test_negative_sd_impossible(self):
        r = check_sd_range("2.50", "-1.00", 4, 1, 4)
        self.assertEqual(r.status, IMPOSSIBLE)

    def test_malformed_bounds(self):
        r = check_sd_range("2.50", "0.50", 4, 4, 1)
        self.assertEqual(r.status, "MALFORMED_INPUT")


class TestTPvalue(unittest.TestCase):
    def test_known_critical_value_05(self):
        # t=2.086, df=20 is the textbook two-tailed alpha=.05 critical value
        p = t_two_tailed_pvalue(2.086, 20)
        self.assertAlmostEqual(p, 0.05, places=2)

    def test_known_critical_value_01(self):
        # t=2.845, df=20 is close to the textbook two-tailed alpha=.01 critical value
        p = t_two_tailed_pvalue(2.845, 20)
        self.assertAlmostEqual(p, 0.01, places=2)

    def test_large_df_approaches_normal(self):
        # t=1.96 at very large df should match the normal-distribution two-tailed p=.05
        p = t_two_tailed_pvalue(1.96, 1_000_000)
        self.assertAlmostEqual(p, 0.05, places=2)

    def test_consistent_report(self):
        r = check_t_pvalue("2.0", "20", "0.06")
        self.assertEqual(r.status, CONSISTENT)

    def test_inconsistent_report(self):
        r = check_t_pvalue("2.0", "20", "0.50")
        self.assertEqual(r.status, IMPOSSIBLE)

    def test_out_of_range_p_impossible(self):
        r = check_t_pvalue("2.0", "20", "1.5")
        self.assertEqual(r.status, IMPOSSIBLE)

    def test_malformed_df(self):
        r = check_t_pvalue("2.0", "-5", "0.05")
        self.assertEqual(r.status, "MALFORMED_INPUT")


if __name__ == "__main__":
    unittest.main()
