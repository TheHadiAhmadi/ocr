import cv2
import numpy as np

# Load the image
image_path = "./image.png"  # Path to your input image
image = cv2.imread(image_path)

# Resize image for faster processing (optional)
orig = image.copy()
(H, W) = image.shape[:2]
newW, newH = (320, 320)  # Size expected by the EAST model
rW = W / float(newW)
rH = H / float(newH)
image = cv2.resize(image, (newW, newH))

# Load pre-trained EAST text detector
east_model = "../frozen_east_text_detection.pb"  # Path to pre-trained EAST model
net = cv2.dnn.readNet(east_model)

# Define layer names for EAST output
layer_names = [
    "feature_fusion/Conv_7/Sigmoid",  # Probability map
    "feature_fusion/concat_3"        # Geometry map
]

# Prepare the image for the model
blob = cv2.dnn.blobFromImage(image, 1.0, (newW, newH), (123.68, 116.78, 103.94), swapRB=True, crop=False)
net.setInput(blob)
(scores, geometry) = net.forward(layer_names)

# Decode the predictions
def decode_predictions(scores, geometry, min_confidence=0.5):
    (num_rows, num_cols) = scores.shape[2:4]
    boxes = []
    confidences = []

    for y in range(num_rows):
        scores_data = scores[0, 0, y]
        x_data0 = geometry[0, 0, y]
        x_data1 = geometry[0, 1, y]
        x_data2 = geometry[0, 2, y]
        x_data3 = geometry[0, 3, y]
        angles_data = geometry[0, 4, y]

        for x in range(num_cols):
            if scores_data[x] < min_confidence:
                continue

            # Calculate the offset
            offset_x = x * 4.0
            offset_y = y * 4.0

            # Extract the rotation angle
            angle = angles_data[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            # Compute bounding box dimensions
            h = x_data0[x] + x_data2[x]
            w = x_data1[x] + x_data3[x]

            # Compute the starting coordinates
            end_x = int(offset_x + (cos * x_data1[x]) + (sin * x_data2[x]))
            end_y = int(offset_y - (sin * x_data1[x]) + (cos * x_data2[x]))
            start_x = int(end_x - w)
            start_y = int(end_y - h)

            boxes.append((start_x, start_y, end_x, end_y))
            confidences.append(scores_data[x])

    return (boxes, confidences)

(min_confidence, nms_threshold) = (0.5, 0.4)
(boxes, confidences) = decode_predictions(scores, geometry, min_confidence)


# Apply non-maxima suppression
indices = cv2.dnn.NMSBoxes(
    [cv2.boundingRect(np.array([[box[0], box[1]]])) for box in boxes],
    confidences,
)

# Draw the bounding boxes on the original image
for i in indices.flatten():
    (start_x, start_y, end_x, end_y) = boxes[i]
    start_x = int(start_x * rW)
    start_y = int(start_y * rH)
    end_x = int(end_x * rW)
    end_y = int(end_y * rH)
    cv2.rectangle(orig, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)

# Show the output image
cv2.imshow("Text Detection", orig)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Save the output
output_path = "/mnt/data/detected_text.png"
cv2.imwrite(output_path, orig)
print(f"Processed image saved to: {output_path}")
