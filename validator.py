from typing import Dict, Any

# Simplified Material Standards Database
# In reality, this would be a much larger config or database table.
STANDARDS = {
    # e.g., Grade 304 Stainless Steel
    "304": {
        "yield_strength_min": 205.0,  # MPa
        "tensile_strength_min": 515.0, # MPa
        "chemistry": {
            "C_max": 0.08,
            "Mn_max": 2.0,
            "P_max": 0.045,
            "S_max": 0.03,
            "Si_max": 0.75,
            "Cr_min": 18.0,
            "Cr_max": 20.0,
            "Ni_min": 8.0,
            "Ni_max": 10.5
        }
    },
    "316": {
        "yield_strength_min": 205.0,
        "tensile_strength_min": 515.0,
        "chemistry": {
            "C_max": 0.08,
            "Mn_max": 2.0,
            "P_max": 0.045,
            "S_max": 0.03,
            "Si_max": 0.75,
            "Cr_min": 16.0,
            "Cr_max": 18.0,
            "Ni_min": 10.0,
            "Ni_max": 14.0,
            "Mo_min": 2.0,
            "Mo_max": 3.0
        }
    }
}

def validate_mtc_data(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates parsed parameters against standard ranges.
    Returns the updated dictionary containing compliance score and reasoning.
    """
    grade = str(parsed_data.get("material_grade", "")).strip().upper()
    
    # Simple mapping
    std = None
    if "304" in grade:
        std = STANDARDS["304"]
    elif "316" in grade:
        std = STANDARDS["316"]
        
    reasoning = []
    points_total = 0
    points_earned = 0
    
    ys = parsed_data.get("yield_strength")
    ts = parsed_data.get("tensile_strength")
    chem = parsed_data.get("chemical_composition", {})

    if not std:
        # Cannot validate against specific standard
        reasoning.append(f"⚠ Unknown or unsupported Material Grade: '{grade}'. Cannot perform standard validation.")
        return {
            "valid_score": 0.0,
            "reasoning": reasoning,
            "is_compliant": False
        }

    # Yield Strength
    if ys is not None:
        points_total += 1
        # Handle string like '250 MPa' or float
        try:
            val = float(str(ys).replace("MPa", "").replace("N/mm2", "").strip())
            if val >= std["yield_strength_min"]:
                points_earned += 1
                reasoning.append(f"✅ Yield Strength {val} MPa >= Required {std['yield_strength_min']} MPa")
            else:
                reasoning.append(f"❌ Yield Strength {val} MPa < Required {std['yield_strength_min']} MPa")
        except ValueError:
            reasoning.append(f"⚠ Could not parse Yield Strength value: {ys}")

    # Tensile Strength
    if ts is not None:
        points_total += 1
        try:
            val = float(str(ts).replace("MPa", "").replace("N/mm2", "").strip())
            if val >= std["tensile_strength_min"]:
                points_earned += 1
                reasoning.append(f"✅ Tensile Strength {val} MPa >= Required {std['tensile_strength_min']} MPa")
            else:
                reasoning.append(f"❌ Tensile Strength {val} MPa < Required {std['tensile_strength_min']} MPa")
        except ValueError:
            reasoning.append(f"⚠ Could not parse Tensile Strength value: {ts}")

    # Chemistry Rules
    for el, val_str in chem.items():
        try:
            val = float(val_str)
        except (ValueError, TypeError):
            continue
            
        points_total += 1
        
        passed_el = True
        min_key = f"{el}_min"
        max_key = f"{el}_max"
        
        if min_key in std["chemistry"]:
            if val < std["chemistry"][min_key]:
                passed_el = False
                reasoning.append(f"❌ {el} {val}% < Required Min {std['chemistry'][min_key]}%")
        if max_key in std["chemistry"]:
            if val > std["chemistry"][max_key]:
                passed_el = False
                reasoning.append(f"❌ {el} {val}% > Required Max {std['chemistry'][max_key]}%")
                
        if passed_el:
            points_earned += 1
            reasoning.append(f"✅ {el} {val}% is within acceptable range")

    if points_total == 0:
        compliance_score = 0.0
        reasoning.append("⚠ No valid quantitative parameters found to validate.")
    else:
        compliance_score = (points_earned / points_total) * 100.0

    return {
        "valid_score": compliance_score,
        "reasoning": reasoning,
        "is_compliant": compliance_score == 100.0
    }
