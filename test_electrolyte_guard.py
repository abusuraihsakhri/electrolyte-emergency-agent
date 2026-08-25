import pytest
from electrolyte_guard import (
    calc_sodium_deficit,
    calc_hyponatremia_correction,
    assess_hyperkalemia_ecg_risk,
    calc_calcium_gluconate_dose,
    calc_insulin_glucose_dose,
    calc_bicarbonate_dose,
    calc_kayexalate_dose,
    hyperkalemia_management_plan,
    calc_hypocalcemia_dose,
    calc_hypercalcemia_treatment,
    calc_magnesium_dose,
    calc_phosphorus_dose,
    main,
)


# --- Sodium Deficit ---

def test_sodium_deficit_male():
    """(130-120) × 0.6 × 70 = 420 mEq"""
    r = calc_sodium_deficit(120, 130, 70, "male")
    assert r["tbw_liters"] == 42.0
    assert r["na_deficit_meq"] == 420.0


def test_sodium_deficit_female():
    r = calc_sodium_deficit(120, 130, 60, "female")
    assert r["tbw_liters"] == 30.0
    assert r["na_deficit_meq"] == 300.0


# --- Hyponatremia Correction ---

def test_hyponatremia_correction():
    r = calc_hyponatremia_correction(118, 130, 70, "male", 24)
    assert r["ods_risk"] in ("LOW", "MODERATE", "HIGH")
    assert r["three_pct_nacl_rate_ml_hr"] > 0
    assert r["safe_desired_na"] <= 128  # max 10 mEq in 24h


def test_hyponatremia_not_needed():
    r = calc_hyponatremia_correction(140, 145, 70)
    assert r["correction_needed"] is False


def test_hyponatremia_ods_risk():
    """Trying to correct too fast should flag HIGH risk.
    Na 110→135 desired, but capped at 120 (max 10 mEq/24h).
    Correction rate = 10/24 = 0.417 mEq/hr, 10 mEq/24h → MODERATE.
    To get HIGH, need correction_per_24h > 10."""
    r = calc_hyponatremia_correction(110, 135, 70, "male", 12)
    # With 12h window, max correction = 10, rate = 10/12 = 0.833/hr, 20 mEq/24h → HIGH
    assert r["ods_risk"] == "HIGH"


def test_hyponatremia_safe_cap():
    """Max correction capped at 10 mEq in 24h"""
    r = calc_hyponatremia_correction(110, 140, 70, "male", 24)
    assert r["safe_desired_na"] == 120.0  # 110 + 10


# --- Hyperkalemia ECG Risk ---

def test_ecg_risk_mild():
    r = assess_hyperkalemia_ecg_risk(5.0)
    assert r["severity"] == "mild"


def test_ecg_risk_moderate():
    r = assess_hyperkalemia_ecg_risk(6.0)
    assert r["severity"] == "moderate"


def test_ecg_risk_severe():
    r = assess_hyperkalemia_ecg_risk(6.8)
    assert r["severity"] == "severe"


def test_ecg_risk_critical():
    r = assess_hyperkalemia_ecg_risk(7.5)
    assert r["severity"] == "critical"


def test_ecg_risk_lethal():
    r = assess_hyperkalemia_ecg_risk(8.5)
    assert r["severity"] == "lethal"


# --- Calcium Gluconate ---

def test_calcium_gluconate_not_needed():
    r = calc_calcium_gluconate_dose(5.0)
    assert r["dose_ml_10pct"] == 0


def test_calcium_gluconate_moderate():
    r = calc_calcium_gluconate_dose(6.5)
    assert r["dose_ml_10pct"] == 10


def test_calcium_gluconate_severe():
    r = calc_calcium_gluconate_dose(7.5)
    assert r["dose_ml_10pct"] == 20


# --- Insulin + Glucose ---

def test_insulin_glucose_standard():
    r = calc_insulin_glucose_dose(6.5, 70, 100)
    assert r["insulin_dose_units"] == 10
    assert r["give_dextrose"] is True
    assert r["dextrose_volume_ml"] == 50


def test_insulin_glucose_high_glucose():
    r = calc_insulin_glucose_dose(6.5, 70, 300)
    assert r["give_dextrose"] is False


# --- Bicarbonate ---

def test_bicarbonate_with_acidosis():
    r = calc_bicarbonate_dose(6.5, 70, 15)
    assert r["indicated"] is True
    assert r["dose_meq"] > 0


def test_bicarbonate_not_indicated():
    r = calc_bicarbonate_dose(6.5, 70, 24)
    assert r["indicated"] is False


# --- Kayexalate ---

def test_kayexalate_agents():
    r1 = calc_kayexalate_dose(6.0, 70, "kayexalate")
    r2 = calc_kayexalate_dose(6.0, 70, "patiromer")
    r3 = calc_kayexalate_dose(6.0, 70, "lokelma")
    assert "kayexalate" in r1["agent"]
    assert "patiromer" in r2["agent"]
    assert "lokelma" in r3["agent"]


# --- Hypocalcemia ---

def test_hypocalcemia_dose():
    """(9.0 - 7.0) × 0.2 × 70 = 28 mL (target Ca = 9.0)"""
    r = calc_hypocalcemia_dose(7.0, 70)
    assert r["dose_ml_10pct_cagluconate"] == 28.0
    assert r["treatment_needed"] is True


def test_hypocalcemia_not_needed():
    r = calc_hypocalcemia_dose(9.5, 70)
    assert r["treatment_needed"] is False


# --- Hypercalcemia ---

def test_hypercalcemia_mild():
    r = calc_hypercalcemia_treatment(11.0, 70)
    assert r["severity"] == "mild"


def test_hypercalcemia_severe():
    r = calc_hypercalcemia_treatment(14.5, 70)
    assert r["severity"] == "severe"
    assert r["calcitonin_dose_iu"] > 0


def test_hypercalcemia_normal():
    r = calc_hypercalcemia_treatment(9.5, 70)
    assert r["treatment_needed"] is False


# --- Hypomagnesemia ---

def test_magnesium_mild():
    r = calc_magnesium_dose(1.5, 70)
    assert r["dose_g_mgso4"] == 2.0


def test_magnesium_severe():
    r = calc_magnesium_dose(0.6, 70)
    assert r["dose_g_mgso4"] == 6.0


def test_magnesium_renal_impairment():
    r = calc_magnesium_dose(1.0, 70, "impaired")
    assert r["dose_g_mgso4"] == 2.0  # 4.0 × 0.5


def test_magnesium_normal():
    r = calc_magnesium_dose(2.0, 70)
    assert r["treatment_needed"] is False


# --- Phosphorus ---

def test_phosphorus_mild():
    r = calc_phosphorus_dose(2.2, 70)
    assert r["severity"] == "mild"
    assert r["route"] == "PO"


def test_phosphorus_severe():
    r = calc_phosphorus_dose(0.8, 70)
    assert r["severity"] == "severe"
    assert r["route"] == "IV"


def test_phosphorus_normal():
    r = calc_phosphorus_dose(3.5, 70)
    assert r["treatment_needed"] is False


# --- CLI ---

def test_cli_hyponatremia():
    assert main(["hyponatremia", "--na", "118", "--desired-na", "130",
                  "--weight", "70"]) == 0


def test_cli_hyperkalemia():
    assert main(["hyperkalemia", "--k", "6.5", "--weight", "70"]) == 0


def test_cli_hypocalcemia():
    assert main(["hypocalcemia", "--ca", "7.0", "--weight", "70"]) == 0
