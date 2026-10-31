from pyzbar.pyzbar import decode
from PIL import Image
import json

def scan_for_qr(image: Image.Image) -> list:
    """
    Scans a PIL Image for QR codes.
    Returns a list of decoded strings.
    """
    decoded_objects = decode(image)
    qr_data_list = []
    
    for obj in decoded_objects:
        try:
            # Decode payload from bytes to string
            payload = obj.data.decode('utf-8')
            qr_data_list.append(payload)
        except Exception as e:
            print(f"Failed to decode QR: {e}")
            
    return qr_data_list

def verify_qr_data(ocr_data: dict, images: list) -> dict:
    """
    Scans all uploaded images for QR codes and compares payload with OCR data.
    """
    all_qr_payloads = []
    for img in images:
        payloads = scan_for_qr(img)
        all_qr_payloads.extend(payloads)
        
    if not all_qr_payloads:
        return {
            "qr_found": False,
            "match_status": "Not Found",
            "alerts": ["No QR code found on document."],
            "qr_data": None
        }
        
    # Try to parse QR data as JSON or Key-Value
    parsed_qr = {}
    raw_payload = all_qr_payloads[0] # Take first valid QR
    
    try:
        parsed_qr = json.loads(raw_payload)
    except json.JSONDecodeError:
        # If not JSON, try simple key-value parsing (e.g. Heat: 12345, Grade: 304)
        lines = raw_payload.split(',')
        for line in lines:
            if ':' in line:
                k, v = line.split(':', 1)
                parsed_qr[k.strip().lower().replace(" ", "_")] = v.strip()
    
    # If we still haven't parsed anything useful, just store the raw
    if not parsed_qr:
        parsed_qr = {"raw_text": raw_payload}
        
    # Compare against OCR Data
    alerts = []
    match_status = "Pass"
    
    if "heat_number" in parsed_qr and "heat_number" in ocr_data:
        if str(parsed_qr["heat_number"]).lower() != str(ocr_data["heat_number"]).lower():
            alerts.append(f"Heat Number mismatch! QR: {parsed_qr['heat_number']}, OCR: {ocr_data['heat_number']}")
            match_status = "Fail"
            
    if "material_grade" in parsed_qr and "material_grade" in ocr_data:
        if str(parsed_qr["material_grade"]).lower() != str(ocr_data["material_grade"]).lower():
            alerts.append(f"Grade mismatch! QR: {parsed_qr['material_grade']}, OCR: {ocr_data['material_grade']}")
            match_status = "Fail"
            
    # If no checks failed, but we found a QR, it passes
    if match_status == "Pass" and not alerts:
        alerts.append("QR data matches document contents.")
        
    return {
        "qr_found": True,
        "match_status": match_status,
        "alerts": alerts,
        "qr_data": parsed_qr
    }
