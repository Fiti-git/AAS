from django.db import models
from django.contrib.auth.models import User, Group
import uuid
from django.core.exceptions import ValidationError

# Employee Model
class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.AutoField(primary_key=True)
    empcode =  models.CharField(max_length=20, null=True)
    fullname = models.CharField(max_length=255)
    idnumber = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    profile_photo = models.URLField(null=True, blank=True)
    date_of_birth = models.DateField()
    outlets = models.ManyToManyField('Outlet', related_name='employees', blank=True)
    cal_epf = models.BooleanField(default=True)
    epf_cal_date = models.DateField(null=True, blank=True)
    epf_grade = models.CharField(max_length=20, null=True, blank=True)
    epf_number = models.CharField(max_length=20, null=True, blank=True)
    employ_number = models.BigIntegerField( null=True, blank=True)
    basic_salary = models.FloatField(null=True, blank=True)
    epf_com_per = models.FloatField(default=8.0, null=True, blank=True)
    epf_emp_per = models.FloatField(default=5.0, null=True, blank=True)
    etf_com_per = models.FloatField(default=3.0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.fullname

# Attendance Model
class Attendance(models.Model):
    # Status choices
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Late', 'Late'),
        ('Half Day', 'Half Day'),
        ('Absent', 'Absent'),
        ('On Leave', 'On Leave'),
    ]
    
    # Verification status choices
    VERIFICATION_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Rejected', 'Rejected'),
        ('Requires Review', 'Requires Review'),
    ]

    attendance_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in_time = models.DateTimeField()
    check_in_lat = models.FloatField()
    check_in_long = models.FloatField()
    photo_check_in = models.URLField(max_length=500, null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    check_out_lat = models.FloatField(null=True, blank=True)
    check_out_long = models.FloatField(null=True, blank=True)
    photo_check_out = models.URLField(max_length=500, null=True, blank=True)
    worked_hours = models.FloatField(null=True, blank=True)
    ot_hours = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Present')
    verified = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verification_notes = models.TextField(null=True, blank=True)  # For admin comments
    
    class Meta:
        unique_together = ('employee', 'date')  # Prevent duplicate entries
        ordering = ['-date', 'employee']
        verbose_name_plural = 'Attendance Records'
    
    def __str__(self):
        return f"{self.employee.fullname} - {self.date} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate worked hours when punching out
        if self.check_out_time and self.check_in_time:
            delta = self.check_out_time - self.check_in_time
            self.worked_hours = round(delta.total_seconds() / 3600, 2)
            
            # Auto-determine status based on worked hours
            if self.worked_hours < 4:
                self.status = 'Half Day'
            elif self.worked_hours > 8:
                self.ot_hours = self.worked_hours - 8
        super().save(*args, **kwargs)
    
class LeaveType(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly adding an auto-incrementing primary key field
    att_type = models.CharField(max_length=50, unique=True)  # Unique identifier for attendance type
    att_type_name = models.CharField(max_length=255)  # Name of the attendance type
    active = models.BooleanField(default=True)  # Whether the leave type is active or not
    att_type_group = models.CharField(max_length=100)  # Group or category of the leave type
    att_type_per_day_hours = models.DecimalField(max_digits=5, decimal_places=2)  # Number of hours allocated per day for this leave type
    pay_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage of pay allocated for this leave type
    att_type_no_of_days_in_year = models.IntegerField()  # Number of leave days allowed per year
    year_start_date = models.DateField()  # Start date of the leave year
    year_end_date = models.DateField()  # End date of the leave year

    def __str__(self):
        return f"{self.att_type_name} ({self.att_type})"

    class Meta:
        db_table = 'leave_type'

class Holiday(models.Model):
    id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    hcode = models.CharField(max_length=50)  # Holiday code, unique for each holiday
    holiday_name = models.CharField(max_length=255)  # Name of the holiday (e.g. Independence Day)
    holiday_type = models.CharField(max_length=50)  # Type of holiday (e.g. public, company)
    holiday_type_name = models.CharField(max_length=100)  # Human-readable type name
    hdate = models.DateField()  # Date of holiday
    active = models.BooleanField(default=True)  # Whether the holiday is currently active
    holiday_ot_pay_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Extra OT pay on this day
    holiday_regular_pay_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Base pay if worked on holiday

    def __str__(self):
        return f"{self.holiday_name} ({self.hcode})"

    class Meta:
        db_table = 'holiday'

class EmpLeave(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    leave_refno = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_date = models.DateField()
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)  # New field for remarks
    add_date = models.DateField(auto_now_add=True)
    action_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="leave_actioned_by")
    action_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Leave {self.leave_refno} - {self.employee.fullname}"

# Agency Model (Optional for context)
class Agency(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Outlets Model
class Outlet(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_meters = models.IntegerField()  # Allowed punch radius in meters
    manager = models.ForeignKey(Employee, related_name="outlet_manager", on_delete=models.SET_NULL, null=True, blank=True)  # Outlet manager is an employee
    agency = models.ForeignKey(Agency, null=True, blank=True, on_delete=models.SET_NULL)  # Optional Agency
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(default=1)

    def __str__(self):
        return self.name

class Role(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    designation = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.group.name  # Returns the group name as a string representation

    class Meta:
        db_table = 'role'

class Devices(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(max_length=50, choices=[
        ('personal', 'Personal'),
        ('company', 'Company'),
    ])
    registered_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Enforce that exactly one of `user` or `outlet` is set
        if bool(self.user) == bool(self.outlet):
            raise ValidationError("Device must be linked to either a user or an outlet, not both or neither.")

    def __str__(self):
        target = self.user.username if self.user else self.outlet.name if self.outlet else "Unassigned"
        return f"{self.device_type} - {target}"

