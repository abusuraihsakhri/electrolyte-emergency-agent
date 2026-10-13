#!/usr/bin/env python3
"""
Electrolyte Emergency Calculator

Real implementations for:
- Hyponatremia correction (Na deficit, 3% NaCl rate, ODS risk)
- Hyperkalemia management (ECG risk, Ca-gluconate, insulin+glucose, bicarb, kayexalate)
- Hypocalcemia (calcium gluconate dosing)
- Hypercalcemia (NS hydration, calcitonin)
- Hypomagnesemia (MgSO4 dosing)
- Phosphorus replacement

References: KDIGO, AHA/ACC, Endocrine Society Guidelines
Stdlib only.
"""

import argparse
import json
import math
import sys
from typing import Dict, Any


def _require_finite(**measurements):
    """Reject NaN and infinity before comparisons and JSON serialization."""
    for name, value in measurements.items():
        try:
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        except (TypeError, OverflowError) as exc:
            raise ValueError(f"{name} must be a finite number") from exc


# ---------------------------------------------------------------------------
# Hyponatremia Correction
# ---------------------------------------------------------------------------

def calc_sodium_deficit(current_na: float, desired_na: float,
                        weight_kg: float, sex: str = "male") -> Dict[str, Any]:
    """
    Sodium deficit for hyponatremia correction.

    Na deficit (mEq) = (Desired Na - Current Na) × TBW
    TBW = 0.6 × weight (males) or 0.5 × weight (females)

    Args:
        current_na: Current serum sodium (mEq/L)
        desired_na: Target sodium (mEq/L)
        weight_kg: Patient weight in kg
        sex: "male" or "female"

    Returns:
        Dict with sodium deficit and TBW
    """
    _require_finite(current_na=current_na, desired_na=desired_na, weight_kg=weight_kg)
    if weight_kg <= 0 or weight_kg > 500:
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if current_na <= 0 or current_na > 200:
        raise ValueError("Current Na must be in physiological range (0-200 mEq/L)")
    if desired_na <= 0 or desired_na > 200:
        raise ValueError("Desired Na must be in physiological range (0-200 mEq/L)")
    if desired_na <= current_na:
        raise ValueError("Desired Na must be greater than current Na")

    if not isinstance(sex, str) or sex.lower() not in ("male", "female"):
        raise ValueError("Sex must be 'male' or 'female' for this TBW estimate")
    tbw_factor = 0.6 if sex.lower() == "male" else 0.5
    tbw = tbw_factor * weight_kg
    na_deficit = (desired_na - current_na) * tbw

    return {
        "current_na": current_na,
        "desired_na": desired_na,
        "weight_kg": weight_kg,
        "sex": sex,
        "tbw_liters": round(tbw, 1),
        "na_deficit_meq": round(na_deficit, 1),
    }


