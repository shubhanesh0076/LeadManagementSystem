
from django.urls import path
from info_bridge.apis.views import DataBridgeAPIView, DataBridgeAppendAPIView

app_name='uploads'

urlpatterns = [
    path('', DataBridgeAPIView.as_view(), name='data-bridge'),
    path('append/', DataBridgeAppendAPIView.as_view(), name='data-bridge-append'),
]