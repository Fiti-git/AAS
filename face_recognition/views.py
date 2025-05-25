import os
import uuid
import numpy as np
from numpy.linalg import norm
from deepface import DeepFace
from pathlib import Path
from django.conf import settings
from django.shortcuts import render
from mtcnn import MTCNN
from PIL import Image

# Base directory for model/data files
BASE_DIR = Path(__file__).resolve().parent

# Load DeepFace-based embeddings once
EMBEDDINGS_PATH = BASE_DIR / 'employee_embeddings_deepface.npz'
data = np.load(EMBEDDINGS_PATH)
saved_embeddings = data['embeddings']
labels = data['labels']

# Cosine similarity function
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

# Face verification using DeepFace
def verify_employee(img_path, embeddings, labels, threshold=0.7):
    try:
        embedding = DeepFace.represent(img_path=img_path, model_name='Facenet', enforce_detection=True)[0]['embedding']
    except Exception as e:
        return None, f"Face detection error: {e}"

    sims = [cosine_similarity(embedding, emb) for emb in embeddings]
    best_idx = np.argmax(sims)
    best_sim = sims[best_idx]
    best_label = labels[best_idx]

    if best_sim >= threshold:
        return best_label, f"Matched with {best_label} (similarity: {best_sim:.2f})"
    else:
        return None, f"No match found (max similarity: {best_sim:.2f})"

# --- New function: preprocess selfie image using MTCNN ---
def preprocess_selfie(image_path):
    # Load image with PIL
    img = Image.open(image_path).convert('RGB')
    img_np = np.array(img)

    detector = MTCNN()
    faces = detector.detect_faces(img_np)

    if len(faces) == 0:
        raise ValueError("No face detected in the image")

    # take first detected face (can customize if multiple faces)
    face = faces[0]
    x, y, width, height = face['box']

    # fix negative coordinates if any
    x, y = max(0, x), max(0, y)

    # Crop the face region from image
    face_img = img.crop((x, y, x + width, y + height))

    # Resize face image to 224x224 (Facenet usually expects 160x160 or 224x224, confirm for your model)
    face_img = face_img.resize((224, 224))

    # Save cropped face to a temp path (can overwrite or use uuid)
    temp_face_path = f"temp_upload/cropped_{uuid.uuid4()}.jpg"
    os.makedirs('temp_upload', exist_ok=True)
    face_img.save(temp_face_path)

    return temp_face_path

# New selfie verification using DeepFace with cropping step
def verify_selfie(photo_file, employee):
    os.makedirs('temp_upload', exist_ok=True)
    temp_filename = f"{uuid.uuid4()}.jpg"
    temp_path = os.path.join('temp_upload', temp_filename)

    with open(temp_path, 'wb+') as f:
        for chunk in photo_file.chunks():
            f.write(chunk)

    cropped_face_path = None
    try:
        # Preprocess selfie: detect & crop face with MTCNN
        cropped_face_path = preprocess_selfie(temp_path)

        # Verify using cropped face image
        label, message = verify_employee(cropped_face_path, saved_embeddings, labels)

        if label and (
            str(label).lower() == str(employee.employee_id).lower()
            or str(label).lower() == employee.fullname.lower()
        ):
            return {"success": True, "message": message}
        else:
            return {"success": False, "message": f"Face mismatch: {message}"}

    except Exception as e:
        return {"success": False, "message": f"Error processing image: {str(e)}"}

    finally:
        # Clean up temp files
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if cropped_face_path and os.path.exists(cropped_face_path):
            os.remove(cropped_face_path)

# View to upload & update embeddings npz file
def update_embeddings(request):
    context = {}
    embeddings_dir = os.path.join(settings.BASE_DIR, 'face_recognition')
    embeddings_file_path = os.path.join(embeddings_dir, 'employee_embeddings_deepface.npz')  # file location

    if request.method == 'POST':
        uploaded_file = request.FILES.get('npz_file')
        if not uploaded_file:
            context['error'] = 'No file uploaded.'
            return render(request, 'update_embeddings.html', context)

        if not uploaded_file.name.endswith('.npz'):
            context['error'] = 'Invalid file format. Only .npz files are allowed.'
            return render(request, 'update_embeddings.html', context)

        try:
            with open(embeddings_file_path, 'wb+') as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)
            context['message'] = 'Embeddings file updated successfully.'
        except Exception as e:
            context['error'] = f'Failed to update file: {str(e)}'

    return render(request, 'update_embeddings.html', context)
