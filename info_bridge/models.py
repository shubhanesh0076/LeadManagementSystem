import datetime
from django.db import models
from accounts.models import User
# Create your models here.



class DataBridge(models.Model):
    current_year = datetime.datetime.now().year 
    YEAR_CHOICE=(
        (year, year) for year in range(2005, current_year)
    )
    file_name=models.CharField(max_length=50, blank=True, null=True, unique=True)
    source=models.CharField(max_length=50, blank=False, null=False)
    sub_source=models.CharField(max_length=50, blank=False, null=False)
    year=models.IntegerField(choices=YEAR_CHOICE, default=current_year)
    lead_count=models.BigIntegerField(default=0)
    uploaded_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='upload_lead', default=None)
    lead_uploaded_at=models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['source']),
            models.Index(fields=['sub_source']),
        ]