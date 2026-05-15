import logging
import os

try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        return func

from django.db import close_old_connections
from django.utils import timezone

from accounts.models import UserTrustScore
from task.models import TaskSubmission
from wallet.models import Wallet, Transaction
from verification.utils import run_submission_verification, run_facebook_group_verification

logger = logging.getLogger(__name__)


@shared_task
def verify_submission(submission_id):
    submission = TaskSubmission.objects.get(id=submission_id)
    submission.verification_attempts += 1
    submission.last_verification_attempt = timezone.now()
    submission.status = 'level1_pending'
    submission.save()

    if submission.task.task_type == 'share':
        from verification.utils import sync_playwright
        if sync_playwright is not None:
            result = run_facebook_group_verification(submission)
        else:
            result = run_submission_verification(submission)
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
        if flag in (
            'invalid_facebook_path',
            'graph_api_failed',
            'private_or_hidden_post',
            'screenshot_inconclusive',
            'fake_link',
            'invalid_url',
            'not_facebook',
        ):
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

    return result


def _run_verification_in_thread(submission_id):
    close_old_connections()
    try:
        verify_submission(submission_id)
    except Exception:
        logger.exception('Verification failed for submission %s', submission_id)
    finally:
        close_old_connections()


def start_verification(submission_id):
    """Run verification so dashboard stats update reliably (sync on Render/Gunicorn)."""
    use_celery = os.getenv('USE_CELERY', '').lower() in ('1', 'true', 'yes')
    if use_celery and hasattr(verify_submission, 'delay'):
        try:
            verify_submission.delay(submission_id)
            return
        except Exception:
            logger.warning(
                'Celery unavailable; running sync verification for submission %s',
                submission_id,
                exc_info=True,
            )

    # Gunicorn kills daemon threads — run in-request so wallet/status/trust update
    _run_verification_in_thread(submission_id)
