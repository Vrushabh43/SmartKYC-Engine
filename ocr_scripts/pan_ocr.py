import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
import re
#Tesseract Library
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

import cv2
import matplotlib.pyplot as plt
from PIL import Image
import os

### Make prettier the prints ###
from colorama import Fore, Style
c_ = Fore.CYAN
m_ = Fore.MAGENTA
r_ = Fore.RED
b_ = Fore.BLUE
y_ = Fore.YELLOW
g_ = Fore.GREEN
w_ = Fore.WHITE

import warnings
warnings.filterwarnings(action='ignore') 

def preprocess_image(image):
    """Preprocess image for better OCR results"""
    try:
        # Resize image if too large
        max_dimension = 2000
        height, width = image.shape[:2]
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            image = cv2.resize(image, None, fx=scale, fy=scale)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        preprocessed_images = []
        
        # Version 1: Basic thresholding
        _, thresh1 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        preprocessed_images.append(thresh1)
        
        # Version 2: Adaptive thresholding
        thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        preprocessed_images.append(thresh2)
        
        # Version 3: Denoising + Thresholding
        denoised = cv2.fastNlMeansDenoising(gray)
        _, thresh3 = cv2.threshold(denoised, 127, 255, cv2.THRESH_BINARY)
        preprocessed_images.append(thresh3)
        
        # Version 4: Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        _, thresh4 = cv2.threshold(enhanced, 127, 255, cv2.THRESH_BINARY)
        preprocessed_images.append(thresh4)
        
        # Version 5: Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        _, thresh5 = cv2.threshold(sharpened, 127, 255, cv2.THRESH_BINARY)
        preprocessed_images.append(thresh5)

        return preprocessed_images
    except Exception as e:
        print(f"Error in preprocessing: {str(e)}")
        return [image]

def clean_text(text):
    # Remove extra whitespace and normalize text
    text = ' '.join(text.split())
    
    # Replace common OCR mistakes
    text = text.replace('|', 'I')
    text = text.replace('।', 'I')
    text = text.replace('l', 'I')
    text = text.replace('`', '')
    text = text.replace('"', '')
    text = text.replace("'", '')
    text = text.replace('°', '')
    text = text.replace('®', '')
    text = text.replace('©', '')
    
    # Remove any non-alphanumeric characters except spaces and slashes (for dates)
    text = re.sub(r'[^\w\s/-]', '', text)
    
    return text.strip()

def get_best_text(image_versions):
    """Get best text from multiple image versions"""
    all_texts = []
    
    # Configure Tesseract parameters for better accuracy
    custom_config = r'--oem 3 --psm 6 -l eng+hin'
    
    for img in image_versions:
        try:
            # Convert to PIL Image for Tesseract
            pil_img = Image.fromarray(img)
            
            # Get text from Tesseract
            text = pytesseract.image_to_string(pil_img, config=custom_config)
            text = clean_text(text)
            all_texts.append(text)
            
            # Try different PSM modes
            for psm in [3, 4, 11, 12]:
                config = f'--oem 3 --psm {psm} -l eng+hin'
                text = pytesseract.image_to_string(pil_img, config=config)
                text = clean_text(text)
                all_texts.append(text)
                
        except Exception as e:
            print(f"Error in OCR: {str(e)}")
            continue
    
    # Combine all extracted texts
    return '\n'.join(all_texts)

def clean_name(text):
    """Clean and normalize name text"""
    if not text:
        return ''
    
    # Convert to uppercase and remove extra spaces
    text = text.upper().strip()
    
    # Remove common noise words and headers
    noise_words = [
        'PERMANENT', 'ACCOUNT', 'NUMBER', 'SIGNATURE', 'INCOME', 'TAX', 
        'DEPARTMENT', 'GOVT', 'OF', 'INDIA', 'FATHER', 'NAME', 'DATE',
        'BIRTH', 'PAN', 'CARD', 'UE', 'TIS', 'EAE', 'BNEI', 'ENE', 'ES',
        'FRAT', 'ATA', 'AFT', 'ARTA', 'LG', 'ORA', 'SASS', 'RR', 'ESS'
    ]
    
    # Split into words and filter
    words = text.split()
    filtered_words = []
    
    for word in words:
        # Skip noise words
        if word in noise_words:
            continue
        # Skip words that are too short
        if len(word) < 2:
            continue
        # Skip words that look like dates
        if re.match(r'\d{2}[/-]\d{2}[/-]\d{4}', word):
            continue
        # Skip words that are just numbers
        if word.isdigit():
            continue
        # Skip words with mixed numbers and letters (likely noise)
        if re.search(r'\d', word):
            continue
        filtered_words.append(word)
    
    # Join filtered words
    text = ' '.join(filtered_words)
    
    # Remove any remaining special characters
    text = re.sub(r'[^A-Z\s]', '', text)
    
    # Remove extra spaces
    text = ' '.join(text.split())
    
    return text

