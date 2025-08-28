import os
import zipfile
from io import BytesIO
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.paginator import Paginator
from main.models import Employee

# Create your views here.
def attendance_page(request):
    return render(request, 'attendance.html')  # Path to the HTML file

def download_employee_images(request):
    """Display list of employees with training images for download"""
    # Get employees who have training images
    employees_with_images = Employee.objects.filter(
        training_images__isnull=False
    ).distinct().order_by('fullname')
    
    # Add image count to each employee
    for employee in employees_with_images:
        employee.image_count = employee.training_images.count()
    
    # Pagination (optional)
    paginator = Paginator(employees_with_images, 20)
    page_number = request.GET.get('page')
    employees = paginator.get_page(page_number)
    
    context = {
        'employees': employees,
        'title': 'Download Employee Training Images'
    }
    return render(request, 'download_images.html', context)

def download_employee_folder(request, employee_id):
    """Download all training images for a specific employee as a ZIP file"""
    employee = get_object_or_404(Employee, employee_id=employee_id)
    training_images = employee.training_images.all()
    
    if not training_images.exists():
        raise Http404("No training images found for this employee")
    
    # Create a BytesIO object to store the zip file
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for training_image in training_images:
            try:
                # Get the full path to the image file
                image_path = training_image.image.path
                if os.path.exists(image_path):
                    # Add file to zip with just the filename (not full path)
                    zip_file.write(image_path, os.path.basename(image_path))
            except Exception as e:
                # Log error but continue with other images
                print(f"Error adding {training_image.image.name} to zip: {e}")
                continue
    
    zip_buffer.seek(0)
    
    # Create HTTP response with zip file
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    filename = f"{employee.fullname.replace(' ', '_')}_training_images.zip"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response