from django.shortcuts import render
from django.conf import settings
import os
import uuid

# Dummy face verification function
def verify_employee(img_path, embeddings=None, labels=None, threshold=0.9):
    # Always return a dummy success
    return None, "Face verification skipped (dummy function)"

# Dummy selfie verification
def verify_selfie(photo_file, employee):
    # Save uploaded file temporarily (optional, can remove if not needed)
    os.makedirs('temp_upload', exist_ok=True)
    temp_filename = f"{uuid.uuid4()}.jpg"
    temp_path = os.path.join('temp_upload', temp_filename)

    try:
        with open(temp_path, 'wb+') as f:
            for chunk in photo_file.chunks():
                f.write(chunk)
        return {"success": True, "message": "Face verification skipped (dummy)"}
    except Exception as e:
        return {"success": False, "message": f"Error processing image: {str(e)}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# Dummy update embeddings page
def update_embeddings(request):
    context = {}
    if request.method == 'POST':
        context['message'] = "Embeddings update skipped (dummy)"
    return render(request, 'update_embeddings.html', context)
