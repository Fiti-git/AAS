from django.shortcuts import render, redirect
from django.http import JsonResponse
from rest_framework.decorators import api_view
from .models import Agency, Employee, Outlet, Role, Holiday , LeaveType
from django.contrib.auth.hashers import make_password
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User, Group
from .serializers import OutletSerializer, EmployeeSerializer, AgencySerializer, HolidaySerializer, LeaveTypeSerializer
from django.shortcuts import render
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView


def home(request):
    return render(request, 'home.html')  # Adjust path to the correct template if needed

# View to render the employee creation form
def employee_form(request):
    return render(request, 'employee.html')  # Path to the HTML file

# API to fetch agencies for the dropdown
@api_view(['GET'])
def get_agencies(request):
    agencies = Agency.objects.all().values('id', 'name', 'address')  # Add address here
    return JsonResponse(list(agencies), safe=False)

@api_view(['GET'])
def get_all_employees(request):
    employees = Employee.objects.all()
    serializer = EmployeeSerializer(employees, many=True)
    return Response(serializer.data)


# API to create an employee (and user)
@api_view(['POST'])
def create_employee(request):
    if request.method == 'POST':
        data = request.data
        
        # Extract employee data from the request
        fullname = data.get('fullname')
        email = data.get('email')
        phone_number = data.get('phone_number', '')
        agency_id = data.get('agency')
        date_of_birth = data.get('date_of_birth')
        profile_photo = data.get('profile_photo', '')
        password = data.get('password')
        username = data.get('fullname')  # The username to assign to the user
        first_name = data.get('first_name')  # The first name of the user
        last_name = data.get('last_name')  # The last name of the user
        group_id = data.get('group', '')  # The group to assign to the user (optional)

        # Create user
        user = User.objects.create_user(
            username=username,  # Username from the request
            email=email,
            password=password,
            first_name=first_name,  # First name from the request
            last_name=last_name,  # Last name from the request
        )

        # Optionally assign the user to a group if provided
        if group_id:
            group, created = Group.objects.get_or_create(id=group_id)
            user.groups.add(group)

        # Create employee
        employee = Employee.objects.create(
            user=user,
            fullname=fullname,
            phone_number=phone_number,
            profile_photo=profile_photo,
            date_of_birth=date_of_birth,
            outlet=agency_id,
        )

        return Response({'message': 'Employee created successfully!'}, status=status.HTTP_201_CREATED)

@api_view(['PUT', 'PATCH'])
def edit_employee(request, employee_id):
    try:
        data = request.data

        # Get employee and linked user
        employee = Employee.objects.get(id=employee_id)
        user = employee.user

        # Update User model fields
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)

        # Optional: update username and password
        if 'username' in data:
            user.username = data['username']
        if 'password' in data and data['password']:
            user.set_password(data['password'])

        # Handle user activation/deactivation
        if 'is_active' in data:
            user.is_active = data['is_active']

        # Optionally update group
        group_id = data.get('group', None)
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                user.groups.clear()
                user.groups.add(group)
            except Group.DoesNotExist:
                return Response({'error': 'Group not found.'}, status=status.HTTP_400_BAD_REQUEST)

        user.save()

        # Update Employee model fields
        employee.fullname = data.get('fullname', employee.fullname)
        employee.phone_number = data.get('phone_number', employee.phone_number)
        employee.profile_photo = data.get('profile_photo', employee.profile_photo)
        employee.date_of_birth = data.get('date_of_birth', employee.date_of_birth)
        employee.outlet_id = data.get('agency', employee.outlet_id)

        employee.save()

        return Response({'message': 'Employee updated successfully.'}, status=status.HTTP_200_OK)

    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def current_user(request):
    if request.user.is_authenticated:
        employee = getattr(request.user, 'employee', None)

        if not employee:
            return Response({"error": "Employee profile not found"}, status=404)

        outlet_ids = getattr(employee, 'outlet', []) or []
        
        if not outlet_ids:
            outlets = []
        else:
            outlets = Outlet.objects.filter(id__in=outlet_ids).values('id', 'name')

        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "outlets": list(outlets)
        })

    return Response({"error": "Not authenticated"}, status=401)

    
