import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import Sequential
import os
import uuid
import psutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent  # recognizer folder path

MODEL_PATH = BASE_DIR / 'best_finetuned_model.h5'
EMBEDDINGS_PATH = BASE_DIR / 'saved_embeddings.npy'
LABELS_PATH = BASE_DIR / 'labels.npy'
IMAGE_PATHS_PATH = BASE_DIR / 'image_paths.npy'

model = tf.keras.models.load_model(str(MODEL_PATH))
embedding_model = Sequential([model.layers[0], model.layers[1]])
saved_embeddings = np.load(str(EMBEDDINGS_PATH))
labels = np.load(str(LABELS_PATH), allow_pickle=True)
image_paths = np.load(str(IMAGE_PATHS_PATH), allow_pickle=True)

def cosine_similarity(emb1, emb2):
    dot = np.dot(emb1, emb2)
    norm1 = np.linalg.norm(emb1)
    norm2 = np.linalg.norm(emb2)
    return dot / (norm1 * norm2)

def recognize_face(new_emb, saved_embs, labels, threshold=0.8):
    similarities = [cosine_similarity(new_emb, emb) for emb in saved_embs]
    best_idx = np.argmax(similarities)
    best_sim = similarities[best_idx]
    if best_sim > threshold:
        return labels[best_idx], best_sim, best_idx
    else:
        return "Unknown", best_sim, None

def verify_selfie(photo_file, employee):
    os.makedirs('temp_upload', exist_ok=True)
    temp_filename = f"{uuid.uuid4()}.jpg"
    temp_path = os.path.join('temp_upload', temp_filename)

    with open(temp_path, 'wb+') as f:
        for chunk in photo_file.chunks():
            f.write(chunk)

    try:
        img = load_img(temp_path, target_size=(224, 224))
        img_array = img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        input_embedding = embedding_model.predict(img_array)[0]
        label, similarity, match_idx = recognize_face(input_embedding, saved_embeddings, labels)

        if str(label).lower() == str(employee.employee_id).lower() or str(label).lower() == employee.fullname.lower():
            return {"success": True, "message": f"Matched with {label} (score: {similarity:.2f})"}
        else:
            return {"success": False, "message": f"Face mismatch (recognized as: {label}, score: {similarity:.2f})"}
    except Exception as e:
        return {"success": False, "message": f"Error processing image: {str(e)}"}
    finally:
        os.remove(temp_path)