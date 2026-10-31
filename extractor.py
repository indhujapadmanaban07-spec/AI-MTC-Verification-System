import os
import json
import google.generativeai as genai
from PIL import Image
import pdf2image
import io

def initialize_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

def _process_pdf_to_image(file_bytes: bytes) -> Image.Image:
    # Convert first page of PDF to image using pdf2image
    try:
        images = pdf2image.convert_from_bytes(file_bytes, first_page=1, last_page=1)
        if images:
            return images[0]
    except Exception as e:
        print(f"Error converting PDF to image: {e}")
    return None

def extract_mtc_data(file_bytes: bytes, file_type: str) -> dict:
    """
    Extracts structured data from an MTC using Gemini Pro Vision.
    File type can be 'pdf', 'png', 'jpg', 'jpeg'.
    """
    if not initialize_gemini():
        # Fallback to dummy data if no API key is set for demonstration purposes
        print("Gemini API key not found. Returning dummy extraction data.")
        return get_dummy_data()

    try:
        image = None
        if file_type == 'pdf':
            image = _process_pdf_to_image(file_bytes)
        else:
            image = Image.open(io.BytesIO(file_bytes))
            
        if not image:
            return {"error": "Could not process image."}

        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = """
        Analyze this Material Test Certificate (MTC) and extract the following parameters as a structured JSON object. 
        DO NOT wrap the response in markdown blocks like ```json.
        Return ONLY the raw JSON string.

        Required fields:
        "material_grade": The grade of the material (e.g., 304, 316L, ASTMA240, EN 10204 3.1). Look for headers like 'Grade', 'Material', 'Specification'.
        "heat_number": The unique heat/cast/melt number. Look for 'Heat No', 'Cast No', 'Melt No', 'Lot No'.
        "supplier_name": The name of the company that issued the certificate.
        "yield_strength": The numerical value of the Yield Strength (YS). Only return the number, no units. Include decimals.
        "tensile_strength": The numerical value of the Tensile Strength (TS/UTS). Only return the number, no units. Include decimals.
        "chemical_composition": A nested JSON object of chemical elements. The keys should be standard element symbols (C, Mn, P, S, Si, Cr, Ni, Mo, etc.). The values should be numerical floats (e.g., {"C": 0.05, "Cr": 18.2}).

        If a field cannot be found, set its value to null. Make sure data types are correct (strings for text, numbers for physics values).
        """
        
        response = model.generate_content([prompt, image])
        text_resp = response.text.strip()
        
        # Clean up if Gemini accidentally returned markdown blocks
        if text_resp.startswith("```json"):
            text_resp = text_resp[7:]
        if text_resp.endswith("```"):
            text_resp = text_resp[:-3]
            
        parsed_json = json.loads(text_resp.strip())
        return parsed_json
        
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {"error": str(e), "fallback": get_dummy_data()}
        
def get_dummy_data():
    """Dummy data for demonstration when API is unavailable"""
    return {
        "material_grade": "304",
        "heat_number": "HT-89241X",
        "supplier_name": "Premium Steel Corp",
        "yield_strength": 260.5,
        "tensile_strength": 550.0,
        "chemical_composition": {
            "C": 0.06,
            "Mn": 1.5,
            "P": 0.03,
            "S": 0.015,
            "Si": 0.5,
            "Cr": 18.5,
            "Ni": 9.2
        }
    }
