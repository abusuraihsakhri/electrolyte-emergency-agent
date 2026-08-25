# Electrolyte Emergency Calculator

> **Nephrology / Emergency** — Electrolyte Disorder Management

## Overview

Real clinical calculator for emergent electrolyte disorders including hyponatremia safe correction (ODS prevention), hyperkalemia multi-step management, hypocalcemia/hypercalcemia treatment, hypomagnesemia replacement, and phosphorus replacement.

**References:** KDIGO, AHA/ACC, Endocrine Society Guidelines

## Formulas Implemented

| Calculator | Formula |
|:-----------|:--------|
| **Na Deficit** | (Desired Na - Current Na) × TBW; TBW = 0.6×weight (M) / 0.5×weight (F) |
| **3% NaCl Rate** | Deficit / 513 × 1000 / hours |
| **ODS Risk** | Max 8-10 mEq/L correction in 24h |
| **Ca Gluconate** | (10 - Ca) × 0.2 × weight mL of 10% Ca-gluconate |
| **Insulin+Glucose** | 10 units regular insulin + D50W 50 mL |
| **MgSO4 Dose** | Mild 2g, Moderate 4g, Severe 6g IV |
| **Phosphorus** | 0.15-0.32 mmol/kg depending on severity |

## CLI Usage

```bash
# Hyponatremia correction
python electrolyte_guard.py hyponatremia --na 118 --desired-na 130 --weight 70 --sex male --hours 24

# Hyperkalemia management
python electrolyte_guard.py hyperkalemia --k 6.8 --weight 70 --glucose 100 --hco3 18

# Hypocalcemia
python electrolyte_guard.py hypocalcemia --ca 7.0 --weight 70

# Hypercalcemia
python electrolyte_guard.py hypercalcemia --ca 13.5 --weight 70

# Hypomagnesemia
python electrolyte_guard.py hypomagnesemia --mg 1.0 --weight 70

# Phosphorus replacement
python electrolyte_guard.py phosphorus --phos 1.5 --weight 70
```

## Python API

```python
from electrolyte_guard import (calc_hyponatremia_correction, hyperkalemia_management_plan,
                                calc_hypocalcemia_dose, calc_magnesium_dose)

# Hyponatremia
result = calc_hyponatremia_correction(current_na=118, desired_na=130,
                                       weight_kg=70, sex="male", hours=24)
print(result["three_pct_nacl_rate_ml_hr"])
print(result["ods_risk"])

# Hyperkalemia
plan = hyperkalemia_management_plan(k_level=6.8, weight_kg=70)
```

## Safety Limits

| Parameter | Limit |
|:----------|:------|
| Na correction (24h) | ≤ 8-10 mEq/L |
| Na correction (48h) | ≤ 18 mEq/L |
| K for Ca-gluconate | ≥ 6.0 or ECG changes |
| K for emergent dialysis | ≥ 6.5 with refractory |

## License

MIT License.
