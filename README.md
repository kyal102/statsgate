# StatsGate

[![CI](https://github.com/kyal102/statsgate/actions/workflows/ci.yml/badge.svg)](https://github.com/kyal102/statsgate/actions/workflows/ci.yml) ![python](https://img.shields.io/badge/python-3.9%2B-blue) ![license](https://img.shields.io/badge/license-MIT-green) ![deps](https://img.shields.io/badge/dependencies-stdlib--only-blue) ![tests](https://img.shields.io/badge/tests-19%20passing-brightgreen)

**Catch impossible or inconsistent reported statistics before they become confident AI claims.**

```bash
python -m statsgate grim 5.94 25
```
```text
[grim] {'mean': '5.94', 'n': 25}
  -> IMPOSSIBLE
     no integer sum over 25 items rounds to 5.94 at 2 decimal place(s) -- this mean cannot come from 25 integer-scored observations
```

A reported mean, standard deviation, and sample size have to be arithmetically consistent with each other. A t-statistic and its degrees of freedom imply exactly one p-value. StatsGate checks whether the numbers in front of you actually add up — the same class of technique real research-integrity investigators use to catch impossible or fabricated statistics in published papers, reimplemented from scratch as a small, dependency-free library and CLI.

> **StatsGate checks arithmetic/statistical consistency only. It does not detect fabrication that happens to be internally consistent, and it does not replace a real data audit or a statistician's review.**

## Origin — this is not new research

The three checks below are re-implementations of published, peer-reviewed techniques, not novel methods:

| Check | Original technique | Source |
|---|---|---|
| GRIM | Granularity-Related Inconsistency of Means | Brown & Heathers (2017), *Social Psychological and Personality Science* |
| SD range | SPRITE-style sample reconstruction bounds | Heathers, Anaya, van der Zee & Brown (2018) |
| t/p-value consistency | `statcheck`-style recomputation | Nuijten, Hartgerink, van Assen, Epskamp & Wicherts (2016) |

StatsGate's contribution is a correct, tested, **zero-dependency** implementation covering all three in one small library — most existing open implementations are R packages or require `scipy`. If you need the full, iterative SPRITE search (which can *construct* a matching dataset, not just bound its SD) or one-tailed/F/chi-square tests, the original R tools remain the more complete choice for now — see [Roadmap](#roadmap).

## Install / run

No dependencies — pure Python standard library.

```bash
python -m statsgate grim 3.44 25                    # GRIM: is this mean reachable?
python -m statsgate sdrange 2.50 0.50 4 1 4          # is this SD achievable for a 1-4 scale?
python -m statsgate tpvalue 2.0 20 0.06              # does t(20)=2.0 really imply p=.06?
python -m statsgate --demo
python -m statsgate --json grim 5.94 25              # machine-readable output
```

Exit code is `1` for a flagged `IMPOSSIBLE` result on a single check (handy in scripts/CI).

## What it does

Three checks, each returning `CONSISTENT`, `IMPOSSIBLE`, `NOT_RULED_OUT`, or `MALFORMED_INPUT` — never a bare true/false, always with the reasoning:

- **GRIM** — a mean of N integer-scored items (e.g. a Likert scale, a count) must equal *some* integer sum divided by N, rounded to the reported number of decimal places. If no integer sum reaches it, the mean is `IMPOSSIBLE`.
- **SD range** — for a fixed sum (implied by the mean and N) and a bounded item scale `[lo, hi]`, the achievable standard deviation has a real minimum and maximum. A reported SD outside `[min, max]` is `IMPOSSIBLE`. The minimum is the exact integer optimum; the maximum is a proven upper bound via a continuous relaxation (see [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for exactly why, and why that makes this check able to under-flag but never wrongly over-flag).
- **t/p-value consistency** — recomputes the exact two-tailed p-value for a reported t-statistic and degrees of freedom, via a from-scratch regularized incomplete beta function (Lentz's continued fraction), and compares it to what was reported.

Every numerical routine is checked against textbook critical-value tables in [`tests/`](tests/test_statsgate.py) (e.g. t=2.086, df=20 → p≈0.05; t=2.845, df=20 → p≈0.01) — not just "looks about right."

See [docs/EXAMPLES.md](docs/EXAMPLES.md) for every example in this README as verified CLI output.

## Worked example: auditing a claim

```text
Paper excerpt: "Participants (N=25) rated their agreement on a 7-point scale
(M = 5.94, SD = 1.2), t(24) = 3.10, p = .03."
```

```bash
$ python -m statsgate grim 5.94 25
[grim] {'mean': '5.94', 'n': 25}
  -> IMPOSSIBLE
     no integer sum over 25 items rounds to 5.94 at 2 decimal place(s)

$ python -m statsgate tpvalue 3.10 24 0.03
[t_pvalue] {'t': '3.10', 'df': '24', 'p': '0.03'}
  -> IMPOSSIBLE
     t(24)=3.10 implies two-tailed p ~= 0.004888, not 0.03 (difference 0.0251 > tolerance 0.005)
```

Two independent arithmetic checks on the same reported paragraph both fail. Neither number needs the raw data to check — the inconsistency is visible from the summary statistics alone.

## What StatsGate can honestly claim — and can't

**Can claim:**
- A flagged `IMPOSSIBLE` result is a real mathematical impossibility, not a heuristic guess — every check here is a closed-form or provably-bounded calculation, verified against known reference values.
- `NOT_RULED_OUT` never claims a dataset exists, only that one isn't ruled out by this check.

**Cannot claim (yet):**
- That a `CONSISTENT` or `NOT_RULED_OUT` result means the data is real. A carefully fabricated dataset can pass every check here.
- Full SPRITE-style dataset reconstruction (proving a matching raw dataset *exists*, not just bounding its SD).
- F-tests, chi-square tests, one-tailed tests, or ANOVA-style reporting (t-tests only, for now).
- Anything about the paper's methodology, sampling, or conclusions — this is arithmetic consistency, not peer review.

## Project structure

```
statsgate/
├── statsgate/
│   ├── __init__.py        # public API
│   ├── __main__.py         # CLI entry point
│   └── gate.py             # GRIM, SD-range, and t/p-value checks
├── tests/
│   └── test_statsgate.py   # 19 tests, incl. textbook critical-value checks
├── docs/
│   ├── EXAMPLES.md          # verified CLI output for every example
│   └── LIMITATIONS.md       # exact scope, and why the SD bound is one-directional
├── .github/workflows/ci.yml
├── pyproject.toml
├── LICENSE
└── README.md
```

## Roadmap

Honest, unstarted, in rough priority order:

1. Full SPRITE iterative reconstruction (construct an actual matching dataset, not just bound its SD)
2. F-test and chi-square p-value consistency (extending the t-test check)
3. One-tailed test support
4. A `--file` mode that scans a whole paper/abstract for candidate statistics automatically

See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for the full current scope.

## Ecosystem

Part of the public **ClaimGate** verification-tool ecosystem:

- **ClaimGate** — paste claims, see what survives
- **ClaimLint** — catch unsupported README/docs claims
- **UnitGate** — catch broken physics equations
- **StatsGate** — catch impossible or inconsistent statistics *(this repo)*
- **EvidencePack** — seal claim-check receipts
- **ReplayGate** — replay checks and detect drift
- **ClaimStack Demo** — end-to-end public demo

These are public lite tools. The full private engine and advanced mechanics remain private.

**AI proposes. Gates verify. Unsupported claims do not survive.**

## License

MIT
