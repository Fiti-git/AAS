from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path, include
from main import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.decorators import permission_classes
from users.views import CustomTokenObtainpairView


urlpatterns = [
    path('', views.home, name='home'),  # This line adds the route for the root UR
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # Root URL to home page
    path('employee_form/', views.employee_form, name='employee_form'),  # Link to the employee form
    path('api/getagencies/', views.get_agencies, name='get_agencies'),
    path('api/getemployees/', views.get_all_employees, name='get_employees'),
    path('api/getoutletemployees/', views.get_outlet_employees, name='get_outletemployees'),
    path('api/employees/create', views.create_employee, name='create_employee'),
    path('api/editemployees/<int:employee_id>/', views.edit_employee, name='edit_delete_employee'),
    path('api/groups/', views.get_groups, name='get_groups'),
    path('api/holidays/', views.HolidayListCreateAPIView.as_view(), name='holiday-list-create'),
    path('api/holidays/<int:pk>/', views.HolidayDetailUpdateAPIView.as_view(), name='holiday-detail-update'),
    path('api/leavetypes/', views.LeaveTypeListCreateAPIView.as_view(), name='leave-type-list-create'),
    path('api/leavetypes/<int:pk>/', views.LeaveTypeDetailUpdateAPIView.as_view(), name='leave-type-detail-update'),
    path('login/', views.loginform_form, name='login'),
    path('api/changepassword/<int:employee_id>/', views.ChangepswrdView.as_view(), name='edit-password'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/user/', views.current_user, name='current-user'),
    path('api/agencies/', views.create_agency, name='create-agency'),
    path('api/agencies/<int:id>/', views.update_agency, name='update-agency'),
    path('api/outlets/create', views.create_outlet, name='outlet-create'),
    path('api/outlets/', views.get_outlets, name='outlet-detail'),
    path('api/outlets/<int:id>/', views.get_outlets, name='outlet-detail'),
    path('api/outlets/manage/<int:id>/',  views.update_or_delete_outlet, name='outlet-manage'),
    path('api/group/', views.list_groups, name='list_groups'),  # GET all groups
    path('api/group/', views.create_group, name='create_group'),  # POST to create new group
    path('api/group/<int:id>/', views.group_detail, name='group_detail'),  # GET group details
    path('api/group/<int:id>/update/', views.update_group, name='update_group'),  # PUT to update group
    path('api/group/<int:id>/deactivate/', views.deactivate_group, name='deactivate_group'),  # Deactivate group
    path('api/create-role/', views.create_role, name='create-role'),
    # path('api/token/', permission_classes([])(TokenObtainPairView.as_view()), name='token_obtain_pair'),
    path('api/token/', CustomTokenObtainpairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # refresh
    path('api/devices/', views.get_all_devices, name='get_all_devices'),          # GET all devices
    path('api/devices/delete/', views.delete_device, name='delete_device'),       # DELETE a device
    path('api/attendance/all/', views.AllAttendanceRecordsView.as_view(), name='all_attendance_records'),  # GET attendance records
    path('api/attendance/', include('attendance.apiurls')),
    path('attendance/', include('attendance.urls')),
    path('api/users/', include('users.apiurls')),
    path('admintool/', include('face_recognition.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)