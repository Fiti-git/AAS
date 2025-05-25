import os
import uuid
import numpy as np
from numpy.linalg import norm
from deepface import DeepFace
import cv2
from pathlib import Path
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Base directory for model/data files
BASE_DIR = Path(__file__).resolve().parent

# Load DeepFace-based embeddings once
EMBEDDINGS_PATH = BASE_DIR / 'employee_embeddings_deepface.npz'
data = np.load(EMBEDDINGS_PATH)
saved_embeddings = data['embeddings']
labels = data['labels']

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

def load_and_detect_face(img_path):
    # Read image using OpenCV
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError("Image not found or unreadable")

    # Detect, align, and crop face using DeepFace's detectFace (uses mtcnn)
    detected_face = DeepFace.detectFace(img_path, detector_backend='mtcnn', enforce_detection=True)
    # detected_face is a numpy array (160x160 RGB)
    return detected_face

def verify_employee(img_path, embeddings, labels, threshold=0.7):
    try:
        # detect and crop face first
        img = load_and_detect_face(img_path)
        if img is None or img.size == 0:
            return None, "No face detected or unable to preprocess image"

        # get embedding from cropped face numpy array
        embedding = DeepFace.represent(img_path=img, model_name='Facenet', enforce_detection=False)[0].get('embedding')
        if embedding is None or len(embedding) == 0:
            return None, "No embedding found for the detected face"
    except Exception as e:
        return None, f"Face detection or embedding error: {e}"

    sims = [cosine_similarity(embedding, emb) for emb in embeddings]
    if not sims:
        return None, "No embeddings found in database to compare"

    best_idx = np.argmax(sims)
    best_sim = sims[best_idx]
    best_label = labels[best_idx]

    if best_sim >= threshold:
        return best_label, f"Matched with {best_label} (similarity: {best_sim:.2f})"
    else:
        return None, f"No match found (max similarity: {best_sim:.2f})"

def verify_selfie(request, employee):
    if request.method != 'POST':
        return render(request, 'verify_selfie.html', {'error': 'POST method required.'})

    photo_file = request.FILES.get('photo')
    if not photo_file:
        return render(request, 'verify_selfie.html', {'error': 'No photo uploaded.'})

    os.makedirs('temp_upload', exist_ok=True)
    temp_filename = f"{uuid.uuid4()}.jpg"
    temp_path = os.path.join('temp_upload', temp_filename)

    with open(temp_path, 'wb+') as f:
        for chunk in photo_file.chunks():
            f.write(chunk)

    try:
        label, message = verify_employee(temp_path, saved_embeddings, labels)
        if label and (
            str(label).lower() == str(employee.employee_id).lower() 
            or str(label).lower() == employee.fullname.lower()
        ):
            context = {"success": True, "message": message}
        else:
            context = {"success": False, "message": f"Face mismatch: {message}"}
    except Exception as e:
        context = {"success": False, "message": f"Error processing image: {str(e)}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return render(request, 'verify_selfie_result.html', context)

@csrf_exempt
def update_embeddings(request):
    context = {}
    embeddings_dir = os.path.join(settings.BASE_DIR, 'face_recognition')
    embeddings_file_path = os.path.join(embeddings_dir, 'employee_embeddings_deepface.npz')

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
