"""
URL configuration for aas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from main import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.decorators import permission_classes

urlpatterns = [
    path('admin/', admin.site.urls),
    path('employee_form/', views.employee_form, name='employee_form'),  # Link to the employee form
    path('api/agencies/', views.get_agencies, name='get_agencies'),
    path('api/employees/', views.create_employee, name='create_employee'),
    path('api/groups/', views.get_groups, name='get_groups'),
    path('login/', views.loginform_form, name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/user/', views.current_user, name='current-user'),
    path('api/outlets/create', views.create_outlet, name='outlet-create'),
    path('api/outlets/', views.get_outlets, name='outlet-detail'),
    path('api/outlets/<int:id>/', views.get_outlets, name='outlet-detail'),
    path('api/outlets/manage/<int:id>/',  views.get_outlets, name='outlet-manage'),
    path('api/attendance/', include('attendance.apiurls')),
    path('attendance/', include('attendance.urls')),
    path('api/group/', views.list_groups),  # GET all groups
    path('api/group/', views.create_group, name='create_group'),  # POST to create new group
    path('api/group/<int:id>/', views.group_detail, name='group_detail'),  # GET group details
    path('api/group/<int:id>/', views.update_group, name='update_group'),  # PUT to update group
    path('api/group/<int:id>/', views.deactivate_group, name='deactivate_group'),

    path('api/token/', permission_classes([])(TokenObtainPairView.as_view()), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # refresh
]
