from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from api.views import get_tasks

urlpatterns = [
    path('auth/token/', obtain_auth_token, name='api_token'),
    path('tasks/', get_tasks, name='api_tasks'),
]
