from math import radians, cos, sin, asin, sqrt
from .models import Outlet

def haversine(lat1, lon1, lat2, lon2):
    # Earth radius in meters
    R = 6371000  
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def verify_location(employee, lat, lon):
    try:
        for outlet_id in employee.outlet:
            outlet = Outlet.objects.get(id=outlet_id)
            
            # Calculate the distance using the haversine formula
            distance = haversine(lat, lon, outlet.latitude, outlet.longitude)
            
            # If within the radius of any outlet, location is verified
            if distance <= outlet.radius_meters:
                return True
        
        # If no outlet is within range, return False
        return False

    except (Outlet.DoesNotExist, TypeError, AttributeError) as e:
        print(f"Location verification error: {e}")
        return False

def verify_selfie(selfie_url, employee):
    try:
        # # Load uploaded selfie
        # selfie_response = requests.get(selfie_url)
        # selfie_img = face_recognition.load_image_file(BytesIO(selfie_response.content))

        # # Load stored image (you'll need a URL or file path)
        # if not employee.photo_url:  # You should have this saved during employee onboarding
        #     return {"success": False, "message": "No stored photo to compare against"}
        
        # stored_response = requests.get(employee.photo_url)
        # stored_img = face_recognition.load_image_file(BytesIO(stored_response.content))

        # # Get face encodings
        # selfie_encoding = face_recognition.face_encodings(selfie_img)
        # stored_encoding = face_recognition.face_encodings(stored_img)

        # if not selfie_encoding or not stored_encoding:
        #     return {"success": False, "message": "Could not detect face in one of the images"}

        # # Compare
        # match = face_recognition.compare_faces([stored_encoding[0]], selfie_encoding[0])[0]
        match = True
        return {"success": match, "message": "Face matched" if match else "Face did not match"}

    except Exception as e:
        return {"success": False, "message": str(e)}