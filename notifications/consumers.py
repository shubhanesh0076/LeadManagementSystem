from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import timedelta
from django.utils import timezone
import json
from notifications.models import Notification
from notifications.apis.serializers import NotificationSerializer
from asgiref.sync import sync_to_async
from info_bridge.models import DataBridge


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        """used for connecting the application."""

        self.room_name = "notification_room"
        self.group_name = "notification_group"

        await self.channel_layer.group_add(
            self.group_name, self.channel_name
        )  # Add the connection to the group
        await self.accept()
        await self.send(
            text_data=json.dumps({"status": "Connection has been established."})
        )
        await self.send_last_week_notifications()

    async def receive(self, text_data):
        # {"notification_id": '74', "is_viewed": true}
        # Handle receiving messages from WebSocket
        
        data = json.loads(text_data)
        if data['action'] == 'update_status':
            await self.update_notification_status(data['notification_id'])

    @sync_to_async
    def update_notification_status(self, notification_id):
        """Updates the notification status to 'viewed'."""
        try:
            Notification.objects.filter(id=notification_id).update(is_viewed=True)
        except Notification.DoesNotExist:
            pass
        
    async def send_last_week_notifications(self):
        # Calculate the time range for the past week
        one_week_ago = timezone.now() - timedelta(days=7)

        # Query and serialize the notifications in an asynchronous way
        last_week_notifications = await sync_to_async(
            lambda: Notification.objects.filter(created_at__gte=one_week_ago).order_by(
                "-created_at"
            )
        )()

        # Serialize the notifications using NotificationSerializer
        last_week_notifications_serialized_data = await sync_to_async(
            lambda: NotificationSerializer(last_week_notifications, many=True).data
        )()

        # Send the notifications to the client
        for notification in last_week_notifications_serialized_data:
            await self.send(text_data=json.dumps({"message": notification}))

    async def send_notification(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps(event["message"]))

    async def reset_counter(self, event):
        # Send counter reset to the WebSocket

        await self.send(text_data=json.dumps({"action": "reset_counter", "count": 0}))

    async def disconnect(self, close_code):
        # Remove the connection from the group
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("CONNECTION HAS BEEN CLOSED...")
