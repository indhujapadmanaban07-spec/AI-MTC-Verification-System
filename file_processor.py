import io
import cv2
import numpy as np
from PIL import Image
import pdf2image

def convert_to_images(file_bytes: bytes, file_type: str):
    """
    Converts input bytes to a list of PIL Images.
    Supports PDF and standard image formats.
    """
    images = []
    if file_type.lower() == 'pdf':
        try:
            # Use poppler to convert pdf to images
            images = pdf2image.convert_from_bytes(file_bytes)
        except Exception as e:
            print(f"Error converting PDF to image: {e}")
            raise e
    elif file_type.lower() in ['jpg', 'jpeg', 'png', 'tiff', 'tif']:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            images = [image]
        except Exception as e:
            print(f"Error opening image: {e}")
            raise e
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    return images


def preprocess_for_ocr(pil_image: Image.Image) -> Image.Image:
    """
    Preprocess image for better OCR accuracy.
    Applies grayscale, noise reduction, thresholding, contrast, and deskew.
    """
    # Convert PIL Image to OpenCV format (numpy array)
    open_cv_image = np.array(pil_image)
    if len(open_cv_image.shape) == 3 and open_cv_image.shape[2] == 3:
        # Convert RGB to BGR for OpenCV
        open_cv_image = open_cv_image[:, :, ::-1].copy()

    # 1. Grayscale
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    # 2. Deskewing (Basic rotation correction)
    # Grab the (x, y) coordinates of all pixel values that are greater than zero
    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]
    # Handle angle based on OpenCV version
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) > 0.5 and abs(angle) < 45: # Only deskew small angles
        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # 3. Noise Reduction (Gaussian Blur)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 4. Adaptive Thresholding
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Convert back to PIL Image
    # Adaptive threshold returns a single-channel image. We convert it to PIL "L" mode
    processed_pil = Image.fromarray(thresh)
    return processed_pil

