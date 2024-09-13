from rest_framework import serializers
from permissions.models import Role, CustomPermissions, UserRoleMapping
from utilities import utils


class RoleListSerializer(serializers.ModelSerializer):

    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id",
            "role_name",
            "slug",
            "description",
            "created_at"
        ]

    
    def get_created_at(self, obj=None):
        if obj is not None:
            return utils.convert_into_desired_dtime_format(obj=obj.created_at)
        else:
            return None


class CreateRoleSerializer(serializers.ModelSerializer):

    role_name = serializers.CharField(write_only=True)

    class Meta:
        model = Role
        fields = ["role_name"]
        extra_fields = {
            "role_name": {"required": True},
        }

    def create(self, validated_data):
        validated_data["role_name"] = validated_data["role_name"].lower()
        return Role.objects.create(**validated_data)

    def validate_role_name(self, value):
        if not all(char.isalpha() or char.isspace() for char in value):
            raise serializers.ValidationError("role name value is invalid.")
        return value


class UpdateRoleSerializer(serializers.ModelSerializer):

    role_name = serializers.CharField(write_only=True)
    old_role_name = serializers.CharField(write_only=True)

    class Meta:
        model = Role
        fields = ["old_role_name", "role_name", "description"]
        extra_fields = {
            "role_name": {"required": True},
        }

    def update(self, instance, validated_data):
        role_name = validated_data.get("role_name", None)

        if not role_name:
            raise serializers.ValidationError("role name field is required.")

        if instance.role_name.lower() == "admin":
            raise serializers.ValidationError("Admin role can not be change.")

        return super().update(instance, validated_data)

    def validate_role_name(self, value):
        if not all(char.isalpha() or char.isspace() for char in value):
            raise serializers.ValidationError("role name value is invalid.")
        return value


class CustomPermissionSerializer(serializers.ModelSerializer):

    created_at = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomPermissions
        fields =  [
            "id",
            "permission_name",
            "method",
            "endpoint",
            "description",
            "created_at"
        ]

    def get_created_at(self, obj=None):
        if obj is not None:
            return utils.convert_into_desired_dtime_format(obj=obj.created_at)
        else:
            return None



class CreatePermissionSerializer(serializers.ModelSerializer):

    permission_name = serializers.CharField()
    method = serializers.CharField()

    class Meta:
        model = CustomPermissions
        fields = "__all__"

    def validate_permission_name(self, value):
        if not all(char.isalpha() or char.isspace() for char in value):
            raise serializers.ValidationError("permission name value is invalid.")
        return value

    def validate_method(self, value):
        if not all(char.isalpha() or char.isspace() for char in value):
            raise serializers.ValidationError("method name value is invalid.")
        return value