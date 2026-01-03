from rest_framework import serializers
from main.models import EmpLeave

class EmpLeaveSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='employee.user.username', read_only=True)
    first_name = serializers.CharField(source='employee.user.first_name', read_only=True)
    employee_id = serializers.IntegerField(source='employee.employee_id', read_only=True)

    att_type = serializers.CharField(source='leave_type.att_type', read_only=True)
    att_type_name = serializers.CharField(source='leave_type.att_type_name', read_only=True)

    class Meta:
        model = EmpLeave
        fields = [
            'leave_refno',
            'employee_id',
            'username',
            'first_name',
            'att_type',
            'att_type_name',
            'leave_date',
            'add_date',
            'action_date',
            'remarks',
            'status',
        ]
