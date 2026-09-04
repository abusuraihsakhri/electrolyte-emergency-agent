# Electrolyte Emergency Agent

> **Domain:** Nephrology & Renal Replacement Protocols  
> **Reference Guidelines & Standards:** `KDIGO & KDOQI Clinical Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Electrolyte Emergency Agent** is an advanced analytical and computational platform implementing Severe Hyponatremia (<=6-8 mEq/24h) & Hyperkalemia Safe Titrator.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calc_sodium_deficit()`**: Sodium deficit for hyponatremia correction.

Na deficit (mEq) = (Desired Na - Current Na) × TBW
TBW = 0.6 × weight (males) or 0.5 × weight (females)

Args:
    current_na: Current serum sodium (mEq/L)
    desired_na: Target sodium (mEq/L)
    weight_kg: Patient weight in kg
    sex: "male" or "female"

Returns:
    Dict with sodium deficit and TBW
- **`calc_hyponatremia_correction()`**: Safe hyponatremia correction rate and 3% NaCl infusion rate.

Max correction: 8-10 mEq/L in 24h (risk of osmotic demyelination syndrome)
3% NaCl = 513 mEq Na per liter

Infusion rate (mL/hr) = Na deficit / 513 × 1000 / hours

Args:
    current_na: Current serum sodium (mEq/L)
    desired_na: Target sodium (mEq/L)
    weight_kg: Patient weight in kg
    sex: "male" or "female"
    hours: Correction time in hours

Returns:
    Dict with correction plan
- **`assess_hyperkalemia_ecg_risk()`**: ECG risk assessment based on potassium level.

K+ 5.5-6.5: Peaked T waves
K+ 6.5-7.0: Loss of P wave, widened QRS
K+ 7.0-8.0: Sine wave pattern
K+ > 8.0: Cardiac arrest risk

Args:
    k_level: Serum potassium in mEq/L

Returns:
    Dict with risk level and expected ECG changes
- **`calc_calcium_gluconate_dose()`**: Calcium gluconate 10% for cardioprotection in hyperkalemia.

Dose: 10-20 mL of 10% calcium gluconate IV over 2-5 minutes
Onset: 1-3 minutes, Duration: 30-60 minutes
Repeat if no ECG improvement in 5 minutes.

10% Ca-gluconate: 100 mg/mL = 9.3 mg elemental Ca/mL = 0.465 mEq/mL

Args:
    k_level: Serum potassium (mEq/L)
    weight_kg: Patient weight (for dose adjustment)

Returns:
    Dict with dosing
- **`calc_insulin_glucose_dose()`**: Insulin + glucose for intracellular potassium shift.

Standard: 10 units regular insulin IV + 25g dextrose (D50W 50 mL)
Expected K drop: 0.5-1.2 mEq/L in 15-30 minutes
Duration: 4-6 hours

If glucose < 250: Give dextrose
If glucose ≥ 250: Insulin only (monitor for hypoglycemia)

Args:
    k_level: Serum potassium (mEq/L)
    weight_kg: Patient weight
    glucose_mg_dl: Current blood glucose

Returns:
    Dict with insulin/glucose dosing

---

## 📐 Mathematical Formulation & Logic

```text
  ods_risk = "HIGH"
  ods_risk = "MODERATE"
  ods_risk = "LOW"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --input data.csv
```

### Parameter Reference
- `--interactive`: Launch guided terminal interactive wizard.
- `--input <path>`: Evaluate input from JSON or CSV specification.
- `--json`: Output deterministic structured results in JSON format.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOB, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition. Configure `AUDIT_SECRET_KEY` env var for persistent audit integrity.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Input Validation:** All calculation functions validate physiological ranges to prevent erroneous outputs.
* **FastAPI & Prometheus Telemetry:** Exposes REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

### Test Coverage

- **50 tests** covering all calculation functions, CLI commands, PHI guard enforcement, audit trail integrity, and input validation
- Tests verify physiological range validation, edge cases, and error handling

---

## 🐳 Container Deployment

```bash
docker build -t electrolyte-emergency-agent .
docker run -p 8000:8000 electrolyte-emergency-agent
```
