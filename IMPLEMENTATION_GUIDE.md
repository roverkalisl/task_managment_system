# Implementation Guide - AI-Powered Smart Verification System

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install required packages
pip install djangorestframework requests Pillow pytesseract

# Install Tesseract OCR (system-level)
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr
```

### 2. Update Django Settings

```python
# config/settings.py

# Add at the bottom
FACEBOOK_GRAPH_ACCESS_TOKEN = os.getenv('FACEBOOK_GRAPH_ACCESS_TOKEN', None)

# Verification thresholds (optional)
VERIFICATION_FAST_SUBMISSION_SECONDS = 120  # 2 minutes
VERIFICATION_MAX_SUBMISSIONS_PER_DAY = 10
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser & Test

```bash
python manage.py createsuperuser
python manage.py runserver
```

---

## 📝 Database Schema

### TaskSubmission Fields

```sql
-- Verification state
level1_passed BOOLEAN DEFAULT FALSE
level2_passed BOOLEAN DEFAULT FALSE
level3_passed BOOLEAN DEFAULT FALSE

-- Confidence scores (0.0 - 1.0)
level1_confidence FLOAT DEFAULT 0.0
level2_confidence FLOAT DEFAULT 0.0
level3_confidence FLOAT DEFAULT 0.0

-- Fraud tracking
is_suspicious BOOLEAN DEFAULT FALSE
fraud_flags JSON DEFAULT []

-- Verification history
verification_attempts INTEGER DEFAULT 0
last_verification_attempt DATETIME NULL
```

### UserTrustScore Fields

```sql
user_id BIGINT UNIQUE (Foreign Key to User)
trust_score FLOAT DEFAULT 0.5

-- Metrics
total_submissions INTEGER DEFAULT 0
approved_submissions INTEGER DEFAULT 0
rejected_submissions INTEGER DEFAULT 0

-- Fraud indicators
duplicate_links_count INTEGER DEFAULT 0
suspicious_patterns_count INTEGER DEFAULT 0
fast_submissions_count INTEGER DEFAULT 0

-- Activity
last_submission_at DATETIME NULL
submission_frequency FLOAT DEFAULT 0.0

updated_at DATETIME AUTO_UPDATE
```

---

## 🔄 Verification Flow Diagrams

### Submission Pipeline

```
User Submits Task
    ↓
Create TaskSubmission (status='level1_pending')
    ↓
Async Thread Started
    ↓
┌─────────────────────────────────┐
│     LEVEL 1: Basic Validation   │
│ - URL format check              │
│ - Facebook domain check         │
│ - HTTP 200 status              │
│ - Valid path check             │
└─────────────────────────────────┘
    ↓ (PASS)
┌─────────────────────────────────┐
│ LEVEL 2: Smart Link Analysis    │
│ - Duplicate detection          │
│ - Speed pattern analysis       │
│ - Graph API validation         │
│ - Privacy checks               │
└─────────────────────────────────┘
    ↓ (PASS or FLAGGED)
┌─────────────────────────────────┐
│ LEVEL 3: Screenshot Verification│
│ - OCR text extraction          │
│ - Facebook UI detection        │
│ - URL matching                 │
│ - Confidence scoring           │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│   FINAL DECISION                │
│ - Update status                │
│ - Update trust score           │
│ - Credit wallet (if approved)  │
└─────────────────────────────────┘
```

### Decision Tree

```
Level 1 Valid?
├─ NO → AUTO REJECT
│
└─ YES → Run Level 2
        └─ Duplicate/Suspicious?
           ├─ YES → Flag for review
           │       └─ Continue to Level 3
           │
           └─ NO → Continue to Level 3
                   └─ Screenshot Confidence?
                      ├─ ≥ 0.75 → AUTO APPROVE
                      ├─ 0.5-0.75 → MANUAL REVIEW
                      └─ < 0.5 → AUTO REJECT
```

---

## 🔑 API Endpoints

### For Frontend Integration

