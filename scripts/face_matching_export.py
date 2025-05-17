import cv2
from deepface import DeepFace
import numpy as np
import os

def initialize_model():
    try:
        # Force model initialization with a dummy image
        dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
        dummy_path = "dummy.jpg"
        cv2.imwrite(dummy_path, dummy_img)
        _ = DeepFace.represent(img_path=dummy_path, model_name="VGG-Face", enforce_detection=False)
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
    except Exception as e:
        print(f"Model initialization error: {str(e)}")
        raise

def extract_and_store_embedding(reference_image_path):
    try:
        initialize_model()
        embedding = DeepFace.represent(img_path=reference_image_path, model_name="VGG-Face")
        np.save("stored_embedding.npy", embedding)
        return True
    except Exception as e:
        print(f"Error extracting embedding: {str(e)}")
        return False

def compare_faces(reference_image_path, live_image_path):
    try:
        initialize_model()
        result = DeepFace.verify(
            img1_path=reference_image_path,
            img2_path=live_image_path,
            model_name="VGG-Face",
            distance_metric="cosine"
        )
        return result['verified']
    except Exception as e:
        print(f"Error comparing faces: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        extracted_face_path = "scripts/extracted_face_image/extracted_face.jpg"
        live_image_path = "scripts/comparison_image/comparison_Img.JPG"
        if extract_and_store_embedding(extracted_face_path):
            result = compare_faces(extracted_face_path, live_image_path)
            print("Faces match!" if result else "Faces do not match!")
    except Exception as e:
        print(f"Error in main: {str(e)}")