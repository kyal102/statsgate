"""CLI:
    python -m statsgate grim 3.45 25
    python -m statsgate sdrange 2.50 0.50 4 1 4
    python -m statsgate tpvalue 2.0 20 0.06
    python -m statsgate --demo
    python -m statsgate --json grim 3.45 25
"""
import argparse
import json
import sys

from .gate import check_grim, check_sd_range, check_t_pvalue

DEMO = [
    ("grim", ["3.44", "25"]),
    ("grim", ["5.94", "25"]),
    ("sdrange", ["2.50", "0.50", "4", "1", "4"]),
    ("sdrange", ["2.50", "5.00", "4", "1", "4"]),
    ("tpvalue", ["2.0", "20", "0.06"]),
    ("tpvalue", ["2.0", "20", "0.50"]),
]


def _print(res, as_json):
    if as_json:
        print(json.dumps(res.to_dict(), indent=2))
        return
    print(f"[{res.check}] {res.input}")
    print(f"  -> {res.status}")
    if res.reason:
        print(f"     {res.reason}")


def _run(check, args):
    if check == "grim":
        return check_grim(args[0], int(args[1]))
    if check == "sdrange":
        return check_sd_range(args[0], args[1], int(args[2]), float(args[3]), float(args[4]))
    if check == "tpvalue":
        return check_t_pvalue(args[0], args[1], args[2])
    raise SystemExit(f"unknown check '{check}' (use: grim, sdrange, tpvalue)")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="statsgate",
        description="Check whether a reported statistic is arithmetically possible.")
    ap.add_argument("check", nargs="?", help="grim | sdrange | tpvalue")
    ap.add_argument("args", nargs="*", help="check-specific positional arguments")
    ap.add_argument("--demo", action="store_true", help="run built-in examples")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    a = ap.parse_args(argv)

    if a.demo:
        for check, args in DEMO:
            _print(_run(check, args), a.json)
            if not a.json:
                print()
        return 0

    if not a.check:
        ap.print_help()
        return 2

    res = _run(a.check, a.args)
    _print(res, a.json)
    return 1 if res.status == "IMPOSSIBLE" else 0


if __name__ == "__main__":
    sys.exit(main())
