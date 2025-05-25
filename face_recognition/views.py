import os
import uuid
import numpy as np
from numpy.linalg import norm
from deepface import DeepFace
from pathlib import Path
from django.conf import settings
from django.shortcuts import render

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
def verify_employee(img_path, embeddings, labels, threshold=0.9):
    try:
        results = DeepFace.represent(img_path=img_path, model_name='Facenet', enforce_detection=True)
        if not results:
            return None, "No faces detected in the image"
        embedding = results[0].get('embedding')
        if embedding is None or len(embedding) == 0:
            return None, "No embedding found for the detected face"
    except Exception as e:
        return None, f"Face detection error: {e}"

    sims = [cosine_similarity(embedding, emb) for emb in embeddings]
    if not sims:  # empty embeddings array check
        return None, "No embeddings found in database to compare"

    best_idx = np.argmax(sims)
    best_sim = sims[best_idx]
    best_label = labels[best_idx]

    if best_sim >= threshold:
        return best_label, f"Matched with {best_label} (similarity: {best_sim:.2f})"
    else:
        return None, f"No match found (max similarity: {best_sim:.2f})"

# New selfie verification using DeepFace
def verify_selfie(photo_file, employee):
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
            return {"success": True, "message": message}
        else:
            return {"success": False, "message": f"Face mismatch: {message}"}
    except Exception as e:
        return {"success": False, "message": f"Error processing image: {str(e)}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

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