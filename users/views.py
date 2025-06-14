from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserDevice

class CustomTokenObtainpairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        is_mobile = request.data.get('is_mobile', False)  # Check if the request is from mobile
        device_uuid = request.data.get('device_uuid', None)  # Get the UUID if it's provided
        
        # If the request is from mobile, ensure UUID is provided
        if is_mobile and not device_uuid:
            return Response({"detail": "UUID is required for mobile devices."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if it's a mobile request and UUID is provided, validate UUID if necessary
        if is_mobile:
            username = request.data.get('username')
            try:
                user = User.objects.get(username=username)
                user_device = UserDevice.objects.get(user=user, uuid=device_uuid)
                
                # Optionally, check if device type matches the user's assigned device type
                if user_device.device_type != 'personal':
                    return Response({"detail": "You are restricted to logging in from a personal device."}, status=status.HTTP_403_FORBIDDEN)
                
            except UserDevice.DoesNotExist:
                return Response({"detail": "UUID not registered or invalid."}, status=status.HTTP_403_FORBIDDEN)
        
        # Proceed with the default JWT token logic for both mobile and web requests
        return super().post(request, *args, **kwargs)
