"""
Captcha OCR Recognition Script
Simplified approach based on pht_tsr.py analysis
"""

import cv2
import pytesseract
import numpy as np
import base64
from PIL import Image
import io
import os
import sys

# Add tes_port to PATH and set tesseract command
os.environ['PATH'] = os.path.abspath('tes_port') + os.pathsep + os.environ.get('PATH', '')
pytesseract.tesseract_cmd = os.path.abspath('tes_port/tesseract.exe')

def recognize_captcha(image_data, method='base64'):
    """
    Simple captcha recognition using the same approach as pht_tsr.py
    """
    try:
        # Convert base64 to image file (like pht_tsr.py expects)
        if method == 'base64':
            # Remove data URL prefix if present
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # Decode base64 to image
            image_bytes = base64.b64decode(image_data)
            image_pil = Image.open(io.BytesIO(image_bytes))
            
            # Convert PIL to OpenCV format (same as cv2.imread result)
            image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
            
        elif method == 'file':
            # Load directly like pht_tsr.py
            image = cv2.imread(image_data)
            
        if image is None:
            return {
                "success": False,
                "text": "",
                "confidence": 0,
                "error": "Failed to load image"
            }
        
        # Use the EXACT same approach as pht_tsr.py
        text = pytesseract.image_to_string(image).strip()
        
        # Clean the text (remove non-alphanumeric characters)
        cleaned_text = ''.join(char for char in text if char.isalnum()).upper()
        
        print(f"Raw OCR output: '{text}'")
        print(f"Cleaned text: '{cleaned_text}'")
        
        # Calculate a simple confidence based on text length and characters
        confidence = 85 if len(cleaned_text) >= 4 and cleaned_text.isalnum() else 50
        
        return {
            "success": True,
            "text": cleaned_text.lower(),
            "confidence": confidence,
            "length": len(cleaned_text),
            "raw_text": text
        }
        
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return {
            "success": False,
            "text": "",
            "confidence": 0,
            "error": f"OCR failed: {str(e)}"
        }

def main():
    """
    Main function for testing the OCR functionality
    Can be called from command line with image path
    """
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        if os.path.exists(image_path):
            result = recognize_captcha(image_path, method='file')
            print(f"Recognition Result: {result}")
        else:
            print(f"Image file not found: {image_path}")
    else:
        print("Usage: python captcha_recognizer.py <image_path>")
        print("Or import this module to use recognize_captcha() function")

if __name__ == "__main__":
    main()