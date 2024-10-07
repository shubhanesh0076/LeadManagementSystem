from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer,
    TokenObtainPairSerializer,
)
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework import serializers
from accounts.models import User
from utilities import utils
from permissions.models import UserRoleMapping
from datetime import datetime
from utilities import utils


class CreateUserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new user instance.

    This serializer handles the user creation process, including password
    confirmation and email validation. It ensures that the user-provided passwords
    match and that the email format is valid. The 'role' field is required to be 
    non-null.

    -----------
    Fields:
        username (str): The username of the user.
        email (str): The email address of the user.
        password (str): The password for the user.
        confirm_password (str): The repeated password for confirmation.
        role (str): The role assigned to the user.

    -------
    Methods:
        validate: Validates that the password and confirm password match.
        validate_email: Ensures the email adheres to the specified format.
        validate_role: Ensures that the role field is not None.
        create: Handles the creation of the user instance after validation.
    """

    confirm_password = serializers.CharField(write_only=True)
    email = serializers.CharField()
    role = serializers.CharField()

    class Meta:
        model = User
        fields = ["username", "role", "email", "password", "confirm_password"]
        extra_fields = {
            "email": {"required": True},
            "password": {"required": True},
            "role": {"required": True},
        }

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        return User.objects.create_user(**validated_data)

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password", None)

        if password != confirm_password:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def validate_email(self, value):
        is_valid = utils.email_validate(email=value)
        if not is_valid:
            raise serializers.ValidationError("Invalid Email...!")
        return value

    def validate_role(self, value):
        if value is None:
            raise serializers.ValidationError("Role field can not be None.")
        return value


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user details.

    This serializer excludes sensitive information such as the password and user
    groups while displaying user data.
    
    ----
    Meta:
        model (User): The User model used for this serializer.
        exclude (list): Excludes sensitive fields like password, groups, and date_joined.
    """

    class Meta:
        model = User
        exclude = ["password", "groups", "date_joined"]


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing user information, including roles and additional metadata.

    This serializer fetches user roles and formats user information for display in
    a user list. It provides custom fields such as the full name, updated timestamp,
    created timestamp, and roles.

    -----------
    Fields:
        username (str): The username of the user.
        name (str): The full name of the user, composed of first and last names.
        email (str): The email address of the user.
        mobile_no (str): The user's primary contact number.
        alt_mobile_no (str): The user's alternate contact number.
        gender (str): The user's gender.
        nationality (str): The user's nationality.
        dob (date): The user's date of birth.
        roles (list): The list of roles assigned to the user.
        current_city (str): The city where the user currently resides.
        slug (str): A unique slug for identifying the user.
        created_on (datetime): Timestamp of when the user was created.
        updated_on (datetime): Timestamp of the last update to the user's data.

    -------
    Methods:
        get_name: Returns the full name of the user, or an empty string if missing.
        get_created_on: Converts the user's creation date into the desired format.
        get_updated_on: Converts the user's last updated date into the desired format.
        get_roles: Fetches and formats the user's roles.
    """
    name = serializers.SerializerMethodField()
    updated_on = serializers.SerializerMethodField()
    created_on = serializers.SerializerMethodField()
    roles= serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name",
            "email",
            "mobile_no",
            "alt_mobile_no",
            "gender",
            "nationality",
            "dob",
            "roles",
            "current_city",
            "slug",
            "created_on",
            "updated_on",
        ]

    def get_name(self, obj=None):
        try:
            if obj is not None:
                full_name = f"{obj.first_name}{obj.last_name}"
                if not full_name:
                    return ""
                return full_name
            else:
                return ""
        except Exception as e:
            return ""

    def get_updated_on(self, obj=None):
        if obj is not None:
            return utils.convert_into_desired_dtime_format(obj.updated_on)
        else:
            return None

    def get_created_on(self, obj=None):
        if obj is not None:
            return utils.convert_into_desired_dtime_format(obj=obj.created_on)
        else:
            return None
    def get_roles(self, obj):
        try:
            if obj:
                roles_qs = obj.roles
                user_roles = [{"role": role.role.role_name, "id": role.role.id} for role in roles_qs]
                return user_roles
            return []
        except Exception as e:
            return []


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining JWT tokens using email and password.

    This serializer extends the TokenObtainPairSerializer to authenticate users using their
    email and password. It validates the email format and ensures the credentials are correct.
    If the credentials are valid, it returns access and refresh tokens.

    -----------
    Attributes:
        email (serializers.CharField): The email field for user authentication.
        password (serializers.CharField): The password field for user authentication.
    """

    email = serializers.CharField()
    password = serializers.CharField()

    def validate_email(self, value):
        """
        Validates the email format and ensures it adheres to the specified criteria.

        ----
        Args:
            value (str): The email address to be validated.

        ------
        Raises:
            serializers.ValidationError: If the email is invalid.

        -------
        Returns:
            str: The validated email in lowercase.
        """

        is_valid = utils.email_validate(email=value.lower())
        if not is_valid:
            raise serializers.ValidationError(detail="Invalid Email...!")
        return value

    def validate(self, attrs):
        """
        Authenticates the user using the provided email and password.

        Converts the email to lowercase and attempts to authenticate the user.
        If the credentials are valid, generates and returns JWT tokens.

        -----
        Args:
            attrs (dict): The dictionary containing email and password.

        -------
        Raises:
            serializers.ValidationError: If the credentials are invalid.

        -------
        Returns:
            dict: A dictionary containing the access and refresh tokens.
        """

        credentials = {
            "email": attrs.get("email"),
            "password": attrs.get("password"),
        }
        user = authenticate(**credentials)

        if user is None:
            raise serializers.ValidationError(
                detail={"message": "Invalid Credentials..."}
            )
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        # Use select_related to optimize the role fetching process
        user_role_mappers_qs = UserRoleMapping.objects.filter(user_id=user.id).select_related('role')
        
        # Fetch the roles as a flat list of role names
        roles = list(user_role_mappers_qs.values_list("role__role_name", flat=True))

        access_token["email"] = user.email
        access_token["roles"] = roles
        return {
            "access_token": str(access_token),
            "refresh_token": str(refresh),
        }


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom serializer for refreshing JWT tokens.

    This serializer extends the TokenRefreshSerializer to include custom claims
    such as email and roles in the refreshed access token.
    """

    def validate(self, attrs):
        """
        Validates the refresh token and adds custom claims to the new access token.

        -----
        Args:
            attrs (dict): The dictionary containing the refresh token.

        -------
        Raises:
            serializers.ValidationError: If the refresh token is invalid.

        -------
        Returns:
            dict: A dictionary containing the new access token and the refresh token.
        """

        try:
            refresh = RefreshToken(attrs["refresh"])
            access_token = refresh.access_token  # generate the refresh access token

            # Add custom claims
            user_id = refresh["user_id"]
            user_role_mappers_qs = UserRoleMapping.objects.filter(user_id=user_id)
            access_token["email"] = User.objects.get(id=user_id).email
            access_token["roles"] = (
                [
                    _role[0]
                    for _role in user_role_mappers_qs.values_list("role__role_name")
                ]
                if user_role_mappers_qs.exists()
                else []
            )
            data = {"access_token": str(access_token)}

            return data
        except (InvalidToken, TokenError):
            raise serializers.ValidationError(
                detail={"message": "Token is invalid or expired."}
            )
