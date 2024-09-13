from django.db import models
from accounts.models import User
from permissions.models import Role
from info_bridge.models import DataBridge

# Create your models here.


class StudentLeads(models.Model):

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("others", "Others"),
    ]

    first_name = models.CharField(max_length=50, blank=False, null=False)
    last_name = models.CharField(max_length=40, null=True, blank=True)
    email = models.EmailField(
        verbose_name="email", max_length=254, unique=True, blank=False
    )
    contact_no = models.CharField(max_length=13, null=True, blank=True)
    alt_contact_no = models.CharField(max_length=13, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=50, choices=GENDER_CHOICES, default="prefered not to answer"
    )
    school = models.CharField(max_length=400, null=True, blank=True)
    is_attempted = models.BooleanField(default=False)
    uploaded = models.ForeignKey(
        DataBridge,
        on_delete=models.CASCADE,
        related_name="student_lead",
        null=True,
        blank=True,
    )
    assign_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assign_lead",
        null=True,
        blank=True,
    )
    assign_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assign_by_lead",
        null=True,
        blank=True,
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )  # Budget information

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class ParentsInfo(models.Model):
    lead = models.OneToOneField(
        StudentLeads, related_name="parentsinfo", on_delete=models.CASCADE
    )
    father_name = models.CharField(max_length=30, null=True, blank=True)
    mother_name = models.CharField(max_length=30, null=True, blank=True)
    father_occupation = models.CharField(max_length=50, null=True, blank=True)
    mother_occupation = models.CharField(max_length=50, null=True, blank=True)
    father_salary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    father_contact_no=models.CharField(max_length=13, null=True, blank=True)
    mother_contact_no=models.CharField(max_length=13, null=True, blank=True)


class LeadInteraction(models.Model):
    lead = models.ForeignKey(
        StudentLeads, related_name="interactions", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True
    )  # Tracks the user's role during the interaction
    interaction_type = models.CharField(
        max_length=255, null=True, blank=True
    )  # e.g., 'call', 'email', 'meeting'
    notes = models.TextField(null=True, blank=True)
    next_followup = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interaction by {self.user} as {self.role} with {self.lead}"

class FollowUp(models.Model):
    lead = models.ForeignKey(StudentLeads, on_delete=models.CASCADE, related_name='follow_ups')
    follow_up_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    follow_up_date = models.DateTimeField()
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Follow-up by {self.follow_up_by} on Lead {self.lead.id}"
