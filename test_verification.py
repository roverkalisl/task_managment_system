#!/usr/bin/env python
"""
Facebook Group Share Verification Test Script
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from verification.utils import verify_facebook_group_share, detect_fake_link, check_duplicate_submission
from django.contrib.auth.models import User

def test_fake_link_detection():
    """Test fake link detection"""
    print("Testing fake link detection...")

    # Test cases
    test_urls = [
        'https://facebook.com/groups/test/posts/123456789',
        'https://bit.ly/fakefb',
        'https://facebook.com/l.php?u=https://example.com',
        'https://facebook.com/groups/test/permalink/123456789',
    ]

    for url in test_urls:
        result = detect_fake_link(url)
        print(f"URL: {url}")
        print(f"  Fake: {result['is_fake']}, Reason: {result['reason']}")
        print()

def test_duplicate_check():
    """Test duplicate submission detection"""
    print("Testing duplicate submission detection...")

    # Create a test user if not exists
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )

    test_urls = [
        'https://facebook.com/groups/test/posts/123456789',
        'https://facebook.com/groups/test/posts/123456789',  # Duplicate
    ]

    for url in test_urls:
        result = check_duplicate_submission(url, user)
        print(f"URL: {url}")
        print(f"  Duplicate: {result['is_duplicate']}, Reason: {result['reason']}")
        print()

def test_facebook_verification():
    """Test Facebook group share verification (requires internet)"""
    print("Testing Facebook group share verification...")
    print("Note: This test requires internet connection and may take time")

    # Example Facebook group post URL (replace with real one for testing)
    test_url = 'https://facebook.com/groups/test/posts/123456789'
    target_link = 'https://example.com/task-content'

    try:
        result = verify_facebook_group_share(test_url, target_link)
        print(f"Verification Result: {result['valid']}")
        print(f"Reason: {result['reason']}")
        if result['group_info']:
            print(f"Group Info: {result['group_info']}")
    except Exception as e:
        print(f"Error during verification: {e}")

if __name__ == '__main__':
    print("Facebook Verification System Test")
    print("=" * 40)

    test_fake_link_detection()
    test_duplicate_check()

    # Only run Facebook verification if explicitly requested
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        test_facebook_verification()
    else:
        print("Skipping full Facebook verification test.")
        print("Run with --full flag to test actual Facebook scraping.")