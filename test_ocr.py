"""
Test script to debug OCR functionality
"""

import cv2
import pytesseract
from captcha_recognizer import recognize_captcha
import base64
import os

# Add tes_port to PATH and set tesseract command
os.environ['PATH'] = os.path.abspath('tes_port') + os.pathsep + os.environ.get('PATH', '')
pytesseract.tesseract_cmd = os.path.abspath('tes_port/tesseract.exe')

def test_ocr():
    """Test OCR with a simple approach"""
    
    # Test if Tesseract is working
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
    except Exception as e:
        print(f"❌ Tesseract not working: {e}")
        return
    
    # Create a simple test image with text
    import numpy as np
    
    # Create a white image with black text
    img = np.ones((100, 300, 3), dtype=np.uint8) * 255
    cv2.putText(img, 'TEST123', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    # Save test image
    cv2.imwrite('test_captcha.png', img)
    print("📝 Created test image: test_captcha.png")
    
    # Test OCR on the image
    try:
        text = pytesseract.image_to_string(img).strip()
        print(f"🔍 OCR Result: '{text}'")
        
        # Clean the text
        cleaned = ''.join(char for char in text if char.isalnum()).upper()
        print(f"🧹 Cleaned Result: '{cleaned}'")
        
        # Test our function
        print("\n--- Testing our recognize_captcha function ---")
        result = recognize_captcha('test_captcha.png', method='file')
        print(f"📊 Function Result: {result}")
        
    except Exception as e:
        print(f"❌ OCR Test Failed: {e}")

if __name__ == "__main__":
    test_ocr()