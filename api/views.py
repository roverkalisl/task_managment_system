# api/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from task.models import Task


@api_view(['GET'])
@permission_classes([AllowAny])
def get_tasks(request):
    tasks = Task.objects.filter(is_active=True).values(
        'id',
        'title',
        'description',
        'task_type',
        'target_link',
        'reward',
        'total_slots',
        'completed_slots',
        'is_active',
        'created_at',
    )
    return Response(list(tasks))
