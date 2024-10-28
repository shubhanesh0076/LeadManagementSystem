# your_app/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import connection
from leads.models import StudentLeads
from info_bridge.models import DataBridge
from locations.models import Address, Country, State, City
from leads.models import LeadRemark
from notifications.services.notification_service import create_notification

@receiver(post_save, sender=Address)
@receiver(post_save, sender=Country)
@receiver(post_save, sender=State)
@receiver(post_save, sender=City)
@receiver(post_save, sender=StudentLeads)
@receiver(post_save, sender=DataBridge)
def refresh_materialized_view(sender, instance, **kwargs):
    with connection.cursor() as cursor:
        cursor.execute("REFRESH MATERIALIZED VIEW optimized_address_view;")

@receiver(post_delete, sender=Address)
@receiver(post_delete, sender=Country)
@receiver(post_delete, sender=State)
@receiver(post_delete, sender=City)
@receiver(post_delete, sender=StudentLeads)
@receiver(post_delete, sender=DataBridge)
def refresh_materialized_view_on_delete(sender, instance, **kwargs):
    with connection.cursor() as cursor:
        cursor.execute("REFRESH MATERIALIZED VIEW optimized_address_view;")

@receiver(post_save, sender=LeadRemark)
def create_lead_assigned_notification(sender, instance, created, **kwargs):
    if instance.is_follow_up:
        # Create a notification for the assigned user
        create_notification(
            user=instance.user,
            lead=instance,
            notification_type='follow-up-reminder',
            message=f"Lead {instance.id} has been assigned to you."
        )
