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
        
        # Apply adaptive thresholding
        threshold = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(threshold)
        
        return denoised
    except Exception as e:
        print(f"Error in preprocessing: {str(e)}")
        return image

def clean_text(text):
    # Remove extra whitespace and normalize text
    text = ' '.join(text.split())
    text = text.replace('|', 'I')  # Common OCR mistake
    return text

def extract_aadhaar_details(image_path):
    try:
        # Read image using opencv
        image = cv2.imread(image_path)
        if image is None:
            raise Exception("Could not read image file")

        # Preprocess the image
        processed_image = preprocess_image(image)
        
        # Save processed image for debugging
        debug_path = os.path.join(os.path.dirname(image_path), 'processed_aadhar.jpg')
        cv2.imwrite(debug_path, processed_image)
        
        # Extract text from image
        text = pytesseract.image_to_string(processed_image, lang='eng', config='--psm 6')
        text = clean_text(text)
        
        # Print extracted text for debugging
        print("Extracted text:", text)
        
        # Define regex patterns for different fields
        patterns = {
            'uid': r'\d{4}\s?\d{4}\s?\d{4}',
            'name': r'(?:Name|नाम)[:\s]+([^\n\d]+)',
            'gender': r'(?:(?:Gender|GENDER|Sex|लिंग)[:\s]+)(MALE|FEMALE|Male|Female|M|F)',
            'dob': r'(?:DOB|Date of Birth|Year of Birth|जन्म तिथि)[:\s]+[\d-/]+',
            'care_of': r'(?:(?:C/O|S/O|D/O|W/O|Son of|Daughter of|Wife of)[:\s]+)([^\n\d]+)',
            'house': r'(?:(?:House No|Ghar|घर)[:\s.,]+)([^,\n]+)',
            'street': r'(?:(?:Street|Road|Gali|सड़क)[:\s.,]+)([^,\n]+)',
            'locality': r'(?:(?:Locality|Area|क्षेत्र)[:\s.,]+)([^,\n]+)',
            'vtc': r'(?:(?:VTC|Village|Town|City|गाँव|शहर)[:\s.,]+)([^,\n]+)',
            'po': r'(?:(?:Post Office|PO|डाकघर)[:\s.,]+)([^,\n]+)',
            'district': r'(?:(?:District|जिला)[:\s.,]+)([^,\n]+)',
            'state': r'(?:(?:State|राज्य)[:\s.,]+)([^,\n]+)',
            'pincode': r'(?:(?:Pincode|PIN Code|पिन कोड)[:\s.,]+)?(\d{6})'
        }
        
        # Extract information using regex
        extracted_data = {}
        for key, pattern in patterns.items():
            try:
                matches = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # If the pattern has a group, take the first group, otherwise take the full match
                    value = matches.group(1) if len(matches.groups()) > 0 else matches.group(0)
                    extracted_data[key] = value.strip()
                else:
                    extracted_data[key] = ''
            except Exception as e:
                print(f"Error extracting {key}: {str(e)}")
                extracted_data[key] = ''
        
        # Print extracted data for debugging
        print("Extracted data:", extracted_data)
        
        return extracted_data
        
    except Exception as e:
        print(f"Error extracting Aadhaar details: {str(e)}")
        return None 