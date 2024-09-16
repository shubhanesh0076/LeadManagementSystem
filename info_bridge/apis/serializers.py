from rest_framework import serializers
from info_bridge.models import DataBridge
from utilities import utils


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
            "lead_uploaded_at",
        ]

    
    def create(self, validated_data):
        return DataBridge.objects.create(**validated_data)


class DataBridgeListSerializer(serializers.ModelSerializer):

    uploaded_by = serializers.SerializerMethodField()
    lead_uploaded_at=serializers.SerializerMethodField()

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
            "lead_uploaded_at",
        ]

    def get_uploaded_by(self, obj=None):
        try:
            if obj is not None:
                return obj.uploaded_by.email 
            return None
        except:
            return None
        
    def get_lead_uploaded_at(self, obj=None):
        if obj is not None:
            return utils.convert_into_desired_dtime_format(obj=obj.lead_uploaded_at)
        return None