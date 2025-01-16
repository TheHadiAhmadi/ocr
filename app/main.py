import re
from typing import Union
from fastapi import FastAPI,File, UploadFile, HTTPException
import shutil
from pathlib import Path
from starlette.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image, ImageEnhance
from io import BytesIO
import numpy as np
import os
import cv2
from paddleocr import PaddleOCR

from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (you can specify domains like ["http://example.com"])
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

TEMP_IMAGE_PATH = "./front/image.jpeg"
# Path where uploaded files will be stored
UPLOAD_DIR = Path("./front/static")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract-ocr'

saved_settings = {
    "grayscale": False,
    "resize_factor": 1,
    "denoise": False,
    "brightness": 100,
    "contrast": 100
}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Save the uploaded file
        file_path = UPLOAD_DIR / "image.jpeg"

        # Open the file in write-binary mode and write the content
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        converted_image_path = UPLOAD_DIR / "converted.jpeg"
        shutil.copy(file_path, converted_image_path)


        saved_settings["grayscale"] =  False
        saved_settings["contrast"] =  1
        saved_settings["brightness"] =  False
        saved_settings["resize_factor"] =  100
        saved_settings["denoise"] =  100

        return {"message": f"File '{"image.jpeg"}' uploaded successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/")
def read_root():
    return {"Hello": "World!"}

class ImageSettings(BaseModel):
    grayscale: bool
    resize_factor: float
    denoise: bool
    brightness: int
    contrast: int  # 0-200

image_path = "./front/static/image.jpeg"
converted_path = "./front/static/converted.jpeg"


