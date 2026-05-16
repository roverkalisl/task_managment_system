from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import DatabaseError
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Task, TaskSubmission
from wallet.models import Wallet, Transaction

_url_validator = URLValidator()

try:
    from verification.tasks import start_verification
except ImportError:
    # Fallback if verification not available
    def start_verification(submission_id):
        pass


# 📋 TASK LIST
@login_required
def tasks_view(request):
    tasks = Task.objects.filter(is_active=True)
    return render(request, 'tasks.html', {'tasks': tasks})


# 📤 SUBMIT TASK (FINAL)
@login_required
def submit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # ❌ duplicate block
    if TaskSubmission.objects.filter(user=request.user, task=task).exists():
        return redirect('dashboard')

    if request.method == "POST":
        link = request.POST.get("link")
        screenshot = request.FILES.get("screenshot")

        if not link:
            return render(request, 'submit_task.html', {
                'task': task,
                'error': 'Please enter a link'
            })

        link = link.strip()
        if not link.startswith(('http://', 'https://')):
            link = f'https://{link}'

        try:
            _url_validator(link)
        except ValidationError:
            return render(request, 'submit_task.html', {
                'task': task,
                'error': 'Please enter a valid URL (e.g. https://facebook.com/...)',
            })

        try:
            submission = TaskSubmission.objects.create(
                user=request.user,
                task=task,
                submitted_link=link,
                screenshot=screenshot,
                status='level1_pending',
            )
        except (ValidationError, DatabaseError):
            return render(request, 'submit_task.html', {
                'task': task,
                'error': 'Could not save submission. Ask admin to run database migrations.',
            })

        try:
            start_verification(submission.id)
        except Exception:
            pass

        return redirect('dashboard')

    return render(request, 'submit_task.html', {'task': task})


@login_required
def create_task_view(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        task_type = request.POST.get('task_type')
        target_link = request.POST.get('target_link')
        reward = request.POST.get('reward')
        total_slots = request.POST.get('total_slots')

        if not title or not target_link or not reward:
            return render(request, 'create_task.html', {
                'error': 'Title, target link, and reward are required.'
            })

        Task.objects.create(
            title=title,
            description=description,
            task_type=task_type,
            target_link=target_link,
            reward=reward,
            total_slots=total_slots or 100,
        )
        return redirect('tasks')

    return render(request, 'create_task.html')


# 📊 DASHBOARD
@login_required
def dashboard(request):
    from accounts.models import UserTrustScore

    user = request.user

    total_tasks = Task.objects.filter(is_active=True).count()

    user_submissions = TaskSubmission.objects.filter(user=user)
    completed = user_submissions.filter(status='approved').count()
    pending_count = user_submissions.filter(
        status__in=[
            'pending',
            'level1_pending',
            'level2_pending',
            'level3_pending',
            'manual_review',
        ]
    ).count()
    rejected_count = user_submissions.filter(status='rejected').count()

    wallet, _ = Wallet.objects.get_or_create(user=user)
    trust, _ = UserTrustScore.objects.get_or_create(user=user)
    recent_submissions = user_submissions.select_related('task').order_by('-submitted_at')[:5]

    return render(request, 'dashboard.html', {
        'total_tasks': total_tasks,
        'completed': completed,
        'pending_count': pending_count,
        'rejected_count': rejected_count,
        'balance': wallet.balance,
        'trust_score': trust.trust_score,
        'recent_submissions': recent_submissions,
    })


@login_required
def review_submissions(request):
    if not request.user.is_staff:
        raise PermissionDenied()

    submissions = TaskSubmission.objects.select_related('user', 'task').order_by('-submitted_at')
    manual_queue = submissions.filter(status='manual_review')
    auto_queue = submissions.filter(status__in=['level1_pending', 'level2_pending', 'level3_pending'])
    return render(request, 'review_submissions.html', {
        'manual_queue': manual_queue,
        'auto_queue': auto_queue,
    })


@login_required
@require_POST
def rerun_verification(request, submission_id):
    if not request.user.is_staff:
        raise PermissionDenied()

    submission = get_object_or_404(TaskSubmission, id=submission_id)
    submission.status = 'level1_pending'
    submission.feedback = 'Staff requested auto re-verification.'
    submission.verified_at = None
    submission.save()

    try:
        start_verification(submission.id)
    except Exception:
        pass

    return redirect('review_submissions')
