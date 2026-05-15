from django.contrib import admin
from .models import Task, TaskSubmission


# 📋 TASK ADMIN
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'task_type',
        'reward',
        'total_slots',
        'completed_slots',
        'is_active',
        'created_at'
    )

    list_filter = (
        'task_type',
        'is_active',
        'created_at'
    )

    search_fields = (
        'title',
        'description',
        'target_link'
    )


# 📤 TASK SUBMISSION ADMIN
@admin.register(TaskSubmission)
class TaskSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'task',
        'status',
        'is_suspicious',
        'level1_passed',
        'level2_passed',
        'level3_passed',
        'submitted_at',
        'verified_at'
    )

    list_filter = (
        'status',
        'is_suspicious',
        'level1_passed',
        'level2_passed',
        'submitted_at'
    )

    search_fields = (
        'user__username',
        'submitted_link',
        'fraud_flags'
    )

    readonly_fields = (
        'verified_at',
        'level1_confidence',
        'level2_confidence',
        'level3_confidence',
        'fraud_flags',
    )