@app.post("/convert")
async def convert_image(settings: ImageSettings):
    try:
        img = Image.open(image_path)

        if (settings.grayscale):
            # Apply grayscale conversion
            img = img.convert("L")  # Convert to grayscale (L mode)
                # Convert image to grayscale before applying threshold
            image_cv = np.array(img)

            _, image_cv = cv2.threshold(image_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            img = Image.fromarray(image_cv)


        # Resize the img if resize factor is provided
        if settings.resize_factor != 1.0:
            width, height = img.size
            new_width = int(width * settings.resize_factor)
            new_height = int(height * settings.resize_factor)
            img = img.resize((new_width, new_height))
        
        if (settings.contrast):
            # Apply contrast enhancement
            enhancer = ImageEnhance.Contrast(img)
            contrast_factor = settings.contrast / 100  # Convert contrast value to a factor
            img = enhancer.enhance(contrast_factor)


        # Adjust brightness
        if settings.brightness != 0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(settings.brightness / 100)
        
        # Apply denoising using OpenCV (Gaussian Blur or Median Filter)
        if settings.denoise:
            # Convert to NumPy array for OpenCV processing
            image_cv = np.array(img)
            image_cv = cv2.GaussianBlur(image_cv, (5, 5), 0)
            # Convert back to PIL
            img = Image.fromarray(image_cv)
        
        if (settings.grayscale):
            image_cv = np.array(img)
            
            _, image_cv = cv2.threshold(image_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            img = Image.fromarray(image_cv)

                
        # Save the updated image back to the static folder
        img.save(converted_path)

        saved_settings["grayscale"] = settings.grayscale
        saved_settings["contrast"] = settings.contrast
        saved_settings["brightness"] = settings.brightness
        saved_settings["resize_factor"] = settings.resize_factor
        saved_settings["denoise"] = settings.denoise

        return {"message": "Image successfully converted."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the image: {str(e)}")
    
@app.get("/load")
async def load_settings():
    try:
        # Return the settings and image as a response
        return {
            "settings": saved_settings,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading processed image: {str(e)}")

@app.post("/rotate-clock")
async def rotate_clock():
    try:
        # Open the image files
        img = Image.open(image_path)
        converted = Image.open(converted_path)

        # Rotate both images 90 degrees clockwise
        img_rotated = img.rotate(-90, expand=True)  # Rotate clockwise by 90 degrees
        converted_rotated = converted.rotate(-90, expand=True)  # Rotate clockwise by 90 degrees

        # Save the rotated images back to their original locations
        img_rotated.save(image_path)
        converted_rotated.save(converted_path)

        return {"message": "Both images rotated 90 degrees clockwise successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rotating images: {str(e)}")

@app.post("/rotate-anticlock")
async def rotate_anticlock():
    try:
        # Open the image files
        img = Image.open(image_path)
        converted = Image.open(converted_path)

        # Rotate both images 90 degrees counterclockwise
        img_rotated = img.rotate(90, expand=True)  # Rotate counterclockwise by 90 degrees
        converted_rotated = converted.rotate(90, expand=True)  # Rotate counterclockwise by 90 degrees

        # Save the rotated images back to their original locations
        img_rotated.save(image_path)
        converted_rotated.save(converted_path)

        return {"message": "Both images rotated 90 degrees counterclockwise successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rotating images: {str(e)}")



# Function to check if a text is Persian
def is_persian(text):
    # Persian characters range
    persian_regex = re.compile(r'[\u0600-\u06FF]+')
    return bool(persian_regex.search(text))

# Reverse Persian text in the OCR result
def reverse_persian_text(text):
    if text:
        if is_persian(text):  # Check if the text is Persian
            return text[::-1]  # Reverse Persian text
        else:
            return text;
    else:
        return text


@app.post("/ocr")
async def ocr_fn():
    try:

        # Open the image file (make sure it exists in the path)
        image_path = "./front/static/image.jpeg"
        converted_path = "./front/static/converted.jpeg"

        img = Image.open(image_path)
        converted = Image.open(converted_path)

        # Use pytesseract to extract detailed OCR data (text, bounding box, and confidence)
        ocr_data = pytesseract.image_to_data(converted, lang="fas+eng", output_type=pytesseract.Output.DICT)
       
        # Prepare a list of text data with bounding box and confidence
        tesseract_results = []
        paddle_results = []
       
        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) > 0:  # Only include text with a valid confidence level
                tesseract_results.append({
                    "text": ocr_data['text'][i],
                    "confidence": int(ocr_data['conf'][i]),
                    "bounding_box": {
                        "left": ocr_data['left'][i],
                        "top": ocr_data['top'][i],
                        "width": ocr_data['width'][i],
                        "height": ocr_data['height'][i],
                    }
                })

        ocr = PaddleOCR(use_space_char=True, rec_batch_num=10, det_db_thresh=0.3, use_angle_cls=True, lang='fa')  # For Persian (Farsi) text, use 'fa' as language
   
         # Use PaddleOCR to extract text and bounding boxes
        ocr_result_img = ocr.ocr(converted_path, cls=True)

        for line in ocr_result_img:
            for word_info in line:
                text = word_info[1][0]  # Extracted text
                confidence = word_info[1][1]  # Confidence score
                bounding_box = word_info[0]  # Bounding box as [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]

                # Prepare the result with bounding box in terms of left, top, width, and height
                x1, y1 = bounding_box[0]
                x2, y2 = bounding_box[1]
                x3, y3 = bounding_box[2]
                x4, y4 = bounding_box[3]
                
                # Calculate bounding box width and height
                width = int(max(x1, x2, x3, x4) - min(x1, x2, x3, x4))
                height = int(max(y1, y2, y3, y4) - min(y1, y2, y3, y4))

                # Only include text with valid confidence
                if confidence > 0:
                    paddle_results.append({
                        "text": reverse_persian_text(text),
                        "confidence": float(confidence) * 100,
                        "bounding_box": {
                            "left": min(x1, x2, x3, x4),
                            "top": min(y1, y2, y3, y4),
                            "width": width,
                            "height": height
                        }
                    })

        return {"tesseract_results": tesseract_results, "paddle_results": paddle_results}

    except Exception as e:
        print (e)
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")


@app.post("/ocr-tesseract")
async def extract_text():
    try:

        # Open the image file (make sure it exists in the path)
        image_path = "./front/static/image.jpeg"
        converted_path = "./front/static/converted.jpeg"

        img = Image.open(image_path)
        converted = Image.open(converted_path)

        # Use pytesseract to extract detailed OCR data (text, bounding box, and confidence)
        ocr_data = pytesseract.image_to_data(img, lang="fas+eng", output_type=pytesseract.Output.DICT)
        # Use pytesseract to extract detailed OCR data (text, bounding box, and confidence)
        ocr_data_converted = pytesseract.image_to_data(converted, lang="fas+eng", output_type=pytesseract.Output.DICT)


        # Prepare a list of text data with bounding box and confidence
        text_results = []
        converted_results = []
        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) > 0:  # Only include text with a valid confidence level
                text_results.append({
                    "text": ocr_data['text'][i],
                    "confidence": int(ocr_data['conf'][i]),
                    "bounding_box": {
                        "left": ocr_data['left'][i],
                        "top": ocr_data['top'][i],
                        "width": ocr_data['width'][i],
                        "height": ocr_data['height'][i],
                    }
                })

        for i in range(len(ocr_data_converted['text'])):
            if int(ocr_data_converted['conf'][i]) > 0:  # Only include text with a valid confidence level
                converted_results.append({
                    "text": ocr_data_converted['text'][i],
                    "confidence": int(ocr_data_converted['conf'][i]),
                    "bounding_box": {
                        "left": ocr_data_converted['left'][i],
                        "top": ocr_data_converted['top'][i],
                        "width": ocr_data_converted['width'][i],
                        "height": ocr_data_converted['height'][i],
                    }
                })

        return {"original_results": text_results, "converted_results": converted_results}

    except Exception as e:
        print (e)
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

  
@app.post("/ocr-paddle")
async def extract_text_paddle():
    try:
        # Open the image file (make sure it exists in the path)
        image_path = "./front/static/image.jpeg"
        converted_path = "./front/static/converted.jpeg"

        # Initialize PaddleOCR
        ocr = PaddleOCR(use_space_char=True, rec_batch_num=10, det_db_thresh=0.3, use_angle_cls=True, lang='fa')  # For Persian (Farsi) text, use 'fa' as language
   

        # Use PaddleOCR to extract text and bounding boxes
        ocr_result_img = ocr.ocr(image_path, cls=True)
        print('HERE 4')

        ocr_result_converted = ocr.ocr(converted_path, cls=True)
        print('HERE 5')

        print(ocr_result_img)
        # Prepare a list of text data with bounding box and confidence for the original image
        text_results = []
        for line in ocr_result_img:
            for word_info in line:
                text = word_info[1][0]  # Extracted text
                confidence = word_info[1][1]  # Confidence score
                bounding_box = word_info[0]  # Bounding box as [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]

                # Prepare the result with bounding box in terms of left, top, width, and height
                x1, y1 = bounding_box[0]
                x2, y2 = bounding_box[1]
                x3, y3 = bounding_box[2]
                x4, y4 = bounding_box[3]
                
                # Calculate bounding box width and height
                width = int(max(x1, x2, x3, x4) - min(x1, x2, x3, x4))
                height = int(max(y1, y2, y3, y4) - min(y1, y2, y3, y4))

                # Only include text with valid confidence
                if confidence > 0:
                    text_results.append({
                        "text": reverse_persian_text(text),
                        "confidence": float(confidence) * 100,
                        "bounding_box": {
                            "left": min(x1, x2, x3, x4),
                            "top": min(y1, y2, y3, y4),
                            "width": width,
                            "height": height
                        }
                    })

        # Prepare a list of text data with bounding box and confidence for the converted image
        converted_results = []
        for line in ocr_result_converted:
            for word_info in line:
                text = word_info[1][0]  # Extracted text
                confidence = word_info[1][1]  # Confidence score
                bounding_box = word_info[0]  # Bounding box as [(x1, y1), (x2, y2), (x3, y3), (x4, y4)]

                # Prepare the result with bounding box in terms of left, top, width, and height
                x1, y1 = bounding_box[0]
                x2, y2 = bounding_box[1]
                x3, y3 = bounding_box[2]
                x4, y4 = bounding_box[3]

                # Calculate bounding box width and height
                width = int(max(x1, x2, x3, x4) - min(x1, x2, x3, x4))
                height = int(max(y1, y2, y3, y4) - min(y1, y2, y3, y4))

                # Only include text with valid confidence
                if confidence > 0:
                    converted_results.append({
                        "text": reverse_persian_text(text),
                        "confidence": float(confidence) * 100,
                        "bounding_box": {
                            "left": min(x1, x2, x3, x4),
                            "top": min(y1, y2, y3, y4),
                            "width": width,
                            "height": height
                        }
                    })

        # Return both original and converted results
        return {"original_results": text_results, "converted_results": converted_results}

    except Exception as e:
        print("ERROR extracting text: ")
        print(e)
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")