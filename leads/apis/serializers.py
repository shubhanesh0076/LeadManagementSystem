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
    AssignedTO,
)
from locations.models import Address
from utilities.custom_exceptions import UnexpectedError
from permissions.models import Role, UserRoleMapping
from django.db import transaction


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
            instance.is_remarked = True
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
            if instance.is_follow_up:
                validated_data.pop("follow_up_date")
                validated_data.pop("follow_up_time")
            validated_data["is_remarked"] = True
            LeadRemarkHistory.objects.create(**validated_data)

        except Exception as e:
            print("error ", e)
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
            "created_at",
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


class AssignedTOSerializer(serializers.ModelSerializer):

    class Meta:
        model = AssignedTO
        fields = "__all__"

    def validate(self, validated_data):
        lead = validated_data.get("lead")
        assign_to = validated_data.get("assign_to")

        request = self.context.get("request")
        assign_by = request.user
        assign_by_roles = request.auth.get("roles", [])

        # Self-assignment validation
        if assign_by.email == assign_to.email:
            raise serializers.ValidationError("You cannot assign the lead to yourself.")

        # Fetch roles of the assignee
        assign_to_roles = UserRoleMapping.objects.filter(
            user_id=assign_to.id
        ).values_list("role__role_name", flat=True)

        # Fetch lead remark and validate the lead has been attempted
        leadremark_qs = LeadRemark.objects.filter(lead=lead).select_related("lead")
        if not leadremark_qs.exists():
            raise serializers.ValidationError("Attempt the lead before assigning it.")

        leadremark_obj = leadremark_qs.first()

        # Check if lead is already assigned by the current user
        assigned_lead_obj = AssignedTO.objects.filter(lead=lead, assign_by=assign_by)
        assigned_to_exists = assigned_lead_obj.filter(assign_to=assign_to).exists()

        # Admins and superusers can assign to anyone
        if "admin" in assign_to_roles or request.user.is_superuser:
            return self._handle_assignment(
                lead,
                assign_to,
                assign_by,
                leadremark_obj,
                leadremark_qs,
                assigned_lead_obj,
                assigned_to_exists,
                validated_data,
            )

        # Validation for non-admins (counselors, bdms, etc.)
        if assigned_lead_obj.exists():
            if assigned_lead_obj.first().assign_to.email != assign_by.email:
                raise serializers.ValidationError(
                    "Only the person assigned to this lead can further assign it."
                )
        else:
            if leadremark_obj.user != assign_by:
                raise serializers.ValidationError(
                    "Only the person who attempted the lead can assign it."
                )

        # Role-based assignment validation
        if "counsellor" in assign_by_roles and "bdms" not in assign_to_roles:
            raise serializers.ValidationError(
                "Counselors can only assign leads to BDMS."
            )

        if "bdms" in assign_by_roles and "bdms" not in assign_to_roles:
            raise serializers.ValidationError(
                "BDMS can only assign leads to other BDMS."
            )

        return self._handle_assignment(
            lead,
            assign_to,
            assign_by,
            leadremark_obj,
            leadremark_qs,
            assigned_lead_obj,
            assigned_to_exists,
            validated_data,
        )

    def _handle_assignment(
        self,
        lead,
        assign_to,
        assign_by,
        leadremark_obj,
        leadremark_qs,
        assigned_lead_obj,
        assigned_to_exists,
        validated_data,
    ):
        lead_status = "REFERRED"
        with transaction.atomic():
            if not assigned_to_exists:
                AssignedTO.objects.create(
                    lead=lead, assign_to=assign_to, assign_by=assign_by
                )

                # Update lead assignment status
                StudentLeads.objects.filter(id=lead.id).update(is_assigned=True)
                leadremark_qs.update(lead_status=lead_status)
                # Log the assignment in LeadRemarkHistory
                LeadRemarkHistory.objects.create(
                    leadremark=leadremark_obj, user=assign_by, lead_status=lead_status
                )

            else:
                assigned_lead_obj.update(assign_to=assign_to, assign_by=assign_by)
                leadremark_qs.update(lead_status=lead_status)
                # Log the reassignment in LeadRemarkHistory
                LeadRemarkHistory.objects.create(
                    leadremark=leadremark_obj, user=assign_by, lead_status=lead_status
                )

        return validated_data


class FollowUpSerializer(serializers.ModelSerializer):

    lead = serializers.SerializerMethodField()
    follow_up_by = serializers.SerializerMethodField()
    contact_no = serializers.SerializerMethodField()

    class Meta:

        model = FollowUp
        fields = [
            "lead",
            "follow_up_by",
            "follow_up_date",
            "follow_up_time",
            "notes",
            "contact_no",
        ]

    def get_lead(self, obj):
        if not obj:
            return None
        return f"{obj.lead.first_name} {obj.lead.last_name}"

    def get_follow_up_by(self, obj):
        if not obj:
            return None

        elif obj.follow_up_by.username:
            return obj.follow_up_by.username

        elif obj.follow_up_by.first_name:
            return f"{obj.lead.first_name} {obj.lead.last_name}"
        else:
            return None

    def get_contact_no(self, obj):
        if not obj:
            return None
        return obj.lead.contact_no


class PendingLeadsSerializer(serializers.ModelSerializer):

    contact_no = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    lead = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = LeadRemark
        fields = [
            "id",
            "contact_established",
            "contact_status",
            "review",
            "lead_status",
            "contact_no",
            "time_spent_on_lead_in_min",
            "created_at",
            "updated_at",
            "is_remarked",
            "lead",
            "user",
        ]

    def get_contact_no(self, obj):
        if obj is not None:
            return obj.lead.contact_no
        else:
            return None

    def get_user(self, obj):

        if not obj:
            return None

        elif obj.user.username:
            return obj.user.username

        elif obj.user.first_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        else:
            return None

    def get_lead(self, obj):

        if not obj:
            return None

        elif obj.lead.email:
            return obj.lead.email

        elif obj.lead.first_name:
            return f"{obj.lead.first_name} {obj.lead.last_name}"
        else:
            return None

    def get_created_at(self, obj):

        if obj is not None:
            return utils.convert_into_desired_dtime_format(obj.updated_at)
        else:
            return None

    def get_updated_at(self, obj):

        if obj is not None:
            return utils.convert_into_desired_dtime_format(obj.updated_at)
        else:
            return None


class ReferredLeadsSerializer(serializers.ModelSerializer):

    assign_to = serializers.SerializerMethodField()
    assign_by = serializers.SerializerMethodField()
    lead = serializers.SerializerMethodField()
    assigned_at = serializers.SerializerMethodField()

    class Meta:
        model = AssignedTO
        fields = ["id", "assign_to", "assign_by", "lead", "assigned_at"]

    def get_assign_to(self, obj):

        try:
            if obj is not None:
                return obj.assign_to.email
            else:
                return None
        except Exception as e:
            return None

    def get_assign_by(self, obj):

        try:
            if obj is not None:
                return obj.assign_by.email
            else:
                return None
        except Exception as e:
            return None

    def get_lead(self, obj):

        try:
            if obj is not None:
                return obj.lead.email
            else:
                return None
        except Exception as e:
            return None

    def get_assigned_at(self, obj):

        try:
            if obj is not None:
                return utils.convert_into_desired_dtime_format(obj.assigned_at)
            else:
                return None
        except Exception as e:
            return None
