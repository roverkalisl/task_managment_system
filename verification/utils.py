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

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

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


def verify_facebook_group_share(submitted_url, target_link, access_token=None):
    """
    Verify Facebook group share using Playwright for scraping.
    """
    if sync_playwright is None:
        return {
            'valid': False,
            'reason': 'Playwright not available; install playwright package',
            'needs_review': True,
            'group_info': None,
        }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = context.new_page()

            # Navigate to the submitted URL
            page.goto(submitted_url, timeout=30000)

            # Wait for content to load
            page.wait_for_load_state('networkidle', timeout=10000)

            # Check if it's a Facebook page
            if 'facebook.com' not in page.url:
                return {
                    'valid': False,
                    'reason': 'Not a Facebook URL',
                    'needs_review': False,
                    'group_info': None,
                }

            # Check if it's a group post
            url_parts = urlparse(page.url)
            if '/groups/' not in url_parts.path:
                return {
                    'valid': False,
                    'reason': 'Not posted to a Facebook group',
                    'needs_review': False,
                    'group_info': None,
                }

            # Extract group information
            group_info = extract_group_info(page)

            # Check if post exists (not deleted/hidden)
            post_content = page.locator('[data-ad-preview="message"]').first
            if not post_content.is_visible():
                post_content = page.locator('[data-pagelet="FeedUnit_0"]').first

            if not post_content.is_visible():
                return {
                    'valid': False,
                    'reason': 'Post not found or deleted',
                    'needs_review': False,
                    'group_info': group_info,
                }

            # Get post text content
            post_text = post_content.text_content().lower()

            # Check if target link is included in the shared post
            target_domain = urlparse(target_link).netloc.lower()
            target_path = urlparse(target_link).path.lower()

            link_found = False
            if target_link.lower() in post_text:
                link_found = True
            elif target_domain in post_text and target_path in post_text:
                link_found = True
            else:
                # Check for links in the post
                links = post_content.locator('a').all()
                for link in links:
                    href = link.get_attribute('href') or ''
                    if target_link in href or (target_domain in href and target_path in href):
                        link_found = True
                        break

            if not link_found:
                return {
                    'valid': False,
                    'reason': 'Original post/link not found in the shared content',
                    'needs_review': False,
                    'group_info': group_info,
                }

            browser.close()

            return {
                'valid': True,
                'reason': 'Facebook group share verified successfully',
                'needs_review': False,
                'group_info': group_info,
            }

    except Exception as e:
        return {
            'valid': False,
            'reason': f'Verification failed: {str(e)}',
            'needs_review': True,
            'group_info': None,
        }


def extract_group_info(page):
    """
    Extract group information from the Facebook page.
    """
    try:
        # Group name
        group_name_selectors = [
            '[data-pagelet="GroupHeader"] h1',
            'h1[data-hovercard-user-id]',
            '[role="main"] h1',
            'h1'
        ]

        group_name = None
        for selector in group_name_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    group_name = element.text_content().strip()
                    break
            except:
                continue

        # Group link
        group_link = page.url.split('/posts/')[0].split('/permalink')[0]

        # Visibility (hard to determine without API, but we can check for lock icon or text)
        visibility = 'Unknown'
        if page.locator('[aria-label*="Private"]').is_visible() or 'private' in page.content().lower():
            visibility = 'Private'
        elif page.locator('[aria-label*="Public"]').is_visible() or 'public' in page.content().lower():
            visibility = 'Public'

        return {
            'name': group_name,
            'link': group_link,
            'visibility': visibility,
            'share_post_url': page.url,
        }
    except Exception:
        return {
            'name': None,
            'link': None,
            'visibility': 'Unknown',
            'share_post_url': page.url,
        }


def check_duplicate_submission(submitted_url, user):
    """
    Check if the same URL was submitted by the same user or recently by others.
    """
    from task.models import TaskSubmission

    # Check user's own submissions
    user_submissions = TaskSubmission.objects.filter(
        user=user,
        submitted_link=submitted_url
    ).exclude(status='rejected')

    if user_submissions.exists():
        return {
            'is_duplicate': True,
            'reason': 'Same URL submitted by user before',
        }

    # Check recent submissions by other users (last 24 hours)
    recent_submissions = TaskSubmission.objects.filter(
        submitted_link=submitted_url,
        submitted_at__gte=timezone.now() - timedelta(hours=24)
    ).exclude(user=user)

    if recent_submissions.exists():
        return {
            'is_duplicate': True,
            'reason': 'URL recently submitted by another user',
        }

    return {
        'is_duplicate': False,
        'reason': None,
    }


