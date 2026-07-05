"""StatsGate -- catch impossible or inconsistent reported statistics.

StatsGate checks arithmetic/statistical consistency only. It does not detect
fabrication that happens to be internally consistent, and it does not
replace a real data audit or a statistician's review.
"""
from .gate import (
    StatsResult, CONSISTENT, IMPOSSIBLE, NOT_RULED_OUT, MALFORMED,
    check_grim, check_sd_range, check_t_pvalue, t_two_tailed_pvalue,
)

__version__ = "0.1.0"
__all__ = [
    "StatsResult", "CONSISTENT", "IMPOSSIBLE", "NOT_RULED_OUT", "MALFORMED",
    "check_grim", "check_sd_range", "check_t_pvalue", "t_two_tailed_pvalue",
]
