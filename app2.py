
from PIL import Image, ImageEnhance
import pytesseract
from paddleocr import PaddleOCR
import easyocr
import numpy as np


# Path to the tesseract executable
# Update this path according to your installation
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract-ocr'

def tesseractocr(image_path):
    print('run tesseractocr')
    try:
        # Open the image file
        img = Image.open(image_path)
        img = img.convert("L")
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = np.array(img)
        # Use Tesseract to extract text
        text = pytesseract.image_to_string(img, "fas")
        return text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def paddleocr(image_path):
    print('run paddleocr')
    """
    Extract text from an image using PaddleOCR.

    :param image_path: Path to the image file
    :return: List of detected text and bounding box information
    """
    try:
        # Initialize the PaddleOCR model
        ocr = PaddleOCR(use_angle_cls=True, lang="fa")

        img = Image.open(image_path)
        img = img.convert("L") 
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = np.array(img)
        # Perform OCR on the image
        results = ocr.ocr(img, cls=True)
        # Parse and return text results
        extracted_text = []
        for line in results[0]:
            # Each line contains [bounding_box, (text, confidence)]
            _, (text, confidence) = line
            extracted_text.append((text[::-1], confidence))

        return extracted_text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def easyocr1(image_path):
    print('run easyocr1')
    # Initialize EasyOCR Reader
    reader = easyocr.Reader(['en', 'fa'], gpu=True)  # Add languages as needed, e.g., 'ar' for Arabic

    img = Image.open(image_path)
    
    img = img.convert("L") 
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    img = np.array(img)

    # Perform OCR
    ocr_results = reader.readtext(img, detail=0, batch_size=16)
    
    # Extract and reverse texts
    reversed_texts = [result for result in ocr_results]  # Reverse the extracted texts
    return " ".join(reversed_texts)

# Joined
import json
import os

print('here')
def process_folder(folder_path):
    ocr_results = {}
    
    # Loop through all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # Check if the file is an image
        if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            try:
                paddle = paddleocr(file_path)
                tesseract = tesseractocr(file_path)
                easy = easyocr1(file_path)
                print(filename)

                ocr_results[filename] = { 
                   "paddle": " ".join([item[0] for item in paddle]), 
                   "tesseract": tesseract, 
                    "easy": easy 
                }
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    with open("./output.json", 'w', encoding='utf-8') as json_file:
        print('saving')
        json.dump(ocr_results, json_file, ensure_ascii=False, indent=4)

    return ocr_results

process_folder('./samples')
