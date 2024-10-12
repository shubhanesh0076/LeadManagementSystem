# import re
from rest_framework.permissions import BasePermission

class IsLeadOwnerOrAdmin(BasePermission):
    """
    Custom permission to allow only the lead owner or an admin to view the lead.
    """

    def has_object_permission(self, request, view, obj):

        lead_remark = obj.lead_remark.all().first()

        if request.user.is_superuser:
            return True  # Superusers always have access

        elif not obj.is_attempted:
            return False  # Deny if the lead has not been attempted

        elif obj.is_attempted:
            if lead_remark.lead_status == "REFFERED":
                assigned_lead = obj.student_lead.all().first()

                # Check if there is an assigned lead and if the current user is the one assigned
                if assigned_lead and assigned_lead.assign_to.id == request.user.id:
                    return True
                return False
            return True

        else:
            return False  # Default to deny access


class LeadTypePermissions(BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        elif request.user.id == int(request.GET.get("user_id")):
            return True
        return False

    