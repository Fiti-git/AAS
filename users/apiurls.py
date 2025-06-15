from django.urls import path
from . import api  # Import views from the current app

urlpatterns = [
    path('device/validate/', api.ValidateDeviceAPIView.as_view(), name='validate_device'),
    path('device/register/', api.RegisterDeviceAPIView.as_view(), name='register_device'),
    path('device/', api.GetDeviceAPIView.as_view(), name='get_device'),
    path('device/update/', api.UpdateDeviceAPIView.as_view(), name='update_device'),
    path('device/delete/', api.DeleteDeviceAPIView.as_view(), name='delete_device'),
    path('device/register/company/', api.RegisterCompanyDeviceAPIView.as_view(), name='register_company_device'),
    path('public/outlets/', api.public_get_outlets, name='public_get_outlets')
]