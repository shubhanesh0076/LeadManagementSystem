from django.utils import timezone
from utilities import utils
from info_bridge.models import DataBridge
from rest_framework import serializers
from leads.models import (
    Education,
    FollowUp,
    GeneralDetails,
    LeadRemark,
    LeadRemarkHistory,
    ParentsInfo,
    StudentLeads,
)
from locations.models import Address
from django.db import transaction
from utilities.custom_exceptions import UnexpectedError


class DataBridgeSourceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBridge
        fields = ["source"]


class AddressSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = [
            "id",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "country",
            "postal_code",
        ]

    def get_country(self, obj: Address):
        if obj:
            return obj.country.name
        return None

    def get_state(self, obj: Address):
        if obj:
            return obj.state.name
        return None

    def get_city(self, obj: Address):
        if obj:
            return obj.city.name
        return None


class GeneralDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralDetails
        fields = ["id", "aim", "budget", "load_required", "study_abroad"]


class ParentsInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentsInfo
        fields = [
            "id",
            "father_name",
            "mother_name",
            "father_occupation",
            "mother_occupation",
            "father_salary",
            "father_contact_no",
            "mother_contact_no",
        ]


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            "id",
            "tenth_score",
            "twelfth_scrore",
            "school",
            "highest_education",
            "education_board",
            "graduation_percentage",
            "preferred_college",
            "preferred_location",
            "preferred_course",
        ]


class StudentLeadsSerializer(serializers.ModelSerializer):
    address = AddressSerializer()
    general_info = GeneralDetailsSerializer()
    parents_info = ParentsInfoSerializer()
    education_info = EducationSerializer()

    class Meta:
        model = StudentLeads
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "contact_no",
            "alt_contact_no",
            "dob",
            "gender",
            "school",
            "is_attempted",
            "is_assigned",
            "amount",
            "parents_info",
            "general_info",
            "address",
            "education_info",
        ]  # Add any additional fields you need

    def to_representation(self, instance):
        """Customize the representation to provide default options."""
        representation = super().to_representation(instance)

        if not representation.get("address"):
            representation["address"] = {}

        if not representation.get("general_info"):
            representation["general_info"] = {}

        if not representation.get("parents_info"):
            representation["parents_info"] = {}

        if not representation.get("education_info"):
            representation["education_info"] = {}

        return representation

    def update(self, instance, validated_data):
        # Handle related fields
        general_info_data = validated_data.pop("general_info", None)
        parents_info_data = validated_data.pop("parents_info", None)
        education_info_data = validated_data.pop("education_info", None)
        address_info_data = validated_data.pop("address", None)

        if validated_data:
            StudentLeads.objects.filter(id=instance.id).update(**validated_data)
        general_details_updates = []
        parents_info_updates = []
        education_updates = []
        address_updates = []

        # GeneralDetails update or create
        if general_info_data:
            general_details = GeneralDetails.objects.filter(lead=instance).first()
            if general_details:
                for attr, value in general_info_data.items():
                    setattr(general_details, attr, value)
                general_details_updates.append(general_details)
            else:
                GeneralDetails.objects.create(lead=instance, **general_info_data)

        # ParentsInfo update or create
        if parents_info_data:
            parents_info = ParentsInfo.objects.filter(lead=instance).first()
            if parents_info:
                for attr, value in parents_info_data.items():
                    setattr(parents_info, attr, value)
                parents_info_updates.append(parents_info)
            else:
                ParentsInfo.objects.create(lead=instance, **parents_info_data)

        # Education update or create
        if education_info_data:
            education = Education.objects.filter(lead=instance).first()
            if education:
                for attr, value in education_info_data.items():
                    setattr(education, attr, value)
                education_updates.append(education)
            else:
                Education.objects.create(lead=instance, **education_info_data)

        # Address update or create
        if address_info_data:
            address = Address.objects.filter(lead=instance).first()
            if address:
                for attr, value in address_info_data.items():
                    setattr(address, attr, value)
                address_updates.append(address)
            else:
                Address.objects.create(lead=instance, **address_info_data)

        # Perform bulk updates for each model
        if general_details_updates:
            GeneralDetails.objects.bulk_update(
                general_details_updates, list(general_info_data.keys())
            )

        if parents_info_updates:
            ParentsInfo.objects.bulk_update(
                parents_info_updates, list(parents_info_data.keys())
            )

        if education_updates:
            Education.objects.bulk_update(
                education_updates, list(education_info_data.keys())
            )

        if address_updates:
            Address.objects.bulk_update(address_updates, list(address_info_data.keys()))

        return instance


