def calculate_authenticity(
        extracted_data: dict,
        validation_results: dict,
        qr_results: dict,
        metadata_results: dict,
        ela_results: dict,
        heat_results: dict
    ) -> dict:
    """
    Calculates unified Authenticity Score out of 100.
    """
    score = 100.0
    deductions = []
    
    # 1. OCR Failure Checks (Missing critical fields)
    if "fallback" in extracted_data:
         score -= 20.0
         deductions.append("-20: Using dummy fallback data instead of actual extraction.")
    elif "error" in extracted_data:
         score -= 100.0
         deductions.append("-100: Total OCR Failure.")
    else:
        # Check critical fields
        missing_fields = []
        for field in ["supplier_name", "material_grade", "heat_number"]:
             val = extracted_data.get(field)
             if not val or str(val).lower() == "unknown":
                 missing_fields.append(field)
                 
        if missing_fields:
             penalty = 10 * len(missing_fields)
             score -= penalty
             deductions.append(f"-{penalty}: Missing critical OCR fields ({', '.join(missing_fields)}).")

    # 2. ASTM Standards Validation
    if not validation_results.get("is_compliant", False):
         # The Validation Engine returns 'valid_score'. If it's low, apply penalty.
         valid_score = validation_results.get("valid_score", 100.0)
         if valid_score < 100:
              diff = (100.0 - valid_score) * 0.5  # Penalize 50% of the ASTM validation drop
              score -= diff
              deductions.append(f"-{diff:.1f}: Material properties out of standard ranges.")
              
    # 3. QR Verification
    if qr_results.get("qr_found"):
         if qr_results.get("match_status") == "Fail":
              score -= 30.0
              deductions.append("-30: QR code data does not match document contents.")
         # If it passes, it validates authenticity (no deduction, optionally small bonus but bounded at 100)
    else:
         score -= 5.0
         deductions.append("-5: No QR Code found.")
         
    # 4. Heat Number Format
    if heat_results and not heat_results.get("is_valid", True):
         score -= 15.0
         deductions.append(f"-15: Invalid Heat Number Format ({heat_results.get('reason')}).")

    # 5. Metadata Suspicion
    if metadata_results.get("alerts"):
         score -= 25.0
         deductions.append("-25: Suspicious PDF editing software detected in metadata.")
         
    # 6. ELA Forgery Detection
    if ela_results.get("is_tampered"):
         score -= 35.0
         deductions.append("-35: Error Level Analysis detected digital tampering/forgery.")
         
    # Clamp score
    score = max(0.0, min(100.0, score))
    
    # Determine Risk Level
    if score >= 85:
        risk_level = "LOW"
    elif score >= 60:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"
        
    return {
        "authenticity_score": score,
        "risk_level": risk_level,
        "deductions": deductions
    }