```python
# task/views.py - Submit Task
POST /submit/<task_id>/
  Input: link, screenshot
  Output: Redirect to dashboard (status pending)

# task/views.py - Get Dashboard
GET /
  Output: {
    'total_tasks': int,
    'completed': int,
    'pending_count': int,
    'balance': float,
    'trust_score': float
  }
```

### Admin API

```python
# Django Admin Interface
GET /admin/task/tasksubmission/
  - View all submissions with status
  - Filter by verification level
  - See fraud flags
  - View screenshots
  - See OCR results

POST /admin/task/tasksubmission/<id>/approve/
  - Manually approve submission
  - Add notes

POST /admin/task/tasksubmission/<id>/reject/
  - Manually reject submission
  - Add rejection reason
```

---

## 🧪 Testing

### Unit Tests for Verification

```python
# tests/test_verification.py

from verification.utils import (
    level1_validation,
    smart_link_analysis,
    analyze_screenshot,
)

def test_level1_valid_facebook_link():
    result = level1_validation('https://facebook.com/username/posts/123')
    assert result['valid'] == True
    assert result['confidence'] == 0.85

def test_level1_invalid_url():
    result = level1_validation('not-a-url')
    assert result['valid'] == False

def test_level1_non_facebook():
    result = level1_validation('https://twitter.com/username')
    assert result['valid'] == False

def test_level2_duplicate_detection():
    # Create first submission
    submission1 = TaskSubmission.objects.create(
        user=user,
        task=task,
        submitted_link='https://facebook.com/posts/123'
    )
    
    # Try to submit same link
    result = smart_link_analysis(
        'https://facebook.com/posts/123',
        user
    )
    assert 'duplicate_link' in result['flags']
    assert result['needs_review'] == True

def test_level3_screenshot_analysis():
    # Create screenshot with Facebook content
    screenshot = SimpleUploadedFile(
        name='test.png',
        content=b'fake image data'
    )
    
    result = analyze_screenshot(screenshot, 'https://facebook.com/posts/123')
    assert result['confidence'] >= 0.0
    assert result['confidence'] <= 1.0
```

### Manual Testing Checklist

- [ ] Submit valid Facebook link → Auto-approve
- [ ] Submit duplicate link → Manual review flag
- [ ] Submit 3 links within 2 minutes → Fast submission flag
- [ ] Submit private Facebook post → Manual review
- [ ] Submit invalid screenshot → Auto-reject
- [ ] Submit with no screenshot → Handle gracefully
- [ ] User registration auto-creates UserTrustScore
- [ ] Trust score updates after submission
- [ ] Admin can see all verification details

---

## 🔐 Facebook Graph API Setup (Optional)

### Get Access Token

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create an app
3. Get Page Access Token (long-lived)
4. Set environment variable:

```bash
export FACEBOOK_GRAPH_ACCESS_TOKEN=your_token_here
```

### Verify Post via API

```python
import requests
import os

token = os.getenv('FACEBOOK_GRAPH_ACCESS_TOKEN')
post_id = '123456789_987654321'

response = requests.get(
    f'https://graph.facebook.com/v17.0/{post_id}',
    params={
        'access_token': token,
        'fields': 'id,privacy,from,created_time,story',
    }
)

data = response.json()
print(data)
# {
#   'id': '123456789_987654321',
#   'privacy': 'EVERYONE',
#   'from': {'name': 'User Name', 'id': '123'},
#   'created_time': '2024-01-01T00:00:00+0000'
# }
```

---

## 📊 Admin Dashboard Customization

### Add Fraud Dashboard

```python
# task/admin.py

from django.urls import path
from django.views.generic import TemplateView

class TaskSubmissionAdmin(admin.ModelAdmin):
    # ... existing config ...
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fraud-report/', self.admin_site.admin_view(self.fraud_report_view)),
        ]
        return custom_urls + urls
    
    def fraud_report_view(self, request):
        # Get fraud statistics
        suspicious_count = TaskSubmission.objects.filter(
            is_suspicious=True
        ).count()
        
        # Get users with low trust scores
        low_trust_users = UserTrustScore.objects.filter(
            trust_score__lt=0.3
        )
        
        context = {
            'suspicious_count': suspicious_count,
            'low_trust_users': low_trust_users,
        }
        return render(request, 'admin/fraud_report.html', context)
```

