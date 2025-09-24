# serializers.py
from rest_framework import serializers
from .models import Outlet, EmpLeave, Holiday, Attendance, Employee, Agency, Holiday , LeaveType

class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.fullname', read_only=True)
    punchin_selfie_url = serializers.ImageField(source='employee.punchin_selfie', read_only=True)
    punchout_selfie_url = serializers.ImageField(source='employee.punchout_selfie', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'attendance_id',
            'employee',
            'employee_name',
            'date',
            'check_in_time',
            'check_in_lat',
            'check_in_long',
            'check_out_time',
            'check_out_lat',
            'check_out_long',
            'worked_hours',
            'ot_hours',
            'status',
            'punchin_verification',
            'punchout_verification',
            'verification_notes',
            'created_at',
            'updated_at',
            'punchin_selfie_url',
            'punchout_selfie_url',
        ]
        read_only_fields = [
            'attendance_id', 'worked_hours', 'ot_hours', 'status', 
            'punchin_verification', 'punchout_verification', 
            'created_at', 'updated_at'
        ]


class OutletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outlet
        fields = '__all__'

class EmpLeaveSerializer(serializers.ModelSerializer):
    leave_type_id = serializers.IntegerField(source='leave_type.id', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.att_type_name', read_only=True)
    employee_name = serializers.CharField(source='employee.user.get_full_name', read_only=True)

    class Meta:
        model = EmpLeave
        fields = [
            'leave_refno',
            'leave_date',
            'remarks',
            'add_date',
            'action_date',
            'status',
            'employee',
            'employee_name',
            'leave_type_id',
            'leave_type_name',
            'action_user'
        ]


class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    groups = serializers.SerializerMethodField()
    outlets = serializers.PrimaryKeyRelatedField(queryset=Outlet.objects.all(), many=True)


    class Meta:
        model = Employee
        fields = [
            'employee_id',
            'fullname',
            'empcode',
            'idnumber',
            'phone_number',
            'date_of_birth',
            'outlets',
            'cal_epf',
            'epf_cal_date',
            'epf_grade',
            'epf_number',
            'employ_number',
            'basic_salary',
            'epf_com_per',
            'epf_emp_per',
            'etf_com_per',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'groups',
            'reference_photo',
            'punchin_selfie',
            'punchout_selfie',
            'is_active',
            'inactive_date',
        ]
        
        read_only_fields = [
            'employee_id',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'groups',
            'reference_photo',
            'punchin_selfie',
            'punchout_selfie',
        ]

    def get_groups(self, obj):
        return [group.name for group in obj.user.groups.all()]

class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = '__all__'

class HolidaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Holiday
        fields = '__all__'
        read_only_fields = ('id',)

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'
        read_only_fields = ('id',)

class EmployeeDetailSerializer(EmployeeSerializer):
    """
    A detailed serializer for an employee that includes their related
    attendance and leave records.
    """
    # The 'attendances' related_name comes from the ForeignKey in the Attendance model
    attendances = AttendanceSerializer(many=True, read_only=True)
    
    # The 'empleave_set' is the default related_name for the ForeignKey in EmpLeave
    leaves = EmpLeaveSerializer(many=True, read_only=True, source='empleave_set')

    class Meta(EmployeeSerializer.Meta):
        # Inherit the Meta class from the base EmployeeSerializer
        # and add the new nested fields to the fields list.
        fields = EmployeeSerializer.Meta.fields + ['attendances', 'leaves']

class OutletDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for a single Outlet that includes only active employees
    with their full details.
    """
    employees = serializers.SerializerMethodField()

    class Meta:
        model = Outlet
        fields = [
            'id',
            'name',
            # add other outlet fields
            'employees'
        ]

    def get_employees(self, obj):
        # Use the Prefetch alias if present, otherwise fall back
        employees_qs = getattr(obj, "active_employees", obj.employees.all())
        return EmployeeDetailSerializer(employees_qs, many=True).data