@api_view(['POST'])
def create_agency(request):
    serializer = AgencySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def update_agency(request, id):
    try:
        agency = Agency.objects.get(id=id)
    except Agency.DoesNotExist:
        return Response({'error': 'Agency not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = AgencySerializer(agency, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(['GET'])
def get_groups(request):
    # Fetch all groups
    groups = Group.objects.all().values('id', 'name')  # Get group id and name
    return JsonResponse(list(groups), safe=False)

@api_view(['POST'])
def create_outlet(request):
    serializer = OutletSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH', 'DELETE'])
def update_or_delete_outlet(request, id):
    try:
        outlet = Outlet.objects.get(pk=id)
    except Outlet.DoesNotExist:
        return Response({'error': 'Outlet not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        serializer = OutletSerializer(outlet, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        outlet.status = 0
        outlet.save()
        return Response({'message': 'Outlet marked as inactive'}, status=status.HTTP_200_OK)

    return Response({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
def get_outlets(request, id=None):
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
    

@api_view(['GET'])
def list_groups(request):
    groups = Group.objects.all()
    group_names = [{"id": group.id, "name": group.name} for group in groups]
    return Response(group_names)

@api_view(['POST'])
def create_group(request):
    group_name = request.data.get('name')
    designation = request.data.get('designation')
    description = request.data.get('description')

    if not group_name:
        return Response({"detail": "Group name is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Create the Group object
    group = Group.objects.create(name=group_name)

    # Create the associated Role object
    if designation:
        role = Role.objects.create(
            group=group, 
            designation=designation, 
            description=description
        )
    else:
        return Response({"detail": "Designation required."}, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "id": group.id,
        "name": group.name,
        "role_id": role.id,
        "designation": role.designation,
        "description": role.description
    }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def group_detail(request, id):
    try:
        group = Group.objects.get(id=id)
    except Group.DoesNotExist:
        return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    permissions = group.permissions.all()
    permissions_list = [{"id": permission.id, "name": permission.name} for permission in permissions]
    
    # Fetching the groupmeta description
    group_meta = group.groupmeta
    group_info = {
        "id": group.id,
        "name": group.name,
        "permissions": permissions_list
    }
    return Response(group_info)

@api_view(['PUT'])
def update_group(request, id):
    try:
        group = Group.objects.get(id=id)
    except Group.DoesNotExist:
        return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    group.name = request.data.get('name', group.name)
    group.save()

    return Response({"id": group.id, "name": group.name})

@api_view(['DELETE'])
def deactivate_group(request, id):
    try:
        group = Group.objects.get(id=id)
    except Group.DoesNotExist:
        return Response({"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND)

    # Get associated GroupMeta object
    try:
        group_meta = group.Role  # Assuming a OneToOne relationship
    except Role.DoesNotExist:
        return Response({"detail": "GroupMeta not found for this group."}, status=status.HTTP_404_NOT_FOUND)

    # Deactivate the group via GroupMeta
    group_meta.is_active = False
    group_meta.save()

    return Response({"detail": f"Group {group.name} has been deactivated."}, status=status.HTTP_200_OK)

class HolidayListCreateAPIView(APIView):
    def get(self, request):
        holidays = Holiday.objects.all()
        serializer = HolidaySerializer(holidays, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = HolidaySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HolidayDetailUpdateAPIView(APIView):
    def get(self, request, pk):
        holiday = get_object_or_404(Holiday, pk=pk)
        serializer = HolidaySerializer(holiday)
        return Response(serializer.data)

    def put(self, request, pk):
        holiday = get_object_or_404(Holiday, pk=pk)
        serializer = HolidaySerializer(holiday, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        holiday = get_object_or_404(Holiday, pk=pk)
        serializer = HolidaySerializer(holiday, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveTypeListCreateAPIView(APIView):
    def get(self, request):
        leave_types = LeaveType.objects.all()
        serializer = LeaveTypeSerializer(leave_types, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LeaveTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LeaveTypeDetailUpdateAPIView(APIView):
    def get(self, request, pk):
        leave_type = get_object_or_404(LeaveType, pk=pk)
        serializer = LeaveTypeSerializer(leave_type)
        return Response(serializer.data)

    def put(self, request, pk):
        leave_type = get_object_or_404(LeaveType, pk=pk)
        serializer = LeaveTypeSerializer(leave_type, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        leave_type = get_object_or_404(LeaveType, pk=pk)
        serializer = LeaveTypeSerializer(leave_type, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

def jwt_login_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            response = redirect('dashboard')  # or any other view
            response.set_cookie('access_token', str(refresh.access_token))  # or use sessionStorage/localStorage via JS
            return response
        else:
            return render(request, "login.html", {"form": {"errors": True}})
    return render(request, "login.html")

# View to render the employee creation form
def loginform_form(request):
    return render(request, 'login.html')  # Path to the HTML file