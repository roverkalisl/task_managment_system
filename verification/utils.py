import os
import re
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.utils import timezone

try:
    import requests
except ImportError:
    requests = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

FACEBOOK_GRAPH_BASE = 'https://graph.facebook.com/v17.0'
FACEBOOK_PATH_PATTERNS = [
    '/posts/',
    '/permalink.php',
    '/story.php',
    '/photo.php',
    '/photos/',
    '/video.php',
    '/videos/',
    '/watch/',
    '/groups/',
]


def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and parsed.netloc != ''
    except Exception:
        return False


def is_facebook_link(url):
    if not is_valid_url(url):
        return False
    return 'facebook.com' in urlparse(url).netloc.lower()


def extract_facebook_post_id(url):
    parsed = urlparse(url)
    path = parsed.path or ''
    query = parsed.query or ''

    if '/posts/' in path:
        return path.split('/posts/')[-1].split('/')[0]
    if '/permalink.php' in path and 'story_fbid=' in query:
        return query.split('story_fbid=')[-1].split('&')[0]
    if '/videos/' in path:
        return path.split('/videos/')[-1].split('/')[0]
    if '/story.php' in path and 'story_fbid=' in query:
        return query.split('story_fbid=')[-1].split('&')[0]
    return None


def check_http_access(url, timeout=10):
    if requests is None:
        return {
            'ok': True,
            'status_code': None,
            'reason': 'HTTP client unavailable; skipping accessibility check',
        }

    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        if response.status_code == 405 or response.status_code >= 400:
            response = requests.get(url, allow_redirects=True, timeout=timeout)

        return {
            'ok': response.status_code == 200,
            'status_code': response.status_code,
            'reason': f'HTTP status {response.status_code}',
        }
    except requests.RequestException as exc:
        return {
            'ok': False,
            'status_code': None,
            'reason': str(exc),
        }


