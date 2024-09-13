from rest_framework import serializers
from info_bridge.models import DataBridge


class DataBridgeSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataBridge
        fields = [
            "id",
            "file_name",
            "source",
            "sub_source",
            "year",
            "lead_count",
            "uploaded_by",
            "laod_uploaded_at",
        ]

    
    def create(self, validated_data):
        return DataBridge.objects.create(**validated_data)

    # source = data.get('source', None)
    # sub_source = data.get('sub_source', None)
    # year = data.get('year', None)
