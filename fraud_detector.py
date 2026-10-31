from typing import Dict, Any, List
import database

def analyze_for_fraud(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks for fraud indicators: duplicate heat numbers, missing mandatory fields, and statistically abnormal values.
    """
    alerts = []
    is_risk = False
    
    # 1. Missing Mandatory Fields
    mandatory_fields = ["heat_number", "material_grade", "yield_strength", "tensile_strength"]
    for field in mandatory_fields:
        val = parsed_data.get(field)
        if val is None or val == "" or str(val).lower() == "unknown":
            alerts.append(f"⚠ Missing Mandatory Field: {field.replace('_', ' ').title()}")
            is_risk = True

    # 2. Duplicate Heat Number (simplistic check)
    heat_number = parsed_data.get("heat_number")
    if heat_number and str(heat_number).lower() != "unknown":
        if database.check_duplicate_heat(str(heat_number)):
            alerts.append(f"🚨 Duplicate Heat Number detected: {heat_number}. Potential forgery or reuse!")
            is_risk = True

    # 3. Abnormal Values (Heuristic checks)
    # E.g., Yield Strength exactly equal to Tensile Strength is highly suspicious
    ys = parsed_data.get("yield_strength")
    ts = parsed_data.get("tensile_strength")
    
    try:
        if ys and ts:
            y_val = float(str(ys).replace("MPa", "").strip())
            t_val = float(str(ts).replace("MPa", "").strip())
            
            if y_val == t_val:
                alerts.append("🚨 Abnormal Values: Yield Strength equals Tensile Strength. Highly suspicious.")
                is_risk = True
            
            if y_val > t_val:
                 alerts.append("🚨 Abnormal Values: Yield Strength > Tensile Strength. Physically impossible.")
                 is_risk = True
                 
            # E.g. extremely perfect numbers (exactly 300.00) might be generated
            if y_val % 100 == 0:
                 alerts.append(f"⚠ Yield Strength is exactly {y_val}. Proceed with caution.")
    except Exception:
        pass # Parsing failures handle gracefully

    return {
        "is_fraud_risk": is_risk,
        "alerts": alerts
    }
