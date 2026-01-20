import os
import shutil
from deepface import DeepFace
import cv2
import numpy as np

# Directory to store user reference images
FACES_DIR = "backend/faces"
if not os.path.exists(FACES_DIR):
    os.makedirs(FACES_DIR)

def save_face_image(user_id: int, image_file_path: str):
    """
    Moves/Saves the uploaded registration image to the faces directory.
    Renames it to user_{id}.jpg
    """
    target_path = os.path.join(FACES_DIR, f"user_{user_id}.jpg")
    shutil.copy(image_file_path, target_path)
    return target_path

def verify_face(temp_image_path: str, user_id: int):
    """
    Verifies the face in temp_image_path against the stored face for user_id.
    Uses FaceNet model.
    """
    reference_image_path = os.path.join(FACES_DIR, f"user_{user_id}.jpg")
    
    if not os.path.exists(reference_image_path):
        return {"verified": False, "message": "Reference image not found for user."}

    try:
        # DeepFace.verify returns a dictionary
        # model_name='Facenet' checks specifically using Google's FaceNet
        result = DeepFace.verify(
            img1_path=temp_image_path,
            img2_path=reference_image_path,
            model_name="Facenet",
            detector_backend="opencv", # opencv is faster, mtcnn/retinaface is more accurate but slower
            distance_metric="cosine"
        )
        
        return {
            "verified": result["verified"],
            "distance": result["distance"],
            "threshold": result["threshold"],
            "message": "Verification successful" if result["verified"] else "Face mismatch"
        }
    except Exception as e:
        print(f"Error in face verification: {e}")
        return {"verified": False, "message": str(e)}
