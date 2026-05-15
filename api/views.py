# api/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from task.models import Task

@api_view(['GET'])
def get_tasks(request):
    tasks = Task.objects.filter(is_active=True).values(
        'id', 'title', 'description', 'task_type', 'action', 'target_link', 'reward', 'time_limit'
    )
    return Response(tasks)