def find_repeated_name(text):
    """Find names that appear multiple times in the text"""
    words = text.split()
    candidates = []
    
    # Look for 2-3 word combinations that appear multiple times
    for i in range(len(words)):
        for j in range(i+2, min(i+4, len(words))):
            name = ' '.join(words[i:j])
            if len(name.split()) >= 2 and text.count(name) >= 2:
                candidates.append((name, text.count(name)))
    
    # Sort by length (prefer longer names) and frequency
    candidates.sort(key=lambda x: (len(x[0].split()), x[1]), reverse=True)
    return candidates[0][0] if candidates else ''

def extract_name_and_father_name(text):
    """Extract name and father's name using multiple approaches"""
    name = ''
    father_name = ''
    
    # Split text into lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Patterns for different PAN card formats
    name_patterns = [
        r'(?:Name|नाम)[:\s]*(.*?)(?=(?:Father|पिता|Date|जन्म|$))',
        r'(?:^|\n)([A-Z\s]{3,}?)(?=\s*(?:Father|पिता|Date|जन्म|$))',
        r'(?:^|\n)([A-Z][A-Z\s]{2,}[A-Z])(?=\s|$)'
    ]
    
    father_patterns = [
        r'(?:Father|पिता)(?:[\'S]*\s*Name|[:\s]+का\s+नाम)[:\s]*(.*?)(?=(?:Date|जन्म|$))',
        r'(?:Father|पिता)[\'S]*\s*Name[:\s]*(.*?)(?=\s*(?:Date|जन्म|$))',
        r'(?<=\n)([A-Z][A-Z\s]{2,}[A-Z])(?=\s|$)'
    ]
    
    # Try to find name using patterns
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip()
            name = clean_name(name)
            if len(name.split()) >= 2:  # Ensure name has at least two words
                break
    
    # Try to find father's name using patterns
    for pattern in father_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            father_name = match.group(1).strip()
            father_name = clean_name(father_name)
            if len(father_name.split()) >= 2:  # Ensure father's name has at least two words
                break
    
    # If patterns didn't work, try line-by-line analysis
    if not name or not father_name:
        name_candidates = []
        father_candidates = []
        
        for line in lines:
            # Skip lines with common headers or dates
            if any(word.lower() in line.lower() for word in ['income', 'tax', 'department', 'permanent', 'card', 'govt', 'india', '/']):
                continue
            
            # Clean the line
            cleaned_line = clean_name(line)
            if not cleaned_line:
                continue
            
            # Look for lines with all caps and proper length
            if len(cleaned_line.split()) >= 2:
                if 'FATHER' in line or 'पिता' in line:
                    father_candidates.append(cleaned_line)
                else:
                    name_candidates.append(cleaned_line)
        
        # Select best candidates
        if name_candidates and not name:
            # Prefer longer names (more likely to be complete)
            name_candidates.sort(key=lambda x: len(x.split()), reverse=True)
            name = name_candidates[0]
        
        if father_candidates and not father_name:
            father_candidates.sort(key=lambda x: len(x.split()), reverse=True)
            father_name = father_candidates[0]
        elif name_candidates and not father_name and len(name_candidates) > 1:
            # If we have multiple name candidates, use the second one for father's name
            father_name = name_candidates[1]
    
    # Final validation and cleaning
    if name:
        name = ' '.join(name.split()[:3])  # Limit to 3 words maximum
    if father_name:
        father_name = ' '.join(father_name.split()[:3])  # Limit to 3 words maximum
    
    return name, father_name

def ExtractDetails(image_path):
    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise Exception("Could not read image file")

        # Get preprocessed versions
        image_versions = preprocess_image(image)
        
        # Extract text from all versions
        text = get_best_text(image_versions)
        
        # Convert to uppercase for consistency
        text = text.upper()
        
        # Extract PAN number
        pan_pattern = r'[A-Z]{5}[0-9]{4}[A-Z]'
        pan_matches = re.findall(pan_pattern, text)
        pan_number = pan_matches[0] if pan_matches else ''
        
        # Extract name and father's name
        name, father_name = extract_name_and_father_name(text)
        
        # Extract DOB
        dob_pattern = r'\d{2}[/-]\d{2}[/-]\d{4}'
        dob_matches = re.findall(dob_pattern, text)
        dob = ''
        if dob_matches:
            for date in dob_matches:
                day, month, year = re.split(r'[/-]', date)
                try:
                    if 1 <= int(day) <= 31 and 1 <= int(month) <= 12 and 1900 <= int(year) <= 2100:
                        dob = date
                        break
                except ValueError:
                    continue
        
        # Create response dictionary
        extracted_data = {
            'pan_number': pan_number,
            'name': name,
            'father_name': father_name,
            'dob': dob
        }
        
        return extracted_data
        
    except Exception as e:
        print(f"Error extracting PAN details: {str(e)}")
        return None

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = 'sample_pan.jpg'
    
    result = ExtractDetails(image_path)
    print(result)