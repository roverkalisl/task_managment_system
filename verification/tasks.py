try:
    from celery import shared_task
except ImportError:
    # Fallback if Celery not available
    def shared_task(func):
        return func

from django.utils import timezone

from accounts.models import UserTrustScore
from task.models import TaskSubmission
from wallet.models import Wallet, Transaction
from verification.utils import run_submission_verification, run_facebook_group_verification


@shared_task
def verify_submission(submission_id):
    submission = TaskSubmission.objects.get(id=submission_id)
    submission.verification_attempts += 1
    submission.last_verification_attempt = timezone.now()
    submission.status = 'level1_pending'
    submission.save()

    # Use appropriate verification based on task type
    if submission.task.task_type == 'share':
        result = run_facebook_group_verification(submission)
    else:
        result = run_submission_verification(submission)

    submission.level1_passed = result['level1_passed']
    submission.level1_confidence = result['level1_confidence']
    submission.level2_passed = result['level2_passed']
    submission.level2_confidence = result['level2_confidence']
    submission.level3_passed = result['level3_passed']
    submission.level3_confidence = result['level3_confidence']
    submission.fraud_flags = result.get('fraud_flags', [])
    submission.feedback = result.get('reason')
    submission.verified_at = timezone.now()

    # Save group information if available
    group_info = result.get('group_info')
    if group_info:
        submission.group_name = group_info.get('name')
        submission.group_link = group_info.get('link')
        submission.group_visibility = group_info.get('visibility')

    user_trust, _ = UserTrustScore.objects.get_or_create(user=submission.user)
    user_trust.total_submissions += 1
    if result['valid'] and not result['needs_review']:
        user_trust.approved_submissions += 1
    elif not result['valid']:
        user_trust.rejected_submissions += 1

    for flag in submission.fraud_flags:
        if flag == 'duplicate_link':
            user_trust.duplicate_links_count += 1
        if flag == 'fast_submission':
            user_trust.fast_submissions_count += 1
        if flag == 'invalid_facebook_path' or flag == 'graph_api_failed':
            user_trust.suspicious_patterns_count += 1
        if flag == 'private_or_hidden_post' or flag == 'screenshot_inconclusive':
            user_trust.suspicious_patterns_count += 1
        if flag == 'fake_link' or flag == 'invalid_url' or flag == 'not_facebook':
            user_trust.suspicious_patterns_count += 1

    user_trust.last_submission_at = submission.submitted_at
    user_trust.update_trust_score()

    if result['valid'] and not result['needs_review']:
        submission.status = 'approved'
        submission.save()

        wallet, _ = Wallet.objects.get_or_create(user=submission.user)
        wallet.balance += submission.task.reward
        wallet.save()

        Transaction.objects.create(
            user=submission.user,
            amount=submission.task.reward,
            transaction_type='reward',
            status='completed',
            reference=f'task-{submission.task.id}-submission-{submission.id}',
        )

        submission.task.completed_slots += 1
        submission.task.save()
    elif result['valid'] and result['needs_review']:
        submission.status = 'manual_review'
        submission.save()
    else:
        submission.status = 'rejected'
        submission.save()

    # Return result for potential chaining
    return result


def start_verification(submission_id):
    """Start verification asynchronously using Celery"""
    verify_submission.delay(submission_id)
