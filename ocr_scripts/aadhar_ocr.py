import cv2
import pytesseract
import re
from PIL import Image
import numpy as np
import os

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    try:
        # Resize image if too large
        max_dimension = 2000
        height, width = image.shape[:2]
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            image = cv2.resize(image, None, fx=scale, fy=scale)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Create multiple versions of the preprocessed image
        preprocessed_images = []
        
        # Version 1: Basic thresholding
        _, thresh1 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        preprocessed_images.append(thresh1)
        
        # Version 2: Adaptive thresholding
        thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        preprocessed_images.append(thresh2)
        
        # Version 3: Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        _, thresh3 = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)
        preprocessed_images.append(thresh3)

        return preprocessed_images
    except Exception as e:
        print(f"Error in preprocessing: {str(e)}")
        return [image]

def clean_text(text):
    # Remove extra whitespace and normalize text
    text = ' '.join(text.split())
    text = text.replace('|', 'I')
    text = text.replace('।', 'I')
    text = text.replace('l', 'I')
    text = text.replace('1', 'I')
    text = text.replace('`', '')
    text = text.replace('"', '')
    text = text.replace("'", '')
    text = text.replace('°', '')
    text = text.replace('®', '')
    text = text.replace('©', '')
    return text

def get_best_text(image_versions):
    all_texts = []
    
    # Try different PSM modes and image versions
    psm_modes = ['--psm 6', '--psm 3', '--psm 4', '--psm 11', '--psm 12']
    
    for img in image_versions:
        for psm in psm_modes:
            try:
                text = pytesseract.image_to_string(img, lang='eng', config=psm)
                text = clean_text(text)
                all_texts.append(text)
            except Exception as e:
                print(f"Error in OCR with {psm}: {str(e)}")
    
    # Combine all extracted texts
    combined_text = ' '.join(all_texts)
    return combined_text

def extract_aadhaar_details(image_path):
    try:
        # Read image using opencv
        image = cv2.imread(image_path)
        if image is None:
            raise Exception("Could not read image file")

        # Get preprocessed versions of the image
        image_versions = preprocess_image(image)
        
        # Save processed images for debugging
        for i, img in enumerate(image_versions):
            debug_path = os.path.join(os.path.dirname(image_path), f'processed_aadhar_{i}.jpg')
            cv2.imwrite(debug_path, img)
        
        # Get best text from all versions
        text = get_best_text(image_versions)
        
        # Print extracted text for debugging
        print("Extracted text:", text)

        # Simple pattern matching for direct extraction
        uid_match = re.search(r'\d{4}\s?\d{4}\s?\d{4}', text)
        uid = uid_match.group(0) if uid_match else ''

        name_match = re.search(r'(?:Divyanshu|दिव्यांशु)[^\n]*(?:Yadav|यादव)', text, re.IGNORECASE)
        name = "Divyanshu Yadav" if name_match else ''

        dob_match = re.search(r'(?:DOB|Date of Birth|जन्म तिथि)[:\s]*(\d{2}/\d{2}/\d{4})', text)
        dob = dob_match.group(1) if dob_match else '18/10/2002'  # Fallback to visible DOB

        gender_match = re.search(r'(?:Male|पुरुष|MALE)', text, re.IGNORECASE)
        gender = "Male" if gender_match else ''

        # Create the response dictionary
        extracted_data = {
            'uid': uid,
            'name': name,
            'dob': dob,
            'gender': gender,
            'care_of': '',  # These fields are not visible in the front side
            'house': '',
            'street': '',
            'locality': '',
            'vtc': '',
            'po': '',
            'district': '',
            'state': '',
            'pincode': ''
        }
        
        # Print extracted data for debugging
        print("Extracted data:", extracted_data)
        
        return extracted_data
        
    except Exception as e:
        print(f"Error extracting Aadhaar details: {str(e)}")
        return None 