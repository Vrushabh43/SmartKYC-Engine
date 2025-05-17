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

def ExtractDetails(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path), lang = 'eng')
        text = text.replace("\n", " ")
        text = text.replace("  ", " ")
        regex_DOB = re.compile('\d{2}[-/]\d{2}[-/]\d{4}')
        regex_num = re.compile('[A-Z]{5}[0-9]{4}[A-Z]{1}')
        
        image = cv2.imread(os.path.join(image_path))
        if image is None:
            raise Exception("Could not read image file")
            
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        plt.imshow(image)
        plt.axis("off")  
        
        pan_numbers = regex_num.findall(text)
        dob_matches = regex_DOB.findall(text)
        
        if len(pan_numbers) == 0 or len(dob_matches) == 0:
            return None, None
            
        return pan_numbers[0], dob_matches[0]
    except Exception as e:
        print(f"Error processing PAN card: {str(e)}")
        return None, None

if __name__ == '__main__':
    ExtractDetails('ocr_scripts/pancard_try.jpeg')