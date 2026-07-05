# StatsGate examples

Every example below is actual verified CLI output, not hand-written.

## GRIM — is a reported mean arithmetically reachable?

```bash
python -m statsgate grim 3.44 25
```
```text
[grim] {'mean': '3.44', 'n': 25}
  -> CONSISTENT
     reachable: integer sum 86 / 25 rounds to 3.44
```

```bash
python -m statsgate grim 5.94 25
```
```text
[grim] {'mean': '5.94', 'n': 25}
  -> IMPOSSIBLE
     no integer sum over 25 items rounds to 5.94 at 2 decimal place(s) -- this mean cannot come from 25 integer-scored observations
```

## SD range — is a reported standard deviation achievable?

```bash
python -m statsgate sdrange 2.50 0.50 4 1 4
```
```text
[sd_range] {'mean': '2.50', 'sd': '0.50', 'n': 4, 'item_min': 1.0, 'item_max': 4.0}
  -> NOT_RULED_OUT
     reported SD 0.50 falls within the achievable range [0.5, 1.5] -- not disproven, not proven to exist
```

```bash
python -m statsgate sdrange 2.50 5.00 4 1 4
```
```text
[sd_range] {'mean': '2.50', 'sd': '5.00', 'n': 4, 'item_min': 1.0, 'item_max': 4.0}
  -> IMPOSSIBLE
     reported SD 5.00 is outside the achievable range [0.5, 1.5] for mean 2.50, n=4, items in [1.0, 4.0]
```

## t-statistic / p-value consistency (statcheck-style)

```bash
python -m statsgate tpvalue 2.0 20 0.06
```
```text
[t_pvalue] {'t': '2.0', 'df': '20', 'p': '0.06'}
  -> CONSISTENT
     t(20)=2.0 implies p ~= 0.059266, matching reported 0.06 within tolerance
```

```bash
python -m statsgate tpvalue 2.0 20 0.50
```
```text
[t_pvalue] {'t': '2.0', 'df': '20', 'p': '0.50'}
  -> IMPOSSIBLE
     t(20)=2.0 implies two-tailed p ~= 0.059266, not 0.50 (difference 0.4407 > tolerance 0.005)
```

## Run everything at once

```bash
python -m statsgate --demo
python -m statsgate --json grim 3.44 25   # machine-readable output
```

## As a library

```python
from statsgate import check_grim, check_sd_range, check_t_pvalue

result = check_grim("5.94", 25)
if result.status == "IMPOSSIBLE":
    print(result.reason)
```
