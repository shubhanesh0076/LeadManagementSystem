from info_bridge.models import DataBridge
from rest_framework import serializers


class DataBridgeSourceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model=DataBridge
        fields=['source']