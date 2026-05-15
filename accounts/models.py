# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True)
    member_id = models.CharField(max_length=20, unique=True)

    REQUIRED_FIELDS = ['email', 'phone', 'member_id']

    def __str__(self):
        return self.username

class UserTrustScore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    trust_score = models.FloatField(default=0.5)  # 0-1 scale

    # Behavior tracking
    total_submissions = models.IntegerField(default=0)
    approved_submissions = models.IntegerField(default=0)
    rejected_submissions = models.IntegerField(default=0)

    # Fraud indicators
    duplicate_links_count = models.IntegerField(default=0)
    suspicious_patterns_count = models.IntegerField(default=0)
    fast_submissions_count = models.IntegerField(default=0)

    # Recent activity
    last_submission_at = models.DateTimeField(null=True, blank=True)
    submission_frequency = models.FloatField(default=0.0)  # submissions per day

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - Trust: {self.trust_score:.2f}"

    def update_trust_score(self):
        """Calculate and update trust score based on behavior"""
        if self.total_submissions == 0:
            self.trust_score = 0.5
        else:
            approval_rate = self.approved_submissions / self.total_submissions

            # Penalize fraud indicators
            fraud_penalty = (
                self.duplicate_links_count * 0.1 +
                self.suspicious_patterns_count * 0.15 +
                self.fast_submissions_count * 0.05
            )

            # Base score from approval rate
            base_score = approval_rate

            # Adjust for frequency (too frequent might be suspicious)
            if self.submission_frequency > 10:  # More than 10 per day
                frequency_penalty = 0.1
            else:
                frequency_penalty = 0.0

            self.trust_score = max(0.0, min(1.0, base_score - fraud_penalty - frequency_penalty))

        self.save()