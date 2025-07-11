from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework import status
from main.models import Devices, Employee, Outlet
from main.serializers import OutletSerializer

class ValidateDeviceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        device_id = request.data.get("device_id")

        if not device_id:
            return Response({
                "detail": "Missing device_id.",
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            registered_device = Devices.objects.get(device_id=device_id)
        except Devices.DoesNotExist:
            return Response({
                "detail": "No personal device registered.",
                "devicenotregistered": True
            }, status=status.HTTP_200_OK)

        # Device exists — now check if it belongs to another user
        if registered_device.user != user:
            return Response({
                "detail": "This is not your registered device.",
                "alternate": True
            }, status=status.HTTP_200_OK)

        # Check if user has a registered device
        try:
            user_device = Devices.objects.get(user=user)
        except Devices.DoesNotExist:
            return Response({
                "detail": "No personal device registered.",
                "devicenotregistered": True
            }, status=status.HTTP_200_OK)

        # Final verification
        if user_device.device_id == device_id:
            return Response({
                "detail": "Device verified as user device.",
                "authorized": True
            }, status=status.HTTP_200_OK)

        # Shouldn't reach here, but fallback:
        return Response({
            "detail": "This is not your authorized device.",
            "unauthorized": True
        }, status=status.HTTP_200_OK)

class RegisterDeviceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        device_id = request.data.get("device_id")
        device_type = request.data.get("device_type")

        if Devices.objects.filter(user=user).exists():
            return Response({
                "detail": "User already has a registered device.",
                "device_registered": False
            }, status=status.HTTP_400_BAD_REQUEST)

        Devices.objects.create(
            user=user,
            device_id=device_id,
            device_type=device_type
        )

        return Response({
            "detail": "Device registered successfully.",
            "device_registered": True
        }, status=status.HTTP_200_OK)


class GetDeviceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            device = Devices.objects.get(user=user)
            return Response({
                "device_id": device.device_id,
                "device_type": device.device_type,
                "outlet_id": device.outlet_id
            }, status=status.HTTP_200_OK)
        except Devices.DoesNotExist:
            return Response({"detail": "No device found."}, status=status.HTTP_404_NOT_FOUND)


class UpdateDeviceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        device_id = request.data.get("device_id")
        device_type = request.data.get("device_type")

        try:
            device = Devices.objects.get(user=user)
            device.device_id = device_id
            device.device_type = device_type
            device.save()
            return Response({"detail": "Device updated successfully."}, status=status.HTTP_200_OK)
        except Devices.DoesNotExist:
            return Response({"detail": "No device found to update."}, status=status.HTTP_404_NOT_FOUND)


class DeleteDeviceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        try:
            device = Devices.objects.get(user=user)
            device.delete()
            return Response({"detail": "Device deleted successfully."}, status=status.HTTP_200_OK)
        except Devices.DoesNotExist:
            return Response({"detail": "No device found to delete."}, status=status.HTTP_404_NOT_FOUND)
              
class RegisterCompanyDeviceAPIView(APIView):
    authentication_classes = []  # No auth required
    permission_classes = []      # Public access

    def post(self, request):
        device_id = request.data.get("device_id")
        outlet_id = request.data.get("outlet_id")
        device_type = request.data.get("device_type", "company")

        if not device_id or not outlet_id:
            return Response({
                "detail": "Device ID and outlet ID are required."
            }, status=status.HTTP_400_BAD_REQUEST)

        if device_type != "company":
            return Response({
                "detail": "Only 'company' devices can be registered with this endpoint."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            outlet = Outlet.objects.get(id=outlet_id)
        except Outlet.DoesNotExist:
            return Response({"detail": "Invalid outlet ID."}, status=status.HTTP_404_NOT_FOUND)

        if Devices.objects.filter(device_id=device_id, outlet=outlet).exists():
            return Response({
                "detail": "This company device is already registered for this outlet."
            }, status=status.HTTP_400_BAD_REQUEST)

        Devices.objects.create(
            device_id=device_id,
            device_type="company",
            outlet=outlet,
            user=None  # company device; no user
        )

        return Response({
            "detail": "Company device registered successfully.",
            "device_registered": True
        }, status=status.HTTP_201_CREATED)
    
@api_view(['GET'])
@authentication_classes([])  # No authentication
@permission_classes([AllowAny])  # Public access
def public_get_outlets(request, id=None):
    if id:
        try:
            outlet = Outlet.objects.get(pk=id)
            serializer = OutletSerializer(outlet)
            return Response(serializer.data)
        except Outlet.DoesNotExist:
            return Response({'error': 'Outlet not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        outlets = Outlet.objects.all()
        serializer = OutletSerializer(outlets, many=True)
        return Response(serializer.data)