def verify_facebook_post(url, access_token):
    if requests is None:
        return {
            'valid': True,
            'reason': 'Graph API unavailable; fallback to smart validation',
            'needs_review': True,
        }

    post_id = extract_facebook_post_id(url)
    if not post_id:
        return {
            'valid': False,
            'reason': 'Unable to extract Facebook post ID',
            'needs_review': True,
        }

    try:
        response = requests.get(
            f'{FACEBOOK_GRAPH_BASE}/{post_id}',
            params={
                'access_token': access_token,
                'fields': 'id,privacy,from,created_time',
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        privacy = data.get('privacy')
        is_public = privacy in ('EVERYONE', 'PUBLIC') or privacy is None
        return {
            'valid': True,
            'reason': 'Post verified via Graph API',
            'needs_review': not is_public,
            'data': data,
        }
    except Exception as exc:
        return {
            'valid': False,
            'reason': f'Graph API request failed: {exc}',
            'needs_review': True,
        }


def extract_text_from_image(image_path):
    if Image is None or pytesseract is None:
        return ''

    try:
        with Image.open(image_path) as image:
            return pytesseract.image_to_string(image)
    except Exception:
        return ''


def analyze_screenshot(screenshot, expected_url=None):
    if not screenshot:
        return {
            'valid': False,
            'confidence': 0.0,
            'needs_review': True,
            'reason': 'Screenshot not provided',
        }

    if Image is None or pytesseract is None:
        return {
            'valid': False,
            'confidence': 0.0,
            'needs_review': True,
            'reason': 'OCR support missing; install Pillow and pytesseract',
        }

    text = extract_text_from_image(screenshot.path).lower()
    has_facebook = 'facebook' in text or 'fb.me' in text
    has_ui_elements = any(term in text for term in ['like', 'comment', 'share', 'posted', 'public', 'friends'])
    has_expected_url = expected_url and expected_url.lower().split('?')[0] in text

    confidence = 0.0
    if has_facebook and has_ui_elements and has_expected_url:
        confidence = 0.95
    elif has_facebook and (has_ui_elements or has_expected_url):
        confidence = 0.75
    elif has_facebook or has_ui_elements:
        confidence = 0.55

    if confidence >= 0.75:
        reason = 'Screenshot appears to contain Facebook UI and matching content'
    elif confidence >= 0.5:
        reason = 'Screenshot contains partial Facebook indicators, manual review recommended'
    else:
        reason = 'Screenshot verification failed or is inconclusive'

    return {
        'valid': confidence >= 0.75,
        'confidence': confidence,
        'needs_review': confidence < 0.75,
        'reason': reason,
        'ocr_text': text,
    }


def is_valid_facebook_path(url):
    parsed = urlparse(url)
    path = (parsed.path or '').lower()
    query = (parsed.query or '').lower()
    if any(pattern in path for pattern in FACEBOOK_PATH_PATTERNS):
        return True
    if 'story_fbid=' in query:
        return True
    return False


def find_duplicate_submissions(url, user, exclude_id=None):
    from task.models import TaskSubmission

    query = TaskSubmission.objects.filter(submitted_link__iexact=url)
    if exclude_id:
        query = query.exclude(id=exclude_id)
    return query.count()


def detect_fast_submission(user, exclude_id=None, threshold_seconds=120):
    from task.models import TaskSubmission

    latest = TaskSubmission.objects.filter(user=user)
    if exclude_id:
        latest = latest.exclude(id=exclude_id)
    latest = latest.order_by('-submitted_at').first()
    if not latest or not latest.submitted_at:
        return False, None

    elapsed = timezone.now() - latest.submitted_at
    return elapsed.total_seconds() < threshold_seconds, elapsed


def smart_link_analysis(url, user, submission_id=None):
    flags = []
    confidence = 0.75
    reason_parts = []

    if not is_valid_facebook_path(url):
        return {
            'valid': False,
            'confidence': 0.0,
            'needs_review': False,
            'reason': 'Link does not match known Facebook content patterns',
            'flags': ['invalid_facebook_path'],
        }

    duplicate_count = find_duplicate_submissions(url, user, exclude_id=submission_id)
    if duplicate_count > 0:
        flags.append('duplicate_link')
        confidence -= 0.25
        reason_parts.append('Duplicate submission detected')

    too_fast, elapsed = detect_fast_submission(user, exclude_id=submission_id)
    if too_fast:
        flags.append('fast_submission')
        confidence -= 0.2
        reason_parts.append('Fast submission cadence')

    access_token = os.getenv('FACEBOOK_GRAPH_ACCESS_TOKEN') or getattr(settings, 'FACEBOOK_GRAPH_ACCESS_TOKEN', None)
    if access_token:
        graph_result = verify_facebook_post(url, access_token)
        if not graph_result['valid']:
            return {
                'valid': False,
                'confidence': 0.0,
                'needs_review': True,
                'reason': graph_result['reason'],
                'flags': flags + ['graph_api_failed'],
            }
        if graph_result.get('needs_review'):
            flags.append('private_or_hidden_post')
            confidence -= 0.15
            reason_parts.append('Facebook post is not fully public')
        else:
            confidence += 0.1
            reason_parts.append('Graph API verification succeeded')

    if flags:
        reason = 'Suspicious link analysis: ' + '; '.join(reason_parts)
    else:
        reason = 'Facebook link pattern analysis passed'

    return {
        'valid': True,
        'confidence': max(0.0, min(1.0, confidence)),
        'needs_review': len(flags) > 0,
        'reason': reason,
        'flags': flags,
    }


def level1_validation(url):
    if not is_valid_url(url):
        return {
            'valid': False,
            'confidence': 0.0,
            'needs_review': False,
            'reason': 'Invalid URL format',
        }

    if not is_facebook_link(url):
        return {
            'valid': False,
            'confidence': 0.0,
            'needs_review': False,
            'reason': 'The submitted link is not a Facebook URL',
        }

    access_result = check_http_access(url)
    if not access_result['ok']:
        return {
            'valid': False,
            'confidence': 0.0,
            'needs_review': False,
            'reason': f'Facebook URL is not accessible: {access_result["reason"]}',
        }

    if not is_valid_facebook_path(url):
        return {
            'valid': False,
            'confidence': 0.0,
            'needs_review': False,
            'reason': 'Facebook URL does not appear to contain a valid post, group, or permalink',
        }

    return {
        'valid': True,
        'confidence': 0.85,
        'needs_review': False,
        'reason': 'Level 1 validation passed',
    }


def run_submission_verification(submission):
    level1 = level1_validation(submission.submitted_link)
    level2 = None
    level3 = None

    if not level1['valid']:
        return {
            'level1_passed': False,
            'level1_confidence': level1['confidence'],
            'level2_passed': False,
            'level2_confidence': 0.0,
            'level3_passed': False,
            'level3_confidence': 0.0,
            'valid': False,
            'needs_review': False,
            'reason': level1['reason'],
            'fraud_flags': [],
        }

    level2 = smart_link_analysis(submission.submitted_link, submission.user, submission.id)
    level3 = analyze_screenshot(submission.screenshot, submission.submitted_link)

    level1_passed = True
    level2_passed = level2['valid']
    level3_passed = level3['valid']
    fraud_flags = level2.get('flags', [])
    if level3.get('needs_review'):
        fraud_flags.append('screenshot_inconclusive')

    overall_confidence = sum([
        level1['confidence'],
        level2['confidence'],
        level3['confidence'] if submission.screenshot else 0.0,
    ]) / (3 if submission.screenshot else 2)

    valid = level1_passed and level2_passed
    if level3_passed:
        valid = True

    needs_review = False
    if not level2_passed or not level3_passed or level2.get('needs_review') or level3.get('needs_review'):
        needs_review = True

    if valid and not needs_review:
        final_reason = 'Submission passed all automated verification layers'
    elif valid and needs_review:
        final_reason = 'Submission needs manual review due to lower confidence or suspicious signals'
    else:
        final_reason = 'Submission failed verification checks'

    return {
        'level1_passed': level1_passed,
        'level1_confidence': level1['confidence'],
        'level2_passed': level2_passed,
        'level2_confidence': level2['confidence'],
        'level3_passed': level3_passed,
        'level3_confidence': level3['confidence'],
        'valid': valid,
        'needs_review': needs_review,
        'reason': final_reason,
        'fraud_flags': fraud_flags,
        'details': {
            'level1': level1,
            'level2': level2,
            'level3': level3,
        },
        'overall_confidence': overall_confidence,
    }