class LeadRemarkSerializer(serializers.ModelSerializer):
    follow_up_date = serializers.DateField()
    follow_up_time = serializers.TimeField()

    class Meta:
        model = LeadRemark
        fields = [
            "lead",
            "user",
            "contact_established",
            "contact_status",
            "review",
            "lead_status",
            "start_time",
            "end_time",
            "time_spent_on_lead_in_min",
            "created_at",
            "updated_at",
            "is_follow_up",
            "follow_up_date",
            "follow_up_time",
        ]

    def update(self, instance, validated_data):
        if not validated_data.get("lead_status", None):
            raise serializers.ValidationError("lead status can not be None.")

        if validated_data.get("contact_established", None) is None:
            raise serializers.ValidationError(
                "contact established field can not be None."
            )

        if validated_data.get("contact_status", None) is None:
            raise serializers.ValidationError("contact status field can not be None.")

        validated_data["start_time"] = instance.start_time
        validated_data["end_time"] = timezone.now()
        validated_data["time_spent_on_lead_in_min"] = utils.datetime_difference(
            validated_data["start_time"], validated_data["end_time"]
        )

        try:
            # LEAD REMARK UPDATE.
            instance.contact_established = validated_data["contact_established"]
            instance.contact_status = validated_data["contact_status"]
            instance.review = validated_data["review"]
            instance.lead_status = validated_data["lead_status"]
            instance.start_time = validated_data["start_time"]
            instance.end_time = validated_data["end_time"]
            instance.time_spent_on_lead_in_min = validated_data[
                "time_spent_on_lead_in_min"
            ]
            instance.is_follow_up = validated_data["is_follow_up"]
            instance.save()
            validated_data["leadremark_id"] = instance.id
            validated_data["user_id"] = instance.user_id

            # LEAD FOLLOWUP CREATED.
            validated_data["user_id"] = instance.user_id
            if instance.is_follow_up:
                follow_up_date = validated_data.get("follow_up_date", None)
                follow_up_time = validated_data.get("follow_up_time", None)

                FollowUp.objects.update_or_create(
                    lead_id=instance.lead_id,
                    defaults={
                        "follow_up_by_id": validated_data["user_id"],
                        "follow_up_date": follow_up_date,
                        "follow_up_time": follow_up_time,
                        "notes": validated_data["review"],
                    },
                )

            # LEAD REMARK HISTORY CREATE.
            validated_data.pop("follow_up_date")
            validated_data.pop("follow_up_time")
            LeadRemarkHistory.objects.create(**validated_data)

        except Exception as e:
            raise UnexpectedError(message="An unexpected error occurse.")
        return instance


class LeadRemarkHistorySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = LeadRemarkHistory
        fields = [
            "user",
            "contact_established",
            "contact_status",
            "review",
            "lead_status",
            "start_time",
            "end_time",
            "time_spent_on_lead_in_min",
            "is_follow_up",
            "updated_at",
            "created_at"
        ]

    def get_user(self, obj):
        try:
            if obj is not None:
                return obj.user.email
            return None
        except:
            return None

    def get_start_time(self, obj):
        try:
            if obj is not None:
                return utils.convert_into_desired_dtime_format(obj.start_time)
            return None
        except:
            return None

    def get_end_time(self, obj):
        try:
            if obj is not None:
                return utils.convert_into_desired_dtime_format(obj.end_time)
            return None
        except:
            return None

    def get_updated_at(self, obj):
        try:
            if obj is not None:
                return utils.convert_into_desired_dtime_format(obj.updated_at)
            return None
        except:
            return None
    
    def get_created_at(self, obj):
        try:
            if obj is not None:
                return utils.convert_into_desired_dtime_format(obj.created_at)
            return None
        except:
            return None


class FollowUpSerializer(serializers.ModelSerializer):

    class Meta:
        model = FollowUp
        fields = "__all__"

    # def create(self, validated_data):
    #     return FollowUp.objects.create()

    # def update(self, instance, validated_data):
    #     pass