---

## 🐛 Troubleshooting

### OCR Not Working

```python
# Solution: Install tesseract system package
# Windows: Download installer
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr

# Then in Django settings
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = '/usr/bin/tesseract'  # Adjust path
```

### Facebook API Returning Errors

```python
# Check token validity
# Token expired? Get new long-lived token
# Rate limited? Add exponential backoff

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_graph_api(url, token):
    response = requests.get(url, params={'access_token': token})
    response.raise_for_status()
    return response.json()
```

### Migrations Issues

```bash
# If migration conflicts occur
python manage.py showmigrations
python manage.py migrate --fake task 0003  # Skip migration
python manage.py makemigrations

# Or reset (dev only)
rm db.sqlite3
python manage.py migrate
```

---

## 📈 Performance Optimization

### Async Task Processing

```python
# Use Celery for better async handling
# pip install celery redis

from celery import shared_task

@shared_task
def verify_submission_async(submission_id):
    from verification.tasks import verify_submission
    verify_submission(submission_id)

# In views.py
submission = TaskSubmission.objects.create(...)
verify_submission_async.delay(submission.id)
```

### Caching Trust Scores

```python
from django.core.cache import cache

def get_user_trust_score(user):
    cache_key = f'trust_score_{user.id}'
    score = cache.get(cache_key)
    
    if score is None:
        try:
            score = user.usertrustscore.trust_score
            cache.set(cache_key, score, 3600)  # 1 hour
        except:
            score = 0.5
    
    return score
```

---

## 📱 Frontend Template Updates

### Dashboard Template

```html
<!-- templates/dashboard.html -->
<div class="stats">
    <div class="stat-card">
        <h3>Trust Score</h3>
        <p class="score">{{ trust_score|floatformat:2 }}</p>
        {% if trust_score >= 0.8 %}
            <span class="badge green">High Trust</span>
        {% elif trust_score >= 0.5 %}
            <span class="badge yellow">Medium Trust</span>
        {% else %}
            <span class="badge red">Low Trust</span>
        {% endif %}
    </div>
    
    <div class="stat-card">
        <h3>Pending Reviews</h3>
        <p class="count">{{ pending_count }}</p>
    </div>
</div>

<div class="submissions">
    <h3>Recent Submissions</h3>
    <table>
        <tr>
            <th>Task</th>
            <th>Status</th>
            <th>Submitted</th>
            <th>Action</th>
        </tr>
        {% for submission in user_submissions %}
        <tr>
            <td>{{ submission.task.title }}</td>
            <td>
                {% if submission.status == 'approved' %}
                    <span class="badge green">✓ Approved</span>
                {% elif submission.status == 'manual_review' %}
                    <span class="badge yellow">⏳ Reviewing</span>
                {% elif submission.status == 'rejected' %}
                    <span class="badge red">✗ Rejected</span>
                {% else %}
                    <span class="badge gray">⌛ Pending</span>
                {% endif %}
            </td>
            <td>{{ submission.submitted_at|date:'M d, H:i' }}</td>
            <td>
                {% if submission.status == 'rejected' %}
                    <small>{{ submission.feedback }}</small>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
</div>
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Use environment variables for secrets
- [ ] Configure database (PostgreSQL recommended)
- [ ] Set up proper logging
- [ ] Enable HTTPS
- [ ] Configure CORS if needed
- [ ] Set up background worker (Celery)
- [ ] Monitor verification queue
- [ ] Regular backups of submission data
- [ ] Log all verification decisions for audit

---

## 📞 Support

For issues or questions:

1. Check [VERIFICATION_SYSTEM_ARCHITECTURE.md](VERIFICATION_SYSTEM_ARCHITECTURE.md)
2. Review code comments in `verification/utils.py`
3. Check Django admin for submission details
4. Enable debug logging: `settings.LOGGING`

---

**Last Updated:** 2024
**Version:** 1.0 - Initial Implementation
