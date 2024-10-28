from django.urls import path
from notifications.consumers import NotificationConsumer


websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi(), name="notification_socket"),
]
