from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from notifications.models import Notification
from notifications.apis.serializers import NotificationSerializer


def create_notification(lead, notification_type, message, user=None):
    notification = Notification.objects.create(
        user=user, lead=lead, notification_type=notification_type, message=message
    )  # Create a new notification
    send_notification_via_websocket(user.id, notification) # Send the notification via WebSocket
    return notification


def send_notification_via_websocket(user_id, notification: Notification):
    channel_layer = get_channel_layer()
    notification_serializered_data = NotificationSerializer(notification).data

    message = {
        "type": "send_notification",
        "message": notification_serializered_data
    }
    async_to_sync(channel_layer.group_send)(f"notification_group", message)


def reset_notification_counter(user_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"notification_group", {"type": "reset_counter", "message": {"count": 0}}
    )
