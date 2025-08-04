import cv2
import numpy as np
from django.core.files.base import ContentFile
import os
import logging
from aas import settings # Use Django settings

logger = logging.getLogger(__name__)

# --- Global variable to hold the loaded classifier ---
face_cascade = None

def get_face_cascade():
    """
    Loads the Haar Cascade classifier from disk once and returns the object.
    Subsequent calls will return the already-loaded object.
    """
    global face_cascade
    if face_cascade is None:
        # Use the robust path from settings.py we defined earlier
        cascade_path = str(settings.HAARCASCADE_FILE_PATH) 
        
        if not os.path.exists(cascade_path):
            # This is a critical server configuration error, so it should fail loudly.
            raise FileNotFoundError(f"Haar Cascade file not found at path: {cascade_path}")
        
        logger.info(f"Initializing Haar Cascade from: {cascade_path}")
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
    return face_cascade

def simple_detect_and_crop_face(photo_file):
    """
    Detects a single face, validates its size, crops it,
    and returns it as a Django ContentFile.
    """
    try:
        # --- Use the memoized function to get the classifier ---
        cascade = get_face_cascade()
        
        # ... rest of your function remains the same ...
        # Read the uploaded file into an OpenCV image
        photo_file.seek(0)
        image_array = np.frombuffer(photo_file.read(), np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:
            return None, "Invalid or corrupted image file."

        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = cascade.detectMultiScale(
            gray_image,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40)
        )
        
        if len(faces) == 0:
            return None, "No face detected. Please ensure your face is clear and fills the frame."
        if len(faces) > 1:
            return None, "Multiple faces detected. Only one person should be in the photo."

        # Get coordinates of the single detected face
        (x, y, w, h) = faces[0]

        # * IMPORTANT QUALITY CHECK *
        # If the detected face is too small, it's not reliable for recognition.
        if w < 40 or h < 40:
            return None, f"Face detected is too small ({w}x{h} pixels). Please move closer to the camera."

        # Crop the face from the image
        cropped_face = image[y:y+h, x:x+w]

        # Convert the cropped face back into a file format
        _, buffer = cv2.imencode('.jpg', cropped_face)
        cropped_image_file = ContentFile(buffer.tobytes(), name=f"cropped_{photo_file.name}")

        return cropped_image_file, None

    except Exception as e:
        logger.error(f"Error during simple face cropping: {str(e)}", exc_info=True)
        return None, "An error occurred while processing the image."