from django.db import models
from accounts.models import User

# Create your models here.


class Role(models.Model):
    role_name = models.CharField(max_length=20, unique=True, db_index=True, blank=False)
    slug = models.SlugField(max_length=200, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CustomPermissions(models.Model):
    permission_name = models.CharField(max_length=50)
    method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=200, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "permissions_custompermissions"
        constraints = [
            models.UniqueConstraint(
                fields=["method", "endpoint"], name="unique_permission_method"
            )
        ]
        indexes = (models.Index(fields=("method", "endpoint")),)


class UserRoleMapping(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="related_user"
    )
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="related_user"
    )


class RoleCustomPermissionMapping(models.Model):
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="related_role"
    )
    custom_permission = models.ForeignKey(
        CustomPermissions,
        on_delete=models.CASCADE,
        related_name="related_custom_permission",
    )


class LeadsDistributions(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_lead_permission", null=True, blank=True
    )
    source = models.JSONField(max_length=10, null=True, blank=True)
    sub_source = models.JSONField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=20, null=True, blank=True)
    state = models.JSONField(null=True, blank=True)
    city = models.JSONField(null=True, blank=True)
    school = models.JSONField(null=True, blank=True)
