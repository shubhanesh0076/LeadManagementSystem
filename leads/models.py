from django.db import models
from accounts.models import User
from permissions.models import Role
from info_bridge.models import DataBridge

# Create your models here.


class StudentLeads(models.Model):

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Others", "Others"),
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
    is_assigned = models.BooleanField(default=False)
    uploaded = models.ForeignKey(
        DataBridge,
        on_delete=models.CASCADE,
        related_name="student_lead",
        null=True,
        blank=True,
    )

    amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )  # Budget information

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Meta:
        indexes = [
            models.Index(fields=["school"]),
            models.Index(fields=["is_attempted"]),
        ]


class ParentsInfo(models.Model):
    lead = models.OneToOneField(
        StudentLeads, related_name="parents_info", on_delete=models.CASCADE
    )
    father_name = models.CharField(max_length=30, null=True, blank=True)
    mother_name = models.CharField(max_length=30, null=True, blank=True)
    father_occupation = models.CharField(max_length=50, null=True, blank=True)
    mother_occupation = models.CharField(max_length=50, null=True, blank=True)
    father_salary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    father_contact_no = models.CharField(max_length=13, null=True, blank=True)
    mother_contact_no = models.CharField(max_length=13, null=True, blank=True)


class Education(models.Model):
    lead = models.OneToOneField(
        StudentLeads, related_name="education_info", on_delete=models.CASCADE
    )
    tenth_score = models.CharField(max_length=10, null=True, blank=True)
    twelfth_scrore = models.CharField(max_length=10, null=True, blank=True)
    school = models.CharField(max_length=200, null=True, blank=True)
    highest_education = models.CharField(max_length=100, null=True, blank=True)
    education_board = models.CharField(max_length=50, null=True, blank=True)
    graduation_percentage = models.CharField(max_length=10, null=True, blank=True)
    preferred_college = models.CharField(max_length=50, null=True, blank=True)
    preferred_location = models.CharField(max_length=30, null=True, blank=True)
    preferred_course = models.CharField(max_length=20, null=True, blank=True)


class GeneralDetails(models.Model):
    lead = models.OneToOneField(
        StudentLeads, related_name="general_info", on_delete=models.CASCADE
    )
    aim = models.CharField(max_length=20, null=True, blank=True)
    budget = models.CharField(max_length=20, null=True, blank=True)
    load_required = models.BooleanField(default=False)
    study_abroad = models.BooleanField(default=False)


class LeadRemark(models.Model):
    CHOOSE_LEAD_STATUS = (
        ("PENDING", "PENDING"),
        ("FOLLOWUP", "FOLLOWUP"),
        ("REFERED", "REFERED"),
        ("CONTACTED", "CONTACTED"),
        ("QUALIFIED", "QUALIFIED"),
        ("UNQUALIFIED", "UNQUALIFIED"),
        ("LOST", "LOST"),
        ("CONVERTED", "CONVERTED"),
        ("COMPLETED", "COMPLETED"),
    )
    
    CHOOSE_CONTACT_REASON = (
        ('Successful Communication', 'Successful Communication'),
        ('Partial Interest', 'Partial Interest'),
        ('Next Steps Defined', 'Next Steps Defined'),
        ('Sale/Deal Closed', 'Sale/Deal Closed'),
        ('Pending Decision', 'Pending Decision'),
        ('No Response', 'No Response'),
        ('Invalid Contact Information', 'Invalid Contact Information'),
        ('Lead Unreachable', 'Lead Unreachable'),
        ('Lead Declined', 'Lead Declined'),
        ('Lead Busy/Unavailable', 'Lead Busy/Unavailable'),
        ('Technical Issues', 'Technical Issues'),
        ('Contact Attempted at Wrong Time', 'Contact Attempted at Wrong Time'),
        ('Other', 'Other')
    )
    
    lead = models.ForeignKey(
        StudentLeads, related_name="lead_remark", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name="user_remark",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    contact_established = models.BooleanField(default=False)
    contact_status = models.CharField(max_length=40, choices=CHOOSE_CONTACT_REASON, null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    lead_status = models.CharField(default="PENDING", choices=CHOOSE_LEAD_STATUS)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_spent_on_lead_in_min = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_follow_up=models.BooleanField(default=False)


class LeadRemarkHistory(models.Model):
    CHOOSE_LEAD_STATUS = (
        ("PENDING", "PENDING"),
        ("FOLLOWUP", "FOLLOWUP"),
        ("REFERED", "REFERED"),
        ("COMPLETED", "COMPLETED"),
    )
    CHOOSE_CONTACT_REASON = (
        ('Successful Communication', 'Successful Communication'),
        ('Partial Interest', 'Partial Interest'),
        ('Next Steps Defined', 'Next Steps Defined'),
        ('Sale/Deal Closed', 'Sale/Deal Closed'),
        ('Pending Decision', 'Pending Decision'),
        ('No Response', 'No Response'),
        ('Invalid Contact Information', 'Invalid Contact Information'),
        ('Lead Unreachable', 'Lead Unreachable'),
        ('Lead Declined', 'Lead Declined'),
        ('Lead Busy/Unavailable', 'Lead Busy/Unavailable'),
        ('Technical Issues', 'Technical Issues'),
        ('Contact Attempted at Wrong Time', 'Contact Attempted at Wrong Time'),
        ('Other', 'Other')
    )

    leadremark = models.ForeignKey(
        LeadRemark, related_name="lead_remark_history", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name="user_remark_history",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    contact_established = models.BooleanField(default=False)
    contact_status = models.CharField(max_length=40, null=True, blank=True, choices=CHOOSE_CONTACT_REASON)
    review = models.TextField(null=True, blank=True)
    lead_status = models.CharField(default="PENDING", choices=CHOOSE_LEAD_STATUS)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_spent_on_lead_in_min = models.IntegerField(default=0)
    is_follow_up=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FollowUp(models.Model):
    lead = models.ForeignKey(
        StudentLeads, on_delete=models.CASCADE, related_name="follow_ups"
    )
    follow_up_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Follow-up by {self.follow_up_by} on Lead {self.lead.id}"


class AssignedTO(models.Model):
    lead = models.ForeignKey(
        StudentLeads, on_delete=models.CASCADE, related_name="student_lead"
    )
    assign_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assign_user",
        null=True,
        blank=True,
    )
    assign_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assign_by_user",
        null=True,
        blank=True,
    )
    assigned_at = models.DateTimeField(auto_now_add=True)


class OptimizedAddressView(models.Model):
    source = models.CharField(max_length=50)
    sub_source = models.CharField(max_length=50)
    country_name = models.CharField(max_length=100)
    state_name = models.CharField(max_length=100)
    city_name = models.CharField(max_length=100)
    school = models.CharField(max_length=400, null=True, blank=True)

    class Meta:
        managed = False  # This is a view, not a table
        db_table = "optimized_address_view"
