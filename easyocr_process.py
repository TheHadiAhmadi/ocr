from PIL import Image, ImageEnhance
import json
import easyocr
import os

def preprocess_image(image_path):
    try:
        # Open the image
        img = Image.open(image_path)

        # Convert to grayscale
        img = img.convert("L")

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)  # Increase contrast (factor 2.0)

        # Resize by 400%
        width, height = img.size
        img = img.resize((width * 4, height * 4), Image.Resampling.LANCZOS)

        return img
    except Exception as e:
        print(f"Error preprocessing {image_path}: {e}")
        return None

# Initialize EasyOCR Reader
reader = easyocr.Reader(['fa', 'en'], gpu=False)  # Add Persian (fa) and English (en) languages

def easyocr1(image):
    temp_path = "temp_preprocessed_image.png"
    image.save(temp_path)

    # Perform OCR using EasyOCR
    ocr_results = reader.readtext(temp_path, detail=1, paragraph=False)

    # Prepare results list
    easyocr_results = []
    for result in ocr_results:
        bbox, text, confidence = result

        # Prepare bounding box in terms of left, top, width, and height
        x1, y1 = bbox[0]
        x2, y2 = bbox[2]
        width = int(x2 - x1)
        height = int(bbox[2][1] - bbox[0][1])

        easyocr_results.append({
            "text": text,
            "confidence": float(confidence) * 100,
            "bounding_box": {
                "left": int(x1),
                "top": int(y1),
                "width": width,
                "height": height
            }
        })
    return easyocr_results


# Folder containing images
samples_folder = "./samples"
results_file = "./results.json"

# Initialize results dictionary
results = {}

# Process each image in the folder
for file_name in os.listdir(samples_folder):
    if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
        image_path = os.path.join(samples_folder, file_name)
        print(f"Processing {file_name}...")
        
        preprocessed_image = preprocess_image(image_path)
        if preprocessed_image is not None:
            # Perform OCR and save results
            results[file_name] = easyocr1(preprocessed_image)

# Save the results as JSON
with open(results_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print(f"OCR results saved to {results_file}")

