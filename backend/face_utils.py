import os
import shutil
from deepface import DeepFace
import cv2
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = "faces"

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Local temp directory for serverless environments
TEMP_DIR = "/tmp" if os.name != 'nt' else "backend/temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def save_face_image(user_id: int, image_file_path: str):
    """
    Uploads the registration image to Supabase Storage.
    """
    file_name = f"user_{user_id}.jpg"
    
    if supabase:
        with open(image_file_path, "rb") as f:
            # Upload with upsert=True to overwrite existing
            supabase.storage.from_(SUPABASE_BUCKET).upload(
                path=file_name,
                file=f,
                file_options={"x-upsert": "true"}
            )
        return file_name # Return the storage path/name
    else:
        # Fallback to local for dev
        FACES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faces")
        if not os.path.exists(FACES_DIR):
            os.makedirs(FACES_DIR)
        target_path = os.path.join(FACES_DIR, file_name)
        shutil.copy(image_file_path, target_path)
        return target_path

def verify_face(temp_image_path: str, user_id: int):
    """
    Verifies the face against stored image in Supabase or local storage.
    """
    file_name = f"user_{user_id}.jpg"
    reference_image_path = ""

    if supabase:
        # Download from Supabase to /tmp
        reference_image_path = os.path.join(TEMP_DIR, file_name)
        try:
            with open(reference_image_path, "wb+") as f:
                res = supabase.storage.from_(SUPABASE_BUCKET).download(file_name)
                f.write(res)
        except Exception as e:
            return {"verified": False, "message": f"Could not retrieve reference image: {str(e)}"}
    else:
        # Local fallback
        FACES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faces")
        reference_image_path = os.path.join(FACES_DIR, file_name)

    if not os.path.exists(reference_image_path):
        return {"verified": False, "message": "Reference image not found."}

    try:
        result = DeepFace.verify(
            img1_path=temp_image_path,
            img2_path=reference_image_path,
            model_name="Facenet",
            detector_backend="opencv",
            distance_metric="cosine"
        )
        
        # Cleanup temp reference image if we downloaded it
        if supabase and os.path.exists(reference_image_path):
            os.remove(reference_image_path)

        return {
            "verified": result["verified"],
            "distance": result["distance"],
            "threshold": result["threshold"],
            "message": "Verification successful" if result["verified"] else "Face mismatch"
        }
    except Exception as e:
        print(f"Error in face verification: {e}")
        return {"verified": False, "message": str(e)}
