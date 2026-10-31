from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdftypes import resolve1
import io

SUSPICIOUS_TOOLS = [
    "photoshop", "illustrator", "coreldraw", "gimp", 
    "canva", "indesign", "paint", "pdfeditor", "foxit phantompdf", "nitro pro"
]

def analyze_metadata(file_bytes: bytes, file_type: str) -> dict:
    """
    Extracts and analyzes PDF metadata using pdfminer.six.
    Checks for signs of visual editing software.
    """
    if file_type.lower() != 'pdf':
         return {
             "has_metadata": False,
             "alerts": [],
             "metadata": {}
         }
         
    alerts = []
    metadata = {}
    
    try:
        parser = PDFParser(io.BytesIO(file_bytes))
        doc = PDFDocument(parser)
        
        info = doc.info[0] if doc.info else {}
        
        for k, v in info.items():
            # Resolve PDF objects to strings
            try:
                val = resolve1(v)
                if hasattr(val, 'decode'):
                    # Some values are encoded in UTF-16
                    try:
                        str_val = val.decode('utf-16')
                    except Exception:
                        try:
                            str_val = val.decode('utf-8')
                        except Exception:
                            str_val = str(val)
                else:
                    str_val = str(val)
                    
                metadata[k] = str_val
                
                # Check for suspicious editing tools
                if k.lower() in ['creator', 'producer']:
                    if any(tool in str_val.lower() for tool in SUSPICIOUS_TOOLS):
                        alerts.append(f"Suspicious editing software found in {k}: '{str_val}'")
            except Exception as inner_e:
                print(f"Error parsing metadata key {k}: {inner_e}")
                
    except Exception as e:
         print(f"Error reading PDF metadata: {e}")
         return {
             "has_metadata": False,
             "alerts": [f"Could not read PDF metadata: {e}"],
             "metadata": {}
         }
         
    return {
        "has_metadata": True,
        "alerts": alerts,
        "metadata": metadata
    }