def detect_fake_link(url):
    """
    Basic fake link detection.
    """
    # Check for suspicious patterns
    suspicious_patterns = [
        'bit.ly', 'tinyurl.com', 'goo.gl',  # URL shorteners
        'facebook.com/l.php',  # Facebook redirect
        'fake', 'test', 'dummy'  # Common fake words
    ]

    url_lower = url.lower()
    for pattern in suspicious_patterns:
        if pattern in url_lower:
            return {
                'is_fake': True,
                'reason': f'Suspicious pattern detected: {pattern}',
            }

    if not is_facebook_link(url):
        return {
            'is_fake': True,
            'reason': 'Not a Facebook URL',
        }

    return {
        'is_fake': False,
        'reason': None,
    }


def run_facebook_group_verification(submission):
    """
    Main verification function for Facebook group shares.
    """
    submitted_url = submission.submitted_link
    target_link = submission.task.target_link
    user = submission.user

    # Level 1: Basic validation
    if not is_valid_url(submitted_url):
        return {
            'level1_passed': False,
            'level1_confidence': 0.0,
            'level2_passed': False,
            'level2_confidence': 0.0,
            'level3_passed': False,
            'level3_confidence': 0.0,
            'valid': False,
            'needs_review': False,
            'reason': 'Invalid URL format',
            'fraud_flags': ['invalid_url'],
            'group_info': None,
        }

    if not is_facebook_link(submitted_url):
        return {
            'level1_passed': False,
            'level1_confidence': 0.0,
            'level2_passed': False,
            'level2_confidence': 0.0,
            'level3_passed': False,
            'level3_confidence': 0.0,
            'valid': False,
            'needs_review': False,
            'reason': 'Not a Facebook URL',
            'fraud_flags': ['not_facebook'],
            'group_info': None,
        }

    # Check for fake links
    fake_check = detect_fake_link(submitted_url)
    if fake_check['is_fake']:
        return {
            'level1_passed': False,
            'level1_confidence': 0.0,
            'level2_passed': False,
            'level2_confidence': 0.0,
            'level3_passed': False,
            'level3_confidence': 0.0,
            'valid': False,
            'needs_review': False,
            'reason': fake_check['reason'],
            'fraud_flags': ['fake_link'],
            'group_info': None,
        }

    # Check for duplicates
    duplicate_check = check_duplicate_submission(submitted_url, user)
    if duplicate_check['is_duplicate']:
        return {
            'level1_passed': False,
            'level1_confidence': 0.0,
            'level2_passed': False,
            'level2_confidence': 0.0,
            'level3_passed': False,
            'level3_confidence': 0.0,
            'valid': False,
            'needs_review': False,
            'reason': duplicate_check['reason'],
            'fraud_flags': ['duplicate_link'],
            'group_info': None,
        }

    # Level 1 passed
    level1_result = {
        'valid': True,
        'confidence': 0.8,
        'reason': 'Basic validation passed',
    }

    # Level 2: Facebook group share verification
    access_token = os.getenv('FACEBOOK_GRAPH_ACCESS_TOKEN') or getattr(settings, 'FACEBOOK_GRAPH_ACCESS_TOKEN', None)
    group_verification = verify_facebook_group_share(submitted_url, target_link, access_token)

    level2_result = {
        'valid': group_verification['valid'],
        'confidence': 0.9 if group_verification['valid'] else 0.0,
        'reason': group_verification['reason'],
        'group_info': group_verification['group_info'],
    }

    # Level 3: Screenshot verification (if provided)
    level3_result = analyze_screenshot(submission.screenshot, submitted_url)

    # Overall assessment
    fraud_flags = []
    if duplicate_check['is_duplicate']:
        fraud_flags.append('duplicate_link')
    if fake_check['is_fake']:
        fraud_flags.append('fake_link')

    valid = level1_result['valid'] and level2_result['valid']
    needs_review = group_verification['needs_review'] or level3_result['needs_review']

    if valid and not needs_review:
        final_reason = 'Facebook group share verified successfully'
    elif valid and needs_review:
        final_reason = 'Verification passed but needs manual review'
    else:
        final_reason = group_verification['reason']

    return {
        'level1_passed': level1_result['valid'],
        'level1_confidence': level1_result['confidence'],
        'level2_passed': level2_result['valid'],
        'level2_confidence': level2_result['confidence'],
        'level3_passed': level3_result['valid'],
        'level3_confidence': level3_result['confidence'],
        'valid': valid,
        'needs_review': needs_review,
        'reason': final_reason,
        'fraud_flags': fraud_flags,
        'group_info': group_verification['group_info'],
        'details': {
            'level1': level1_result,
            'level2': level2_result,
            'level3': level3_result,
        },
    }
