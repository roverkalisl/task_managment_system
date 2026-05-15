from threading import Thread

from django.utils import timezone

from accounts.models import UserTrustScore
from task.models import TaskSubmission
from wallet.models import Wallet, Transaction
from verification.utils import run_submission_verification


def verify_submission(submission_id):
    submission = TaskSubmission.objects.get(id=submission_id)
    submission.verification_attempts += 1
    submission.last_verification_attempt = timezone.now()
    submission.status = 'level1_pending'
    submission.save()

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


def start_verification(submission_id):
    Thread(target=verify_submission, args=(submission_id,)).start()
