from PIL import Image, ImageChops, ImageEnhance
import io
import numpy as np

def detect_ela(image: Image.Image) -> dict:
    """
    Performs Error Level Analysis (ELA) to detect image forgery.
    Returns the analysis result including tampered status and the ELA heatmap.
    """
    # Ensure image is in RGB mode for consistent diff
    original = image.convert('RGB')
    
    # 1. Resave the image at 90% quality
    buffer = io.BytesIO()
    original.save(buffer, 'JPEG', quality=90)
    resaved = Image.open(buffer)
    
    # 2. Compute absolute difference between original and resaved image
    ela_image = ImageChops.difference(original, resaved)
    
    # 3. Enhance difference
    extrema = ela_image.getextrema()
    max_diff = 1
    if extrema:
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
            
        scale = 255.0 / max_diff
        ela_image = ImageEnhance.Brightness(ela_image).enhance(scale)
        
    # Analyze the ELA block wise for anomalies (simple threshold implementation)
    # A single high diff block could be a text insertion
    # Let's use max_diff as a heuristic threshold for simplicity:
    # JPEG uniform compression should keep diffs relatively tight. High maximum diff indicates tampering.
    is_tampered = False
    alerts = []
    
    if max_diff > 35:
        is_tampered = True
        alerts.append("High ELA variance detected. Document may have been digitally altered.")
        
    # Save ELA visualization into bytes for UI display
    ela_buffer = io.BytesIO()
    ela_image.save(ela_buffer, format="PNG")
    ela_bytes = ela_buffer.getvalue()
    
    return {
        "is_tampered": is_tampered,
        "max_difference": max_diff,
        "heatmap_bytes": ela_bytes,
        "alerts": alerts
    }
