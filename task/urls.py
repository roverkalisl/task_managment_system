# task/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.tasks, name='tasks'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('submit/<int:task_id>/', views.submit_task, name='submit_task'),
]
