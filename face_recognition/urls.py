from django.urls import path
from . import views

urlpatterns = [
    path('embeddings/', views.update_embeddings, name='update_embeddings'),
]
