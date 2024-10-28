from django.db import models
from accounts.models import User
from leads.models import LeadRemark
# Create your models here.



class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('assigned-lead', 'Assigned Lead'),
        ('follow-up-reminder', 'Follow-Up Reminder'),
        ('others', 'Other'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lead = models.ForeignKey(LeadRemark, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.notification_type} or {self.user.username}"

