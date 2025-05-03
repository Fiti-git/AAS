from django.shortcuts import render

# Create your views here.
def attendance_page(request):
    return render(request, 'attendance.html')  # Path to the HTML file