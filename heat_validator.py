import re

def validate_heat_format(heat_number: str) -> dict:
    """
    Validates a heat number format.
    Checks length, alphanumerics, and generic patterns.
    """
    if not heat_number or heat_number.upper() == 'UNKNOWN':
        return {"is_valid": False, "reason": "Heat number is missing or unknown."}
    
    heat_clean = str(heat_number).strip().upper()
    
    # Needs to be at least 3 characters and at most 20
    if len(heat_clean) < 3:
        return {"is_valid": False, "reason": "Heat number is too short (less than 3 chars)."}
    if len(heat_clean) > 20:
        return {"is_valid": False, "reason": "Heat number is too long (over 20 chars)."}
        
    # Check if composed of alphanumeric characters (allow dashes and slashes)
    if not re.match(r'^[-/A-Z0-9]+$', heat_clean):
        return {"is_valid": False, "reason": "Contains invalid characters (only alphanumeric, dashes, and slashes allowed)."}
        
    # Has at least one letter and at least one digit
    has_letter = any(char.isalpha() for char in heat_clean)
    has_digit = any(char.isdigit() for char in heat_clean)
    
    if not has_letter and not has_digit:
         return {"is_valid": False, "reason": "Format is invalid, must contain at least numbers."}
         
    return {"is_valid": True, "reason": "Format is standard.", "formatted": heat_clean}

def match_with_qr_data(heat_number: str, qr_payload: dict) -> dict:
    """
    Compare OCR heat number with QR data heat number if available.
    """
    qr_heat = qr_payload.get("heat_number", "")
    
    if not qr_heat:
        return {"match": None, "message": "No heat number found in QR."}
        
    if str(heat_number).strip().upper() == str(qr_heat).strip().upper():
        return {"match": True, "message": "Heat number matches QR Data."}
    else:
        return {"match": False, "message": f"Mismatch! OCR: {heat_number}, QR: {qr_heat}"}
