"""StatsGate: catch impossible or inconsistent reported statistics.

Three deterministic checks, each a real, published technique used by
research-integrity investigators to flag likely-fabricated or erroneous
numbers in papers:

  GRIM      -- a reported mean of N integer-scored items must be reachable
               as (some integer sum) / N. If no integer sum rounds to the
               reported mean, the mean is IMPOSSIBLE.
  SD bounds -- for a fixed sum (implied by the reported mean and N) and a
               bounded item scale [lo, hi], the achievable standard
               deviation has a real minimum and maximum. A reported SD
               outside that range is IMPOSSIBLE. (The maximum is a
               continuous-relaxation upper bound -- see docs/LIMITATIONS.md;
               it can under-flag but never over-flags.)
  P-VALUE   -- recomputes the two-tailed p-value for a reported t-statistic
               and degrees of freedom via the exact Student's t CDF
               (regularized incomplete beta function) and compares it to
               the reported p-value.

StatsGate checks arithmetic/statistical CONSISTENCY only. It does not detect
fabrication that happens to be internally consistent, and it does not
replace a real data audit or a statistician's review.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

CONSISTENT = "CONSISTENT"
IMPOSSIBLE = "IMPOSSIBLE"
NOT_RULED_OUT = "NOT_RULED_OUT"   # SD case: inside the achievable range, not proven to exist
MALFORMED = "MALFORMED_INPUT"

PUBLIC_WORDING = ("StatsGate checks arithmetic/statistical consistency of reported "
                  "numbers only. It does not detect fabrication that happens to be "
                  "internally consistent, and it does not replace a real data audit.")


@dataclass
class StatsResult:
    check: str
    status: str
    input: dict = field(default_factory=dict)
    reason: str = ""
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tool": "statsgate", "check": self.check, "status": self.status,
            "input": self.input, "reason": self.reason, "detail": self.detail,
            "public_wording": PUBLIC_WORDING,
        }


# =============================================================== GRIM test
def _decimals_in(s: str) -> int:
    return len(s.split(".", 1)[1]) if "." in s else 0


def check_grim(mean_str: str, n: int) -> StatsResult:
    """GRIM: is a reported mean of N integer-scored items arithmetically reachable?"""
    inp = {"mean": mean_str, "n": n}
    if n <= 0:
        return StatsResult("grim", MALFORMED, inp, reason="n must be a positive integer")
    try:
        reported = float(mean_str)
    except ValueError:
        return StatsResult("grim", MALFORMED, inp, reason=f"'{mean_str}' is not a number")
    decimals = _decimals_in(mean_str)
    center = round(reported * n)
    window = 3  # rounding can only shift the nearest integer sum by ~1; padded for safety
    for s in range(max(0, center - window), center + window + 1):
        if round(s / n, decimals) == reported:
            return StatsResult("grim", CONSISTENT, inp,
                               reason=f"reachable: integer sum {s} / {n} rounds to {mean_str}",
                               detail={"matching_sum": s})
    return StatsResult("grim", IMPOSSIBLE, inp,
                       reason=f"no integer sum over {n} items rounds to {mean_str} at "
                              f"{decimals} decimal place(s) -- this mean cannot come from "
                              f"{n} integer-scored observations",
                       detail={"decimals": decimals})


# ======================================================== SD achievable-range
def _min_sum_squares_integer(n: int, s: int) -> float:
    """Exact minimum sum-of-squares for n integers summing to s (equal-as-possible split)."""
    q, r = divmod(s, n)
    return r * (q + 1) ** 2 + (n - r) * q ** 2


def _max_sum_squares_relaxed(n: int, s: float, lo: float, hi: float) -> Optional[float]:
    """Upper bound on sum-of-squares for n REAL values in [lo, hi] summing to s.
    Convexity argument: the maximizer of a convex objective (sum of squares) over a
    box-constrained affine slice has at most one coordinate strictly inside (lo, hi);
    the rest sit at a bound. We search over how many sit at `hi` vs `lo` and solve
    for the one patch value. This is a real, deterministic upper bound (see
    docs/LIMITATIONS.md for why it's an upper bound on the true integer-constrained
    maximum, not the exact integer optimum)."""
    if s < n * lo - 1e-9 or s > n * hi + 1e-9:
        return None  # sum itself infeasible given the bounds
    best = None
    for k in range(0, n + 1):
        # Variant A: k at hi, one patch among the (n-k) "lo" slots, rest at lo.
        if n - k >= 1:
            p = s - k * hi - (n - k - 1) * lo
            if lo - 1e-9 <= p <= hi + 1e-9:
                val = k * hi ** 2 + (n - k - 1) * lo ** 2 + p ** 2
                best = val if best is None else max(best, val)
        # Variant B: (k-1) at hi, one patch among the "hi" slots, rest at lo.
        if k >= 1:
            p = s - (k - 1) * hi - (n - k) * lo
            if lo - 1e-9 <= p <= hi + 1e-9:
                val = (k - 1) * hi ** 2 + (n - k) * lo ** 2 + p ** 2
                best = val if best is None else max(best, val)
    return best


def check_sd_range(mean_str: str, sd_str: str, n: int, item_min: float, item_max: float) -> StatsResult:
    """Is a reported SD achievable for N integer items in [item_min, item_max]
    with the given mean? Flags IMPOSSIBLE only when provably unreachable."""
    inp = {"mean": mean_str, "sd": sd_str, "n": n, "item_min": item_min, "item_max": item_max}
    if n <= 1:
        return StatsResult("sd_range", MALFORMED, inp, reason="n must be >= 2 for an SD to be defined")
    if item_max <= item_min:
        return StatsResult("sd_range", MALFORMED, inp, reason="item_max must be > item_min")
    try:
        mean, sd = float(mean_str), float(sd_str)
    except ValueError:
        return StatsResult("sd_range", MALFORMED, inp, reason="mean/sd must be numbers")
    if sd < 0:
        return StatsResult("sd_range", IMPOSSIBLE, inp, reason="a standard deviation cannot be negative")

    s = round(mean * n)
    min_ss = _min_sum_squares_integer(n, s)
    sd_min_sq = min_ss / n - mean ** 2
    sd_min = math.sqrt(max(0.0, sd_min_sq))

    max_ss = _max_sum_squares_relaxed(n, s, item_min, item_max)
    if max_ss is None:
        return StatsResult("sd_range", IMPOSSIBLE, inp,
                           reason=f"mean {mean_str} over {n} items is not reachable within "
                                  f"[{item_min}, {item_max}] at all")
    sd_max_sq = max_ss / n - mean ** 2
    sd_max = math.sqrt(max(0.0, sd_max_sq))

    detail = {"sd_min": round(sd_min, 6), "sd_max_upper_bound": round(sd_max, 6)}
    if sd < sd_min - 1e-6 or sd > sd_max + 1e-6:
        return StatsResult("sd_range", IMPOSSIBLE, inp, detail=detail,
                           reason=f"reported SD {sd_str} is outside the achievable range "
                                  f"[{detail['sd_min']}, {detail['sd_max_upper_bound']}] "
                                  f"for mean {mean_str}, n={n}, items in [{item_min}, {item_max}]")
    return StatsResult("sd_range", NOT_RULED_OUT, inp, detail=detail,
                       reason=f"reported SD {sd_str} falls within the achievable range "
                              f"[{detail['sd_min']}, {detail['sd_max_upper_bound']}] -- "
                              f"not disproven, not proven to exist")


# ================================================== t-test p-value consistency
def _betacf(a: float, b: float, x: float, max_iter: int = 200, eps: float = 3e-12) -> float:
    """Continued fraction for the incomplete beta function (Lentz's algorithm)."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    """I_x(a, b), the regularized incomplete beta function, x in [0, 1]."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(ln_beta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_two_tailed_pvalue(t: float, df: float) -> float:
    """Exact two-tailed p-value for a Student's t statistic with `df` degrees
    of freedom, via the regularized incomplete beta function."""
    t = abs(t)
    x = df / (df + t * t)
    return _regularized_incomplete_beta(df / 2.0, 0.5, x)


def check_t_pvalue(t_str: str, df_str: str, p_str: str, tol: float = 0.005) -> StatsResult:
    """statcheck-style check: does the reported p-value match what the t-statistic
    and df actually imply (two-tailed)?"""
    inp = {"t": t_str, "df": df_str, "p": p_str}
    try:
        t, df, p_reported = float(t_str), float(df_str), float(p_str)
    except ValueError:
        return StatsResult("t_pvalue", MALFORMED, inp, reason="t/df/p must be numbers")
    if df <= 0:
        return StatsResult("t_pvalue", MALFORMED, inp, reason="df must be positive")
    if not (0.0 <= p_reported <= 1.0):
        return StatsResult("t_pvalue", IMPOSSIBLE, inp, reason="a p-value must be in [0, 1]")
    p_computed = t_two_tailed_pvalue(t, df)
    detail = {"p_computed": round(p_computed, 6)}
    if abs(p_computed - p_reported) > tol:
        return StatsResult("t_pvalue", IMPOSSIBLE, inp, detail=detail,
                           reason=f"t({df_str})={t_str} implies two-tailed p ~= "
                                  f"{detail['p_computed']}, not {p_str} "
                                  f"(difference {abs(p_computed - p_reported):.4f} > tolerance {tol})")
    return StatsResult("t_pvalue", CONSISTENT, inp, detail=detail,
                       reason=f"t({df_str})={t_str} implies p ~= {detail['p_computed']}, "
                              f"matching reported {p_str} within tolerance")
