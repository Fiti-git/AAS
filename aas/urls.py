from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.http import JsonResponse

from main import views
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import CustomTokenObtainpairView
from main.views import OutletDetailView


# ------------------------------------------------------------------------------
# Health endpoint (fast, no auth, no DB)
# ------------------------------------------------------------------------------
def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # -----------------
    # HOME + HEALTH
    # -----------------
    path('', views.home, name='home'),  # keep single root
    path('health/', health, name='health'),

    # -----------------
    # ADMIN
    # -----------------
    path('admin/', admin.site.urls),

    # -----------------
    # EMPLOYEE / AUTH
    # -----------------
    path('employee_form/', views.employee_form, name='employee_form'),
    path('login/', views.loginform_form, name='login'),

    # -----------------
    # AGENCIES
    # -----------------
    path('api/getagencies/', views.get_agencies, name='get_agencies'),

    # -----------------
    # EMPLOYEES
    # -----------------
    path('api/getemployees', views.get_active_employees, name='get_employees'),
    path('api/getallemployees/', views.get_all_employees, name='get_all_employees'),
    path('api/deactivate-employee/<int:employee_id>/', views.deactivate_employee, name='deactivate_employee'),
    path('api/activate-employee/<int:employee_id>/', views.activate_employee, name='activate_employee'),

    # IMPORTANT: you have frontend calls without trailing slash sometimes
    path('api/getoutletemployees/', views.get_outlet_employees, name='get_outletemployees'),
    path('api/getoutletemployees', views.get_outlet_employees),  # alias: no trailing slash

    path('api/employees/create', views.create_employee, name='create_employee'),
    path('api/editemployees/<int:employee_id>/', views.edit_employee, name='edit_delete_employee'),
    path('api/changepassword/<int:employee_id>/', views.ChangepswrdView.as_view(), name='edit-password'),

    # -----------------
    # GROUPS (your original endpoints preserved)
    # -----------------
    path('api/groups/', views.get_groups, name='get_groups'),

    # You had duplicate same path for GET + POST which is not valid in Django routing.
    # Keeping BOTH by giving POST a different URL while keeping old one too.
    path('api/group/', views.list_groups, name='list_groups'),   # keep
    path('api/group/create/', views.create_group, name='create_group'),  # FIXED (new)
    path('api/group/<int:id>/', views.group_detail, name='group_detail'),
    path('api/group/<int:id>/update/', views.update_group, name='update_group'),
    path('api/group/<int:id>/deactivate/', views.deactivate_group, name='deactivate_group'),

    # Optional aliases without slash for safety (doesn't break anything)
    path('api/group', views.list_groups),
    path('api/group/create', views.create_group),

    # -----------------
    # HOLIDAYS / LEAVES
    # -----------------
    path('api/holidays/', views.HolidayListCreateAPIView.as_view(), name='holiday-list-create'),
    path('api/holidays/<int:pk>/', views.HolidayDetailUpdateAPIView.as_view(), name='holiday-detail-update'),

    path('api/leavetypes/', views.LeaveTypeListCreateAPIView.as_view(), name='leave-type-list-create'),
    path('api/leavetypes/<int:pk>/', views.LeaveTypeDetailUpdateAPIView.as_view(), name='leave-type-detail-update'),

    # -----------------
    # USER
    # -----------------
    path('api/user/', views.current_user, name='current-user'),
    path('api/users/', include('users.apiurls')),

    # -----------------
    # AGENCIES CRUD
    # -----------------
    path('api/agencies/', views.create_agency, name='create-agency'),
    path('api/agencies/<int:id>/', views.update_agency, name='update-agency'),

    # -----------------
    # OUTLETS
    # -----------------
    path('api/outlets/create', views.create_outlet, name='outlet-create'),
    path('api/outlets/', views.get_outlets, name='outlet-detail'),
    path('api/outlets/<int:id>/', views.get_outlets, name='outlet-detail'),
    path('api/outlets/manage/<int:id>/',  views.update_or_delete_outlet, name='outlet-manage'),

    # -----------------
    # ROLES
    # -----------------
    path('api/create-role/', views.create_role, name='create-role'),

    # -----------------
    # JWT TOKEN
    # -----------------
    path('api/token/', CustomTokenObtainpairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # -----------------
    # DEVICES
    # -----------------
    path('api/devices/', views.get_all_devices, name='get_all_devices'),
    path('api/devices/delete/', views.delete_device, name='delete_device'),

    # -----------------
    # ATTENDANCE
    # -----------------
    path('api/attendance/all/', views.AllAttendanceRecordsView.as_view(), name='all_attendance_records'),
    path('api/attendance/', include('attendance.apiurls')),
    path('attendance/', include('attendance.urls')),

    # -----------------
    # FACE TOOL
    # -----------------
    path('admintool/', include('face_recognition.urls')),

    # -----------------
    # OUTLET DETAILS
    # -----------------
    path('outletsalldata/<int:pk>/', OutletDetailView.as_view(), name='outlet-detail'),

    # -----------------
    # SIMPLE LISTS
    # -----------------
    path('api/simple-employees/', views.get_simple_employees, name='simple_employees'),
    path('api/simple-leave-requests/', views.get_simple_leave_requests, name='simple_leave_requests'),

    # -----------------
    # REPORTS
    # -----------------
    path('report/', include('report.urls')),

    # -----------------
    # OTHER APPS (if any)
    # -----------------
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
