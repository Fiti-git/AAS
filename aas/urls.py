from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.http import JsonResponse

from main import views
from main.views import OutletDetailView
from users.views import CustomTokenObtainpairView
from rest_framework_simplejwt.views import TokenRefreshView


# ------------------------------------------------------------------------------
# Health check (no DB, no auth)
# ------------------------------------------------------------------------------
def health(request):
    return JsonResponse({"status": "ok"})


# ------------------------------------------------------------------------------
# URL patterns
# ------------------------------------------------------------------------------
urlpatterns = [

    # ---- CORE / STATUS ----
    path('', views.home, name='home'),
    path('health/', health, name='health'),

    # ---- ADMIN ----
    path('admin/', admin.site.urls),

    # ---- AUTH ----
    path('login/', views.loginform_form, name='login'),
    path('api/token/', CustomTokenObtainpairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ---- USER / PROFILE ----
    path('api/user/', views.current_user, name='current_user'),
    path('api/users/', include('users.apiurls')),

    # ---- EMPLOYEES ----
    path('employee_form/', views.employee_form, name='employee_form'),
    path('api/getemployees/', views.get_active_employees),
    path('api/getallemployees/', views.get_all_employees),
    path('api/simple-employees/', views.get_simple_employees),
    path('api/deactivate-employee/<int:employee_id>/', views.deactivate_employee),
    path('api/editemployees/<int:employee_id>/', views.edit_employee),
    path('api/changepassword/<int:employee_id>/', views.ChangepswrdView.as_view()),

    # ---- AGENCIES ----
    path('api/getagencies/', views.get_agencies),
    path('api/agencies/', views.create_agency),                 # POST
    path('api/agencies/<int:id>/', views.update_agency),        # PUT / DELETE

    # ---- OUTLETS ----
    path('api/outlets/', views.get_outlets),                    # GET
    path('api/outlets/create/', views.create_outlet),           # POST
    path('api/outlets/manage/<int:id>/', views.update_or_delete_outlet),
    path('outletsalldata/<int:pk>/', OutletDetailView.as_view()),

    # ---- GROUPS (FIXED CONFLICT) ----
    path('api/groups/', views.list_groups),                     # GET
    path('api/groups/create/', views.create_group),             # POST
    path('api/groups/<int:id>/', views.group_detail),           # GET
    path('api/groups/<int:id>/update/', views.update_group),    # PUT
    path('api/groups/<int:id>/deactivate/', views.deactivate_group),

    # ---- ROLES ----
    path('api/create-role/', views.create_role),

    # ---- HOLIDAYS ----
    path('api/holidays/', views.HolidayListCreateAPIView.as_view()),
    path('api/holidays/<int:pk>/', views.HolidayDetailUpdateAPIView.as_view()),

    # ---- LEAVE TYPES ----
    path('api/leavetypes/', views.LeaveTypeListCreateAPIView.as_view()),
    path('api/leavetypes/<int:pk>/', views.LeaveTypeDetailUpdateAPIView.as_view()),

    # ---- DEVICES ----
    path('api/devices/', views.get_all_devices),
    path('api/devices/delete/', views.delete_device),

    # ---- ATTENDANCE ----
    path('api/attendance/all/', views.AllAttendanceRecordsView.as_view()),
    path('api/attendance/', include('attendance.apiurls')),
    path('attendance/', include('attendance.urls')),

    # ---- FACE / ADMIN TOOL ----
    path('admintool/', include('face_recognition.urls')),

    # ---- REPORTS ----
    path('report/', include('report.urls')),
]


# ------------------------------------------------------------------------------
# MEDIA (DEV ONLY)
# ------------------------------------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
