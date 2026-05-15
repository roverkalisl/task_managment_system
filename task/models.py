from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


# 📋 TASK MODEL
class Task(models.Model):
    TASK_TYPES = (
        ('share', 'Share'),
        ('post', 'Post'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='share')

    target_link = models.URLField()
    reward = models.DecimalField(max_digits=8, decimal_places=2)

    total_slots = models.IntegerField(default=100)
    completed_slots = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# 📤 TASK SUBMISSION
class TaskSubmission(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('level1_pending', 'Level 1 Verification'),
        ('level2_pending', 'Level 2 Verification'),
        ('level3_pending', 'Level 3 Verification'),
        ('manual_review', 'Manual Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    submitted_link = models.URLField()
    screenshot = models.ImageField(upload_to='proofs/', null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(null=True, blank=True)

    # Verification levels
    level1_passed = models.BooleanField(default=False)
    level2_passed = models.BooleanField(default=False)
    level3_passed = models.BooleanField(default=False)

    # AI confidence scores
    level1_confidence = models.FloatField(default=0.0)  # 0-1
    level2_confidence = models.FloatField(default=0.0)
    level3_confidence = models.FloatField(default=0.0)

    # Fraud detection
    is_suspicious = models.BooleanField(default=False)
    fraud_flags = models.JSONField(default=list)  # List of fraud indicators

    # Verification metadata
    verification_attempts = models.IntegerField(default=0)
    last_verification_attempt = models.DateTimeField(null=True, blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.task}"

    def get_overall_confidence(self):
        """Calculate overall confidence based on passed levels"""
        if self.level3_passed:
            return (self.level1_confidence + self.level2_confidence + self.level3_confidence) / 3
        elif self.level2_passed:
            return (self.level1_confidence + self.level2_confidence) / 2
        elif self.level1_passed:
            return self.level1_confidence
        return 0.0

    class Meta:
        unique_together = ('user', 'task')