def calc_hyponatremia_correction(current_na: float, desired_na: float,
                                  weight_kg: float, sex: str = "male",
                                  hours: float = 24.0) -> Dict[str, Any]:
    """
    Safe hyponatremia correction rate and 3% NaCl infusion rate.

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
    """
    _require_finite(current_na=current_na, desired_na=desired_na, weight_kg=weight_kg, hours=hours)
    if hours <= 0:
        raise ValueError("Hours must be positive")
    if weight_kg <= 0 or weight_kg > 500:
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if current_na <= 0 or current_na > 200:
        raise ValueError("Current Na must be in physiological range (0-200 mEq/L)")
    if desired_na <= 0 or desired_na > 200:
        raise ValueError("Desired Na must be in physiological range (0-200 mEq/L)")
    if current_na >= 135:
        return {
            "current_na": current_na,
            "diagnosis": "Not hyponatremic (Na ≥ 135)",
            "correction_needed": False,
        }

    if desired_na <= current_na:
        raise ValueError("Desired Na must exceed current Na")
    # Educational ceiling: first 24 h <=10 mmol/L; each subsequent 24 h <=8.
    # A total ceiling is not a treatment target or a patient-specific safety assessment.
    max_correction = min(hours, 24.0) * (10.0 / 24.0)
    max_correction += max(hours - 24.0, 0.0) * (8.0 / 24.0)
    safe_desired = min(desired_na, current_na + max_correction)

    deficit = calc_sodium_deficit(current_na, safe_desired, weight_kg, sex)
    na_deficit = deficit["na_deficit_meq"]

    # 3% NaCl: 513 mEq/L
    hypertonic_na_conc = 513.0
    infusion_rate_ml_hr = (na_deficit / hypertonic_na_conc) * 1000.0 / hours

    correction_per_hour = (safe_desired - current_na) / hours
    correction_per_24h = correction_per_hour * 24.0

    # Risk assessment
    if correction_per_24h > 10:
        ods_risk = "HIGH"
        recommendation = ("CORRECTION TOO RAPID. Risk of osmotic demyelination syndrome (ODS). "
                          "Slow rate or add D5W/desmopressin to prevent overcorrection.")
    elif correction_per_24h > 8:
        ods_risk = "MODERATE"
        recommendation = "Approaching safe limit. Monitor sodium q2-4h."
    else:
        ods_risk = "LOW"
        recommendation = "Within safe correction rate. Monitor sodium q4-6h."

    return {
        "current_na": current_na,
        "desired_na": desired_na,
        "safe_desired_na": round(safe_desired, 1),
        "weight_kg": weight_kg,
        "sex": sex,
        "tbw_liters": deficit["tbw_liters"],
        "na_deficit_meq": round(na_deficit, 1),
        "correction_hours": hours,
        "correction_rate_meq_hr": round(correction_per_hour, 2),
        "correction_per_24h_meq": round(correction_per_24h, 1),
        "max_safe_correction_24h": 10.0,
        "requested_exceeds_limit": desired_na > safe_desired,
        "calculation_only": True,
        "clinical_caution": (
            "Arithmetic estimate, NOT a hypertonic saline prescription or "
            "patient-specific ODS risk prediction. Symptoms, chronicity, urine "
            "output, comorbidities and serial sodium values require clinician review."
        ),
        "three_pct_nacl_rate_ml_hr": round(infusion_rate_ml_hr, 1),
        "three_pct_nacl_conc_meq_l": hypertonic_na_conc,
        "ods_risk": ods_risk,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Hyperkalemia Management
# ---------------------------------------------------------------------------

def assess_hyperkalemia_ecg_risk(k_level: float) -> Dict[str, Any]:
    """
    ECG risk assessment based on potassium level.

    K+ 5.5-6.5: Peaked T waves
    K+ 6.5-7.0: Loss of P wave, widened QRS
    K+ 7.0-8.0: Sine wave pattern
    K+ > 8.0: Cardiac arrest risk

    Args:
        k_level: Serum potassium in mEq/L

    Returns:
        Dict with risk level and expected ECG changes
    """
    _require_finite(k_level=k_level)
    if k_level < 0 or k_level > 15:
        raise ValueError("K level must be in physiological range (0-15 mEq/L)")
    if k_level < 5.5:
        return {
            "k_level": k_level,
            "severity": "mild",
            "ecg_changes": "None expected",
            "risk": "low",
            "action": "Interpret with clinical context and measured ECG; a potassium value does not predict ECG findings.",
        }
    elif k_level < 6.5:
        return {
            "k_level": k_level,
            "severity": "moderate",
            "ecg_changes": "Peaked T waves, shortened QT",
            "risk": "moderate",
            "action": "Prompt clinical assessment with ECG and repeat testing as appropriate; do not infer ECG changes from potassium alone.",
        }
    elif k_level < 7.0:
        return {
            "k_level": k_level,
            "severity": "severe",
            "ecg_changes": "Loss of P waves, widened QRS, prolonged PR",
            "risk": "high",
            "action": "Emergency clinical assessment, ECG and local treatment protocol; no ECG pattern is guaranteed by potassium level.",
        }
    elif k_level < 8.0:
        return {
            "k_level": k_level,
            "severity": "critical",
            "ecg_changes": "Sine wave pattern, very wide QRS",
            "risk": "critical",
            "action": "Immediate emergency care and monitored assessment under local hyperkalemia protocol.",
        }
    else:
        return {
            "k_level": k_level,
            "severity": "lethal",
            "ecg_changes": "Sine wave → ventricular fibrillation → asystole",
            "risk": "imminent_arrest",
            "action": "Immediate emergency care and ECG monitoring; this output is not a prescription.",
        }


def calc_calcium_gluconate_dose(k_level: float, weight_kg: float = 70.0) -> Dict[str, Any]:
    """
    Calcium gluconate 10% for cardioprotection in hyperkalemia.

    Dose: 10-20 mL of 10% calcium gluconate IV over 2-5 minutes
    Onset: 1-3 minutes, Duration: 30-60 minutes
    Repeat if no ECG improvement in 5 minutes.

    10% Ca-gluconate: 100 mg/mL = 9.3 mg elemental Ca/mL = 0.465 mEq/mL

    Args:
        k_level: Serum potassium (mEq/L)
        weight_kg: Patient weight (for dose adjustment)

    Returns:
        Dict with dosing
    """
    _require_finite(k_level=k_level, weight_kg=weight_kg)
    if k_level < 0 or k_level > 15:
        raise ValueError("K level must be in physiological range (0-15 mEq/L)")
    if weight_kg <= 0 or weight_kg > 500:
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if k_level < 6.0:
        dose_ml = 0
        urgency = "not_routine"
        note = "Not routinely indicated for K < 6.0 without ECG changes."
    elif k_level < 7.0:
        dose_ml = 10
        urgency = "recommended"
        note = "10 mL of 10% Ca-gluconate IV over 2-5 min."
    else:
        dose_ml = 20
        urgency = "emergent"
        note = "20 mL of 10% Ca-gluconate IV over 2-5 min. May repeat in 5 min."

    elemental_ca_mg = dose_ml * 9.3
    ca_meq = dose_ml * 0.465

    return {
        "indication": "Hyperkalemia cardioprotection",
        "k_level": k_level,
        "dose_ml_10pct": dose_ml,
        "elemental_calcium_mg": round(elemental_ca_mg, 1),
        "calcium_meq": round(ca_meq, 2),
        "concentration": "10% Ca-gluconate (100 mg/mL, 0.465 mEq/mL)",
        "infusion_time": "2-5 minutes IV push",
        "onset": "1-3 minutes",
        "duration": "30-60 minutes",
        "urgency": urgency,
        "note": note,
    }


def calc_insulin_glucose_dose(k_level: float, weight_kg: float = 70.0,
                               glucose_mg_dl: float = 100.0) -> Dict[str, Any]:
    """
    Insulin + glucose for intracellular potassium shift.

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
    """
    _require_finite(k_level=k_level, weight_kg=weight_kg, glucose_mg_dl=glucose_mg_dl)
    if k_level < 0 or k_level > 15:
        raise ValueError("K level must be in physiological range (0-15 mEq/L)")
    if weight_kg <= 0 or weight_kg > 500:
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if glucose_mg_dl < 0 or glucose_mg_dl > 1000:
        raise ValueError("Glucose must be in physiological range (0-1000 mg/dL)")
    insulin_dose = 10.0  # units regular insulin IV

    if glucose_mg_dl < 250:
        dextrose_ml = 50.0  # D50W
        dextrose_g = 25.0
        give_dextrose = True
    else:
        dextrose_ml = 0
        dextrose_g = 0
        give_dextrose = False

    expected_k_drop = "0.5-1.2 mEq/L in 15-30 minutes"

    return {
        "indication": "Intracellular K shift",
        "k_level": k_level,
        "insulin_dose_units": insulin_dose,
        "insulin_type": "Regular insulin IV push",
        "dextrose_dose_g": dextrose_g,
        "dextrose_volume_ml": dextrose_ml,
        "dextrose_concentration": "D50W (50%)",
        "give_dextrose": give_dextrose,
        "glucose_mg_dl": glucose_mg_dl,
        "expected_k_reduction": expected_k_drop,
        "onset": "15-30 minutes",
        "duration": "4-6 hours",
        "monitoring": "Check glucose q1h for 6h (hypoglycemia risk)",
        "note": "Hold dextrose if glucose > 250 mg/dL. Monitor glucose closely.",
    }


def calc_bicarbonate_dose(k_level: float, weight_kg: float = 70.0,
                           hco3: float = 20.0) -> Dict[str, Any]:
    """
    Sodium bicarbonate for hyperkalemia (limited efficacy).

    NaHCO3 1-2 mEq/kg IV over 5-10 minutes
    Most effective if concurrent metabolic acidosis (HCO3 < 20)

    Note: Bicarbonate alone is less effective than insulin+glucose for K shift.
    Consider only with concurrent acidosis.

    Args:
        k_level: Serum potassium
        weight_kg: Patient weight
        hco3: Serum bicarbonate (mEq/L)

    Returns:
        Dict with bicarbonate dosing
    """
    _require_finite(k_level=k_level, weight_kg=weight_kg, hco3=hco3)
    if k_level < 0 or k_level > 15:
        raise ValueError("K level must be in physiological range (0-15 mEq/L)")
    if weight_kg <= 0 or weight_kg > 500:
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if hco3 < 0 or hco3 > 50:
        raise ValueError("HCO3 must be in physiological range (0-50 mEq/L)")
    if hco3 >= 22:
        dose_meq = 0
        note = "Bicarbonate not indicated (HCO3 ≥ 22). Use insulin+glucose instead."
        indicated = False
    else:
        dose_meq = weight_kg * 1.5  # 1-2 mEq/kg, use 1.5 as midpoint
        note = (f"NaHCO3 {round(dose_meq)} mEq IV over 5-10 min. "
                "Most effective with concurrent acidosis.")
        indicated = True

    return {
        "indication": "Hyperkalemia with acidosis",
        "k_level": k_level,
        "hco3": hco3,
        "dose_meq": round(dose_meq, 0),
        "concentration": "NaHCO3 8.4% (1 mEq/mL)",
        "volume_ml": round(dose_meq, 0),
        "infusion_time": "5-10 minutes IV",
        "indicated": indicated,
        "note": note,
        "efficacy": "Limited as monotherapy. Best combined with insulin+glucose.",
    }


def calc_kayexalate_dose(k_level: float, weight_kg: float = 70.0,
                          agent: str = "patiromer") -> Dict[str, Any]:
    """
    Potassium-binding agents for K elimination.

    Sodium polystyrene sulfonate (Kayexalate): 15-30g PO/PR
    Patiromer (Veltassa): 8.4g PO daily (onset 7h, not for acute)
    Sodium zirconium cyclosilicate (Lokelma): 10g PO TID × 48h (onset 1-2h)

    Args:
        k_level: Serum potassium
        weight_kg: Patient weight
        agent: "kayexalate", "patiromer", or "lokelma"

    Returns:
        Dict with binding agent dosing
    """
    _require_finite(k_level=k_level, weight_kg=weight_kg)
    if not (0 <= k_level <= 15):
        raise ValueError("K level must be in physiological range (0-15 mEq/L)")
    if not (0 < weight_kg <= 500):
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if agent == "kayexalate":
        dose = "15-30g PO or rectally"
        onset = "1-6 hours (PO), longer PR"
        route = "PO/PR"
        note = "Do NOT mix with sorbitol. Risk of serious gastrointestinal injury; not a reliable emergency potassium-lowering treatment."
        expected_drop = "0.5-1.0 mEq/L"
    elif agent == "patiromer":
        dose = "8.4g PO once daily"
        onset = "7+ hours"
        route = "PO"
        note = "NOT for acute emergencies. Separate from other meds by 3h."
        expected_drop = "0.2-0.5 mEq/L per day"
    elif agent == "lokelma":
        dose = "10g PO three times daily × 48h, then 10g daily"
        onset = "1-2 hours"
        route = "PO"
        note = "Fastest onset binder. Can be used for acute K reduction."
        expected_drop = "0.5-1.0 mEq/L in 24h"
    else:
        raise ValueError("Agent must be 'kayexalate', 'patiromer', or 'lokelma'")

    return {
        "agent": agent,
        "k_level": k_level,
        "dose": dose,
        "route": route,
        "onset": onset,
        "expected_k_drop": expected_drop,
        "note": note,
    }


def hyperkalemia_management_plan(k_level: float, weight_kg: float = 70.0,
                                  glucose_mg_dl: float = 100.0,
                                  hco3: float = 20.0) -> Dict[str, Any]:
    """
    Complete hyperkalemia management plan.
    """
    ecg = assess_hyperkalemia_ecg_risk(k_level)
    ca_gluconate = calc_calcium_gluconate_dose(k_level, weight_kg)
    insulin_glucose = calc_insulin_glucose_dose(k_level, weight_kg, glucose_mg_dl)
    bicarb = calc_bicarbonate_dose(k_level, weight_kg, hco3)
    binder = calc_kayexalate_dose(k_level, weight_kg, "lokelma")

    return {
        "k_level": k_level,
        "ecg_risk": ecg,
        "cardioprotection": ca_gluconate,
        "intracellular_shift": insulin_glucose,
        "bicarbonate": bicarb,
        "elimination": binder,
        "dialysis_consult": k_level >= 6.5,
    }


# ---------------------------------------------------------------------------
# Hypocalcemia
# ---------------------------------------------------------------------------

def calc_hypocalcemia_dose(current_ca: float, weight_kg: float) -> Dict[str, Any]:
    """
    Calcium gluconate 10% dose for symptomatic hypocalcemia.

    Dose (mL of 10% Ca-gluconate) = (10 - Ca) × 0.2 × weight_kg
    10% Ca-gluconate: 9.3 mg elemental Ca per mL

    Correction: Target Ca 8.0-9.0 mg/dL

    Args:
        current_ca: Current serum calcium (mg/dL)
        weight_kg: Patient weight in kg

    Returns:
        Dict with calcium replacement dosing
    """
    _require_finite(current_ca=current_ca, weight_kg=weight_kg)
    if weight_kg <= 0 or weight_kg > 500:
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if current_ca < 0 or current_ca > 20:
        raise ValueError("Current Ca must be in physiological range (0-20 mg/dL)")
    if current_ca >= 8.5:
        return {
            "current_ca": current_ca,
            "diagnosis": "Calcium not significantly low (≥ 8.5 mg/dL)",
            "treatment_needed": False,
        }

    desired_ca = 9.0
    ca_deficit = desired_ca - current_ca
    dose_ml = ca_deficit * 0.2 * weight_kg
    elemental_ca_mg = dose_ml * 9.3
    ca_meq = dose_ml * 0.465

    return {
        "current_ca": current_ca,
        "desired_ca": desired_ca,
        "weight_kg": weight_kg,
        "ca_deficit_mg_dl": round(ca_deficit, 1),
        "dose_ml_10pct_cagluconate": round(dose_ml, 1),
        "elemental_calcium_mg": round(elemental_ca_mg, 1),
        "calcium_meq": round(ca_meq, 2),
        "infusion": "Infuse over 10-20 minutes with cardiac monitoring",
        "note": "Give 10 mL (1 ampule) IV push over 10 min for acute symptoms, then infuse remainder.",
        "treatment_needed": True,
    }


# ---------------------------------------------------------------------------
# Hypercalcemia
# ---------------------------------------------------------------------------

def calc_hypercalcemia_treatment(ca_level: float, weight_kg: float) -> Dict[str, Any]:
    """
    Hypercalcemia management.

    Mild (10.5-12): Hydration only
    Moderate (12-14): NS hydration + consider calcitonin
    Severe (>14): Emergent - NS + calcitonin + bisphosphonate

    NS hydration: 200-300 mL/hr for 2-4 hours, then 100-150 mL/hr
    Calcitonin: 4 IU/kg SC/IM, onset 4-6h, duration <48h (tachyphylaxis)

    Args:
        ca_level: Serum calcium (mg/dL)
        weight_kg: Patient weight

    Returns:
        Dict with treatment plan
    """
    _require_finite(ca_level=ca_level, weight_kg=weight_kg)
    if weight_kg <= 0 or weight_kg > 500:
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if ca_level < 0 or ca_level > 30:
        raise ValueError("Ca level must be in physiological range (0-30 mg/dL)")
    if ca_level < 10.5:
        return {
            "ca_level": ca_level,
            "diagnosis": "Normal or mildly elevated calcium",
            "treatment_needed": False,
        }

    # NS hydration
    ns_bolus_ml = 1000.0  # 1L bolus
    ns_maintenance_ml_hr = 150.0
    ns_total_24h = ns_bolus_ml + (ns_maintenance_ml_hr * 20)  # 20h after initial bolus

    # Calcitonin
    calcitonin_dose_iu = 4.0 * weight_kg
    calcitonin_onset = "4-6 hours"
    calcitonin_duration = "< 48 hours (tachyphylaxis)"

    if ca_level >= 14:
        severity = "severe"
        urgency = "emergent"
        additional = "Consider dialysis, bisphosphonate (zoledronic acid 4mg IV)"
    elif ca_level >= 12:
        severity = "moderate"
        urgency = "urgent"
        additional = "Consider bisphosphonate if not responding to hydration"
    else:
        severity = "mild"
        urgency = "routine"
        additional = "Hydration usually sufficient"
        calcitonin_dose_iu = 0  # not needed for mild

    return {
        "ca_level": ca_level,
        "severity": severity,
        "urgency": urgency,
        "ns_bolus_ml": ns_bolus_ml,
        "ns_maintenance_ml_hr": ns_maintenance_ml_hr,
        "ns_total_24h_ml": round(ns_total_24h, 0),
        "calcitonin_dose_iu": round(calcitonin_dose_iu, 0),
        "calcitonin_route": "SC or IM",
        "calcitonin_onset": calcitonin_onset,
        "calcitonin_duration": calcitonin_duration,
        "additional": additional,
        "monitoring": "Recheck Ca q4-6h, monitor urine output, cardiac monitoring",
    }


# ---------------------------------------------------------------------------
# Hypomagnesemia
# ---------------------------------------------------------------------------

def calc_magnesium_dose(current_mg: float, weight_kg: float,
                         renal_function: str = "normal") -> Dict[str, Any]:
    """
    Magnesium sulfate replacement for hypomagnesemia.

    Mild (1.2-1.7 mg/dL): 1-2g MgSO4 IV over 1-2h
    Moderate (0.8-1.2): 2-4g MgSO4 IV over 2-4h
    Severe (<0.8): 4-6g MgSO4 IV over 4-6h (cardiac monitoring)

    MgSO4: 1g = 8.12 mEq Mg = 98.6 mg elemental Mg

    Args:
        current_mg: Serum magnesium (mg/dL)
        weight_kg: Patient weight
        renal_function: "normal" or "impaired"

    Returns:
        Dict with magnesium replacement
    """
    _require_finite(current_mg=current_mg, weight_kg=weight_kg)
    if weight_kg <= 0 or weight_kg > 500:
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if current_mg < 0 or current_mg > 10:
        raise ValueError("Current Mg must be in physiological range (0-10 mg/dL)")
    if renal_function not in ("normal", "impaired"):
        raise ValueError("Renal function must be 'normal' or 'impaired'")
    if current_mg >= 1.7:
        return {
            "current_mg": current_mg,
            "diagnosis": "Magnesium not low (≥ 1.7 mg/dL)",
            "treatment_needed": False,
        }

    if current_mg >= 1.2:
        severity = "mild"
        dose_g = 2.0
        infusion_hours = 2.0
    elif current_mg >= 0.8:
        severity = "moderate"
        dose_g = 4.0
        infusion_hours = 4.0
    else:
        severity = "severe"
        dose_g = 6.0
        infusion_hours = 6.0

    if renal_function == "impaired":
        dose_g = dose_g * 0.5  # Reduce dose by 50% in renal impairment
        note = "Dose reduced 50% for renal impairment. Monitor closely."
    else:
        note = "Recheck Mg 6-12h after infusion. Repeat if needed."

    dose_meq = dose_g * 8.12
    rate_g_hr = dose_g / infusion_hours

    return {
        "current_mg": current_mg,
        "severity": severity,
        "dose_g_mgso4": round(dose_g, 1),
        "dose_meq": round(dose_meq, 1),
        "infusion_hours": infusion_hours,
        "rate_g_hr": round(rate_g_hr, 2),
        "renal_function": renal_function,
        "note": note,
        "treatment_needed": True,
    }


# ---------------------------------------------------------------------------
# Phosphorus Replacement
# ---------------------------------------------------------------------------

def calc_phosphorus_dose(current_phos: float, weight_kg: float,
                           renal_function: str = "normal") -> Dict[str, Any]:
    """
    Phosphorus replacement for hypophosphatemia.

    Mild (2.0-2.5 mg/dL): PO supplementation (Na/K phosphate 250-500 mg TID)
    Moderate (1.0-2.0): IV Na-phosphate or K-phosphate 0.16-0.32 mmol/kg over 2-6h
    Severe (<1.0): IV 0.32 mmol/kg over 6-12h (ICU monitoring)

    1 mmol phosphorus = 31 mg elemental P

    Args:
        current_phos: Serum phosphorus (mg/dL)
        weight_kg: Patient weight
        renal_function: "normal" or "impaired"

    Returns:
        Dict with phosphorus replacement
    """
    _require_finite(current_phos=current_phos, weight_kg=weight_kg)
    if weight_kg <= 0 or weight_kg > 500:
        raise ValueError("Weight must be positive and realistic (0-500 kg)")
    if current_phos < 0 or current_phos > 15:
        raise ValueError("Current phosphorus must be in physiological range (0-15 mg/dL)")
    if renal_function not in ("normal", "impaired"):
        raise ValueError("Renal function must be 'normal' or 'impaired'")
    if current_phos >= 2.5:
        return {
            "current_phos": current_phos,
            "diagnosis": "Phosphorus not low (≥ 2.5 mg/dL)",
            "treatment_needed": False,
        }

    if current_phos >= 2.0:
        severity = "mild"
        dose_mmol_kg = 0.15
        route = "PO"
        infusion_hours = 0
        note = "Na-phosphate or K-phosphate 250-500 mg PO TID"
    elif current_phos >= 1.0:
        severity = "moderate"
        dose_mmol_kg = 0.24
        route = "IV"
        infusion_hours = 4.0
        note = "IV phosphate over 4-6h. Recheck after infusion."
    else:
        severity = "severe"
        dose_mmol_kg = 0.32
        route = "IV"
        infusion_hours = 8.0
        note = "SEVERE: IV phosphate over 6-12h. ICU monitoring. Risk of hypocalcemia."

    if renal_function == "impaired":
        dose_mmol_kg *= 0.5
        note += " Dose reduced 50% for renal impairment."

    dose_mmol = dose_mmol_kg * weight_kg
    dose_mg_elemental = dose_mmol * 31.0

    return {
        "current_phos": current_phos,
        "severity": severity,
        "dose_mmol": round(dose_mmol, 2),
        "dose_mmol_kg": round(dose_mmol_kg, 3),
        "dose_mg_elemental": round(dose_mg_elemental, 1),
        "route": route,
        "infusion_hours": infusion_hours,
        "renal_function": renal_function,
        "note": note,
        "treatment_needed": True,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="electrolyte-guard",
        description="Electrolyte Emergency Calculator"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Hyponatremia
    p_hypo = sub.add_parser("hyponatremia", help="Hyponatremia correction")
    p_hypo.add_argument("--na", type=float, required=True, help="Current Na (mEq/L)")
    p_hypo.add_argument("--desired-na", type=float, required=True, help="Target Na")
    p_hypo.add_argument("--weight", type=float, required=True, help="Weight (kg)")
    p_hypo.add_argument("--sex", choices=["male", "female"], default="male")
    p_hypo.add_argument("--hours", type=float, default=24.0, help="Correction hours")

    # Hyperkalemia
    p_hyper = sub.add_parser("hyperkalemia", help="Hyperkalemia management")
    p_hyper.add_argument("--k", type=float, required=True, help="Serum K (mEq/L)")
    p_hyper.add_argument("--weight", type=float, default=70.0, help="Weight (kg)")
    p_hyper.add_argument("--glucose", type=float, default=100.0, help="Glucose (mg/dL)")
    p_hyper.add_argument("--hco3", type=float, default=20.0, help="HCO3 (mEq/L)")

    # Hypocalcemia
    p_cah = sub.add_parser("hypocalcemia", help="Hypocalcemia treatment")
    p_cah.add_argument("--ca", type=float, required=True, help="Serum Ca (mg/dL)")
    p_cah.add_argument("--weight", type=float, required=True, help="Weight (kg)")

    # Hypercalcemia
    p_cahh = sub.add_parser("hypercalcemia", help="Hypercalcemia treatment")
    p_cahh.add_argument("--ca", type=float, required=True, help="Serum Ca (mg/dL)")
    p_cahh.add_argument("--weight", type=float, required=True, help="Weight (kg)")

    # Hypomagnesemia
    p_mg = sub.add_parser("hypomagnesemia", help="Magnesium replacement")
    p_mg.add_argument("--mg", type=float, required=True, help="Serum Mg (mg/dL)")
    p_mg.add_argument("--weight", type=float, required=True, help="Weight (kg)")
    p_mg.add_argument("--renal", choices=["normal", "impaired"], default="normal")

    # Phosphorus
    p_phos = sub.add_parser("phosphorus", help="Phosphorus replacement")
    p_phos.add_argument("--phos", type=float, required=True, help="Serum Phos (mg/dL)")
    p_phos.add_argument("--weight", type=float, required=True, help="Weight (kg)")
    p_phos.add_argument("--renal", choices=["normal", "impaired"], default="normal")

    args = parser.parse_args(argv)

    if args.command == "hyponatremia":
        result = calc_hyponatremia_correction(args.na, args.desired_na, args.weight,
                                               args.sex, args.hours)
    elif args.command == "hyperkalemia":
        result = hyperkalemia_management_plan(args.k, args.weight, args.glucose, args.hco3)
    elif args.command == "hypocalcemia":
        result = calc_hypocalcemia_dose(args.ca, args.weight)
    elif args.command == "hypercalcemia":
        result = calc_hypercalcemia_treatment(args.ca, args.weight)
    elif args.command == "hypomagnesemia":
        result = calc_magnesium_dose(args.mg, args.weight, args.renal)
    elif args.command == "phosphorus":
        result = calc_phosphorus_dose(args.phos, args.weight, args.renal)
    else:
        parser.print_help()
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
